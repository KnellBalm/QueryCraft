from fastapi import APIRouter, HTTPException, Request
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from backend.generator.daily_challenge_writer import (
    load_daily_challenge,
    get_latest_challenge
)
from backend.api.problems import get_user_id_from_request
from backend.services.problem_service import get_user_set_index, get_logger
from backend.common.date_utils import get_today_kst

logger = get_logger(__name__)
router = APIRouter(prefix="/daily", tags=["Daily Challenge"])


def filter_problems_by_set(problems: List[dict], user_id: Optional[str], target_date: date) -> List[dict]:
    """사용자 세트에 맞는 문제만 필터링 및 프론트엔드용 필드 정규화"""
    if not problems:
        return []
    
    # 1. 문제 데이터에 set_index가 있는지 확인 (v2.0+)
    has_set_index = any('set_index' in p for p in problems)
    
    # 2. 사용자 세트 인덱스 조회 (PA 타입 기준으로 대표 할당)
    # get_user_set_index는 0 또는 1을 반환함
    set_index = get_user_set_index(user_id, target_date, "pa")
    
    if not has_set_index:
        filtered = problems[:6]
    else:
        # 3. 필터링 (set_index 매칭)
        filtered = [p for p in problems if p.get('set_index') == set_index]
    
    # 만약 필터링 결과가 없으면 (예: 데이터 생성 오류) 전체 중 6개라도 반환
    if not filtered:
        logger.warning(f"No problems found for set_index {set_index}, falling back to any 6")
        filtered = problems[:6]
    
    # 4. 프론트엔드 호환성을 위한 필드 정규화
    final_problems = []
    for p in filtered:
        p_copy = p.copy()
        # frontend/src/pages/DailyChallenge.tsx는 problem_type을 기대함
        if 'problem_type' not in p_copy:
            p_copy['problem_type'] = p_copy.get('data_type', 'pa')
        # difficulty가 누락된 경우 기본값
        if 'difficulty' not in p_copy:
            p_copy['difficulty'] = 'medium'
        # table_names가 누락된 경우 빈 리스트 (expected_columns 등에서 유추 가능하나 우선 빈 값)
        if 'table_names' not in p_copy:
            p_copy['table_names'] = p_copy.get('table_names', [])
            
        final_problems.append(p_copy)
        
    return final_problems[:6]


@router.get("/latest")
async def get_latest_daily_challenge(request: Request):
    """
    가장 최근 Daily Challenge 조회 (사용자별 세트 필터링)
    """
    challenge = get_latest_challenge()
    
    if not challenge:
        raise HTTPException(
            status_code=404,
            detail="No Daily Challenge found"
        )
    
    user_id = get_user_id_from_request(request)
    target_date = date.fromisoformat(challenge.get("date", get_today_kst().isoformat()))
    
    # 문제 필터링
    challenge["problems"] = filter_problems_by_set(
        challenge.get("problems", []), 
        user_id, 
        target_date
    )
    
    return challenge


@router.get("/{target_date}")
async def get_daily_challenge(request: Request, target_date: str):
    """
    특정 날짜의 Daily Challenge 조회 (사용자별 세트 필터링)
    """
    # 날짜 형식 검증
    try:
        dt = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {target_date}. Expected YYYY-MM-DD"
        )
    
    # Daily Challenge 로드
    challenge = load_daily_challenge(target_date)
    
    if not challenge:
        raise HTTPException(
            status_code=404,
            detail=f"Daily Challenge not found for date: {target_date}"
        )
    
    user_id = get_user_id_from_request(request)
    
    # 문제 필터링
    challenge["problems"] = filter_problems_by_set(
        challenge.get("problems", []), 
        user_id, 
        dt
    )
    
    return challenge


@router.get("/{target_date}/problems")
async def get_daily_problems_only(request: Request, target_date: str):
    """
    특정 날짜의 문제만 조회 (scenario 제외)
    """
    try:
        dt = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(400, f"Invalid date format: {target_date}")
        
    challenge = load_daily_challenge(target_date)
    
    if not challenge:
        raise HTTPException(
            status_code=404,
            detail=f"Daily Challenge not found for date: {target_date}"
        )
    
    user_id = get_user_id_from_request(request)
    
    return {
        "date": target_date,
        "problems": filter_problems_by_set(challenge.get("problems", []), user_id, dt),
        "metadata": challenge["metadata"]
    }


@router.get("/{target_date}/scenario")
async def get_daily_scenario(target_date: str):
    """
    특정 날짜의 시나리오만 조회 (문제 제외)
    
    Args:
        target_date: YYYY-MM-DD
    
    Returns:
        Scenario object
    """
    challenge = load_daily_challenge(target_date)
    
    if not challenge:
        raise HTTPException(
            status_code=404,
            detail=f"Daily Challenge not found for date: {target_date}"
        )
    
    return {
        "date": target_date,
        "scenario": challenge["scenario"]
    }


@router.get("/{target_date}/tables")
async def get_daily_tables(target_date: str):
    """
    특정 날짜의 테이블 스키마 정보 조회
    
    Args:
        target_date: YYYY-MM-DD
    
    Returns:
        Table configs
    """
    challenge = load_daily_challenge(target_date)
    
    if not challenge:
        raise HTTPException(
            status_code=404,
            detail=f"Daily Challenge not found for date: {target_date}"
        )
    
    return {
        "date": target_date,
        "tables": challenge["scenario"]["table_configs"]
    }
