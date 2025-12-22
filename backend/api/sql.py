# backend/api/sql.py
"""SQL 실행 API"""
from fastapi import APIRouter

from backend.schemas.submission import (
    SQLExecuteRequest, SQLExecuteResponse,
    SubmitRequest, SubmitResponse
)
from backend.services.sql_service import execute_sql
from backend.services.grading_service import grade_submission


router = APIRouter(prefix="/sql", tags=["sql"])


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
async def submit_answer(request: SubmitRequest):
    """문제 제출 및 채점"""
    return grade_submission(
        problem_id=request.problem_id,
        sql=request.sql,
        note=request.note
    )
