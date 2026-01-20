# backend/api/sql.py
# [STABLE-FLOW] 이 파일은 핵심 제출 API 로직을 포함하며 현재 안정 상태로 고정되었습니다. 수정 시 주의하십시오.
"""SQL 실행 API"""
from fastapi import APIRouter, Request
from pydantic import BaseModel

from backend.schemas.submission import (
    SQLExecuteRequest, SQLExecuteResponse,
    SubmitRequest, SubmitResponse,
    InsightRequest, InsightResponse,
    TranslateRequest, TranslateResponse
)
from backend.services.sql_service import execute_sql
from backend.services.grading_service import grade_submission, get_hint
from backend.services.ai_service import get_ai_insight, translate_text_to_sql
from backend.api.auth import get_session


router = APIRouter(prefix="/sql", tags=["sql"])


class HintRequest(BaseModel):
    problem_id: str
    sql: str
    data_type: str = "pa"


class HintResponse(BaseModel):
    hint: str


@router.post("/execute", response_model=SQLExecuteResponse)
async def execute_query(request: SQLExecuteRequest):
    """SQL 쿼리 실행 (테스트용)"""
    data, columns, error, elapsed = execute_sql(request.sql, request.limit)
    
    if error:
        return SQLExecuteResponse(
            success=False,
            error=error,
            execution_time_ms=elapsed
        )
    
    return SQLExecuteResponse(
        success=True,
        columns=columns,
        data=data,
        row_count=len(data) if data else 0,
        execution_time_ms=elapsed
    )


@router.post("/submit", response_model=SubmitResponse)
async def submit_answer(request: SubmitRequest, req: Request):
    """문제 제출 및 채점"""
    # 세션에서 user_id 추출
    user_id = None
    session_id = req.cookies.get("session_id")
    if session_id:
        session = get_session(session_id)
        if session and session.get("user"):
            user_id = session["user"].get("id")
    
    result = grade_submission(
        problem_id=request.problem_id,
        sql=request.sql,
        data_type=getattr(request, 'data_type', 'pa'),
        note=request.note,
        user_id=user_id
    )
    
    # 문제를 찾을 수 없는 경우 404 에러 반환
    if not result.is_correct and result.feedback == "문제를 찾을 수 없습니다.":
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
        
    return result


@router.post("/hint", response_model=HintResponse)
async def request_hint(request: HintRequest):
    """AI 힌트 요청"""
    hint = get_hint(
        problem_id=request.problem_id,
        sql=request.sql,
        data_type=request.data_type
    )
    return HintResponse(hint=hint)


@router.post("/insight", response_model=InsightResponse)
async def request_insight(request: InsightRequest):
    """AI 인사이트 요청"""
    insight_data = get_ai_insight(
        problem_id=request.problem_id,
        sql=request.sql,
        results=request.results,
        data_type=request.data_type
    )
    return InsightResponse(**insight_data)


@router.post("/translate", response_model=TranslateResponse)
async def request_translate(request: TranslateRequest):
    """자연어-to-SQL 변환 요청"""
    sql = translate_text_to_sql(
        question=request.question,
        data_type=request.data_type
    )
    return TranslateResponse(sql=sql)


class AIHelpRequest(BaseModel):
    problem_id: str
    help_type: str  # "hint" or "solution"
    current_sql: str = ""
    attempt_count: int = 0
    data_type: str = "pa"


class AIHelpResponse(BaseModel):
    type: str
    content: str


@router.post("/ai-help", response_model=AIHelpResponse)
async def request_ai_help(request: AIHelpRequest):
    """
    Daily 문제 AI 도움 요청
    
    - help_type: "hint" (접근 방향 힌트) 또는 "solution" (정답 쿼리)
    - 문제당 1회 제한은 프론트엔드에서 처리
    """
    from backend.services.ai_service import get_ai_help
    
    result = get_ai_help(
        problem_id=request.problem_id,
        help_type=request.help_type,
        current_sql=request.current_sql,
        attempt_count=request.attempt_count,
        data_type=request.data_type
    )
    return AIHelpResponse(**result)
