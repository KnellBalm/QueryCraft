# backend/api/problems.py
"""문제 API"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request

from backend.schemas.problem import (
    ProblemListResponse, ProblemDetailResponse, TableSchema
)
from backend.services.problem_service import (
    get_problems, get_problem_by_id, get_table_schema
)
from backend.services.recommendation_service import get_recommended_problems
from backend.common.date_utils import get_today_kst
from backend.api.auth import get_session


router = APIRouter(prefix="/problems", tags=["problems"])


def get_user_id_from_request(request: Request) -> Optional[str]:
    """Request에서 user_id 추출"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    session = get_session(session_id)
    if not session or not session.get("user"):
        return None
    return session["user"].get("id")


@router.get("/schema/{data_type}", response_model=list[TableSchema])
async def get_schema(data_type: str):
    """테이블 스키마 조회"""
    prefix = "stream_" if data_type == "stream" else "pa_"
    return get_table_schema(prefix)


@router.get("/{data_type}", response_model=ProblemListResponse)
async def list_problems(
    request: Request,
    data_type: str,
    target_date: Optional[str] = Query(None, description="날짜 (YYYY-MM-DD)")
):
    """문제 목록 조회 (사용자별 세트 할당)"""
    if data_type not in ("pa", "stream", "rca"):
        raise HTTPException(400, "data_type은 'pa', 'stream', 또는 'rca'이어야 합니다.")
    
    if target_date:
        try:
            dt = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(400, "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
    else:
        dt = get_today_kst()
    
    user_id = get_user_id_from_request(request)
    problems = get_problems(dt, data_type, user_id)
    completed = sum(1 for p in problems if p.is_completed)
    
    # 메타데이터 추가
    metadata = None
    if data_type in ("pa", "rca"):
        from problems.prompt import get_current_product_type
        from backend.generator.product_config import get_kpi_guide
        
        p_type = get_current_product_type()
        guide = get_kpi_guide(p_type)
        if guide:
            from backend.schemas.problem import DatasetMetadata
            metadata = DatasetMetadata(
                company_name=guide.get("company_name", "Unknown Corp"),
                company_description=guide.get("company_description", ""),
                product_type=p_type,
                north_star=guide.get("north_star"),
                key_metrics=guide.get("key_metrics")
            )
    
    return ProblemListResponse(
        date=dt.isoformat(),
        data_type=data_type,
        problems=problems,
        total=len(problems),
        completed=completed,
        metadata=metadata
    )


@router.get("/{data_type}/{problem_id}", response_model=ProblemDetailResponse)
async def get_problem_detail(
    request: Request,
    data_type: str,
    problem_id: str,
    target_date: Optional[str] = Query(None)
):
    """문제 상세 조회"""
    if target_date:
        try:
            dt = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(400, "날짜 형식이 올바르지 않습니다.")
    else:
        dt = get_today_kst()
    
    user_id = get_user_id_from_request(request)
    problem = get_problem_by_id(problem_id, data_type, dt, user_id)
    
    if not problem:
        raise HTTPException(404, "문제를 찾을 수 없습니다.")
    
    # 메타데이터 추가
    metadata = None
    if data_type in ("pa", "rca"):
        from problems.prompt import get_current_product_type
        from backend.generator.product_config import get_kpi_guide
        
        p_type = get_current_product_type()
        guide = get_kpi_guide(p_type)
        if guide:
            from backend.schemas.problem import DatasetMetadata
            metadata = DatasetMetadata(
                company_name=guide.get("company_name", "Unknown Corp"),
                company_description=guide.get("company_description", ""),
                product_type=p_type,
                north_star=guide.get("north_star"),
                key_metrics=guide.get("key_metrics")
            )
    
    return ProblemDetailResponse(
        problem=problem,
        tables=get_table_schema("stream_" if data_type == "stream" else "pa_"),
        metadata=metadata
    )


@router.get("/recommend", response_model=list[Problem])
async def recommend_problems(request: Request, limit: int = 3):
    """개인화 문제 추천"""
    user_id = get_user_id_from_request(request)
    if not user_id:
        # 로그인 안 된 경우 인기 문제나 최신 문제 리턴 (가짜 ID)
        problems = get_recommended_problems("guest", limit)
    else:
        problems = get_recommended_problems(user_id, limit)
    return problems
