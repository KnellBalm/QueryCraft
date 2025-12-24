# backend/api/stats.py
"""통계 API"""
from typing import Optional
from fastapi import APIRouter

from backend.schemas.submission import UserStats, SubmissionHistory
from backend.services.stats_service import get_user_stats, get_submission_history


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/me", response_model=UserStats)
async def get_my_stats():
    """내 통계 조회"""
    return get_user_stats()


@router.get("/history", response_model=list[SubmissionHistory])
async def get_history(limit: int = 20, data_type: Optional[str] = None):
    """제출 이력 조회 (data_type: 'pa' 또는 'stream' 필터링)"""
    return get_submission_history(limit, data_type)

