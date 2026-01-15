# backend/api/practice.py
"""무한 연습 모드 API"""
from datetime import date
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import json
import uuid

from backend.services.database import postgres_connection


router = APIRouter(prefix="/practice", tags=["practice"])


class GeneratePracticeRequest(BaseModel):
    """연습 문제 생성 요청"""
    data_type: str = "pa"  # pa or stream


class PracticeProblem(BaseModel):
    """연습 문제"""
    id: str
    title: str
    description: str
    difficulty: str
    answer_sql: str
    data_type: str


class GeneratePracticeResponse(BaseModel):
    """연습 문제 생성 응답"""
    success: bool
    problem: Optional[PracticeProblem] = None
    message: Optional[str] = None


class SubmitPracticeRequest(BaseModel):
    """연습 문제 제출"""
    problem_id: str
    sql: str
    answer_sql: str
    difficulty: str
    data_type: str = "pa"


@router.post("/generate", response_model=GeneratePracticeResponse)
async def generate_practice_problem(request: GeneratePracticeRequest):
    """연습 문제 1개 생성 (Gemini 호출)"""
    try:
        from problems.prompt_pa import build_pa_prompt
        from problems.prompt import get_data_summary
        from problems.gemini import call_gemini_json
        
        # 현재 프로덕트 타입 가져오기
        try:
            with postgres_connection() as pg:
                df = pg.fetch_df("SELECT product_type FROM public.current_product_type WHERE id = 1")
            product_type = df.iloc[0]["product_type"] if len(df) > 0 else "commerce"
        except:
            product_type = "commerce"
        
        # 데이터 요약 가져오기
        data_summary = get_data_summary()
        
        # Gemini에 문제 1개만 요청
        prompt = build_pa_prompt(data_summary, n=1, product_type=product_type)
        problems = call_gemini_json(prompt)
        
        if not problems or len(problems) == 0:
            return GeneratePracticeResponse(
                success=False,
                message="문제 생성에 실패했습니다."
            )
        
        p = problems[0]
        problem_id = f"practice_{uuid.uuid4().hex[:8]}"
        
        # Gemini 응답 필드: question 또는 description
        description = p.get("question") or p.get("description") or ""
        
        return GeneratePracticeResponse(
            success=True,
            problem=PracticeProblem(
                id=problem_id,
                title=p.get("title", "연습 문제"),
                description=description,
                difficulty=p.get("difficulty", "medium"),
                answer_sql=p.get("answer_sql", ""),
                data_type=request.data_type
            )
        )
    except Exception as e:
        return GeneratePracticeResponse(
            success=False,
            message=f"오류: {str(e)}"
        )


@router.post("/submit")
async def submit_practice(request: SubmitPracticeRequest, req: Request):
    """연습 문제 제출 및 채점 (레벨업에 반영)"""
    try:
        from backend.grader.sql_grader import SQLGrader
        from backend.grader.engine import check_answer
        from backend.services.grading_service import save_submission_pg, award_xp, get_difficulty_xp
        from backend.common.date_utils import get_today_kst
        from backend.api.auth import get_session
        
        # 사용자 ID 추출
        user_id = None
        session_id = req.cookies.get("session_id")
        if session_id:
            session = get_session(session_id)
            if session and session.get("user"):
                user_id = session["user"].get("id")
        
        grader = SQLGrader()
        
        # 정답 SQL 실행
        expected_result = grader.execute_sql(request.answer_sql, data_type=request.data_type)
        if not expected_result["success"]:
            return {
                "success": False,
                "is_correct": False,
                "message": f"정답 SQL 실행 오류: {expected_result.get('error', '알 수 없는 오류')}"
            }
        
        # 사용자 SQL 실행 및 비교
        user_result = grader.execute_sql(request.sql, data_type=request.data_type)
        if not user_result["success"]:
            return {
                "success": True,
                "is_correct": False,
                "message": f"SQL 실행 오류: {user_result.get('error', '알 수 없는 오류')}"
            }
        
        # 결과 비교
        is_correct = grader.compare_results(expected_result["data"], user_result["data"])
        
        # 점수 계산
        xp_value = 0
        if is_correct:
            xp_value = get_difficulty_xp(request.difficulty)
        
        # DB에 저장 (레벨업에 반영)
        try:
            save_submission_pg(
                session_date=get_today_kst().isoformat(),
                problem_id=request.problem_id,
                data_type=f"practice_{request.data_type}",
                sql_text=request.sql,
                is_correct=is_correct,
                feedback="정답!" if is_correct else "오답",
                user_id=user_id,
                difficulty=request.difficulty
            )
            
            # 정답인 경우 XP 지급
            if is_correct and user_id:
                award_xp(user_id, xp_value)
        except Exception:
            pass  # 저장 실패해도 채점 결과는 반환
        
        return {
            "success": True,
            "is_correct": is_correct,
            "score": xp_value if is_correct else 0,
            "message": f"정답입니다! 🎉 (+{xp_value} XP)" if is_correct else "오답입니다. 다시 시도해보세요."
        }
        
    except Exception as e:
        return {
            "success": False,
            "is_correct": False,
            "message": f"채점 오류: {str(e)}"
        }


