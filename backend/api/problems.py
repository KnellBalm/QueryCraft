# backend/api/problems.py
"""문제 API"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.schemas.problem import (
    Problem, ProblemListResponse, ProblemDetailResponse, TableSchema
)
from backend.services.problem_service import (
    get_problems, get_problem_by_id, get_table_schema
)


router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("/schema/{data_type}", response_model=list[TableSchema])
async def get_schema(data_type: str):
    """테이블 스키마 조회"""
    prefix = "pa_" if data_type == "pa" else "stream_"
    return get_table_schema(prefix)


@router.get("/{data_type}", response_model=ProblemListResponse)
async def list_problems(
    data_type: str,
    target_date: Optional[str] = Query(None, description="날짜 (YYYY-MM-DD)")
):
    """문제 목록 조회"""
    if data_type not in ("pa", "stream"):
        raise HTTPException(400, "data_type은 'pa' 또는 'stream'이어야 합니다.")
    
    if target_date:
        try:
            dt = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(400, "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
    else:
        dt = date.today()
    
    problems = get_problems(data_type, dt)
    completed = sum(1 for p in problems if p.is_completed)
    
    return ProblemListResponse(
        date=dt.isoformat(),
        data_type=data_type,
        problems=problems,
        total=len(problems),
        completed=completed
    )


@router.get("/{data_type}/{problem_id}", response_model=ProblemDetailResponse)
async def get_problem_detail(
    data_type: str,
    problem_id: str,
    target_date: Optional[str] = Query(None)
):
    """문제 상세 조회"""
    if data_type not in ("pa", "stream"):
        raise HTTPException(400, "data_type은 'pa' 또는 'stream'이어야 합니다.")
    
    dt = date.fromisoformat(target_date) if target_date else date.today()
    
    problem = get_problem_by_id(problem_id, data_type, dt)
    if not problem:
        raise HTTPException(404, "문제를 찾을 수 없습니다.")
    
    prefix = "pa_" if data_type == "pa" else "stream_"
    tables = get_table_schema(prefix)
    
    return ProblemDetailResponse(problem=problem, tables=tables)
