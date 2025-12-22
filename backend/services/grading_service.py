# backend/services/grading_service.py
"""채점 서비스"""
import time
from datetime import date, datetime
from typing import Tuple, Optional

from backend.services.database import postgres_connection, duckdb_connection
from backend.schemas.submission import SubmitResponse


def grade_submission(
    problem_id: str,
    sql: str,
    note: Optional[str] = None
) -> SubmitResponse:
    """
    문제 제출 채점
    """
    start = time.time()
    session_date = date.today().isoformat()
    
    try:
        # 1. 사용자 SQL 실행
        with postgres_connection() as pg:
            user_df = pg.fetch_df(sql.strip().rstrip(";"))
        
        # 2. 채점 (현재는 간단한 검증만)
        # TODO: 정답 SQL과 비교
        is_correct = len(user_df) > 0
        
        # 3. AI 피드백 생성
        try:
            from problems.gemini import grade_pa_submission
            feedback = grade_pa_submission(
                problem_id=problem_id,
                sql_text=sql,
                is_correct=is_correct,
                diff=None,
                note=note
            )
        except Exception as e:
            feedback = f"피드백 생성 실패: {str(e)}"
        
        # 4. 제출 기록 저장
        save_submission(
            session_date=session_date,
            problem_id=problem_id,
            sql_text=sql,
            is_correct=is_correct,
            feedback=feedback
        )
        
        elapsed = (time.time() - start) * 1000
        
        return SubmitResponse(
            is_correct=is_correct,
            feedback=feedback,
            execution_time_ms=elapsed,
            diff=None
        )
    
    except Exception as e:
        # 실행 오류
        feedback = f"SQL 실행 오류: {str(e)}"
        
        save_submission(
            session_date=session_date,
            problem_id=problem_id,
            sql_text=sql,
            is_correct=False,
            feedback=feedback
        )
        
        return SubmitResponse(
            is_correct=False,
            feedback=feedback,
            execution_time_ms=0,
            diff=str(e)
        )


def save_submission(
    session_date: str,
    problem_id: str,
    sql_text: str,
    is_correct: bool,
    feedback: str
):
    """제출 기록 저장"""
    try:
        with duckdb_connection() as duck:
            duck.insert("pa_submissions", {
                "session_date": session_date,
                "problem_id": problem_id,
                "sql_text": sql_text,
                "is_correct": is_correct,
                "feedback": feedback,
                "submitted_at": datetime.now()
            })
    except Exception:
        pass  # 저장 실패해도 결과는 반환
