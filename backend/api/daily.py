from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from backend.generator.daily_challenge_writer import (
    load_daily_challenge,
    get_latest_challenge
)
from backend.api.auth import get_user_id_from_request
from backend.services.problem_service import (
    get_user_set_index, 
    get_logger,
    filter_problems_by_set
)
from backend.common.date_utils import get_today_kst
from backend.api.admin import run_full_generation_task

logger = get_logger(__name__)
router = APIRouter(prefix="/daily", tags=["Daily Challenge"])


@router.get("/latest")
async def get_latest_daily_challenge(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    가장 최근 Daily Challenge 조회 (사용자별 세트 필터링)
    """
    challenge = get_latest_challenge()
    
    if not challenge:
        # [PORTFOLIO-MODE] 오늘 챌린지 없으면 가장 최신 챌린지 로드
        logger.info("No Daily Challenge for today. Falling back to latest available challenge.")
        challenge = get_latest_challenge()
        
    if not challenge:
        # 데이터가 아예 없는 경우에만 에러 (또는 기본값)
        raise HTTPException(
            status_code=404,
            detail="이용 가능한 데일리 챌린지가 없습니다."
        )
    
    user_id = get_user_id_from_request(request)
    target_date = date.fromisoformat(challenge.get("date", get_today_kst().isoformat()))
    
    # 문제 필터링
    filtered_problems = filter_problems_by_set(
        challenge.get("problems", []), 
        user_id, 
        target_date
    )
    challenge["problems"] = filtered_problems

    # UI 호환성을 위해 scenario 정보를 metadata로 병합하고 카운트 갱신
    if "scenario" in challenge and "metadata" in challenge:
        scenario = challenge["scenario"]
        challenge["metadata"].update({
            "company_name": scenario.get("company_name"),
            "company_description": scenario.get("company_description"),
            "product_type": scenario.get("product_type"),
            "north_star": scenario.get("north_star"),
            "key_metrics": scenario.get("key_metrics"),
            # 필터링된 결과에 맞게 카운트 갱신 (사용자 혼동 방지)
            "total_problems": len(filtered_problems),
            "pa_count": sum(1 for p in filtered_problems if p.get('problem_type') == 'pa'),
            "stream_count": sum(1 for p in filtered_problems if p.get('problem_type') == 'stream'),
        })
    
    return challenge


@router.get("/{target_date}")
async def get_daily_challenge(
    request: Request, 
    target_date: str,
    background_tasks: BackgroundTasks
):
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
        # [PORTFOLIO-MODE] 특정 날짜 데이터 없으면 최신 데이터로 리다이렉트 유도하거나 안내
        logger.warning(f"Challenge not found for {target_date}.")
        raise HTTPException(
            status_code=404,
            detail=f"{target_date}의 데이터를 찾을 수 없습니다."
        )
    
    user_id = get_user_id_from_request(request)
    
    # 문제 필터링
    filtered_problems = filter_problems_by_set(
        challenge.get("problems", []), 
        user_id, 
        dt
    )
    challenge["problems"] = filtered_problems

    # UI 호환성을 위해 scenario 정보를 metadata로 병합하고 카운트 갱신
    if "scenario" in challenge and "metadata" in challenge:
        scenario = challenge["scenario"]
        challenge["metadata"].update({
            "company_name": scenario.get("company_name"),
            "company_description": scenario.get("company_description"),
            "product_type": scenario.get("product_type"),
            "north_star": scenario.get("north_star"),
            "key_metrics": scenario.get("key_metrics"),
            # 필터링된 결과에 맞게 카운트 갱신
            "total_problems": len(filtered_problems),
            "pa_count": sum(1 for p in filtered_problems if p.get('problem_type') == 'pa'),
            "stream_count": sum(1 for p in filtered_problems if p.get('problem_type') == 'stream'),
        })
    
    return challenge


@router.get("/{target_date}/problems")
async def get_daily_problems_only(
    request: Request, 
    target_date: str,
    background_tasks: BackgroundTasks
):
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
    
    metadata = challenge.get("metadata", {}).copy()
    scenario = challenge.get("scenario", {})
    
    # 문제 필터링
    filtered_problems = filter_problems_by_set(challenge.get("problems", []), user_id, dt)
    
    # UI 호환성을 위해 scenario 정보를 metadata로 병합하고 카운트 갱신
    metadata.update({
        "company_name": scenario.get("company_name"),
        "company_description": scenario.get("company_description"),
        "product_type": scenario.get("product_type"),
        "north_star": scenario.get("north_star"),
        "key_metrics": scenario.get("key_metrics"),
        "total_problems": len(filtered_problems),
        "pa_count": sum(1 for p in filtered_problems if p.get('problem_type') == 'pa'),
        "stream_count": sum(1 for p in filtered_problems if p.get('problem_type') == 'stream'),
    })

    return {
        "date": target_date,
        "problems": filtered_problems,
        "metadata": metadata
    }


@router.get("/{target_date}/scenario")
async def get_daily_scenario(
    target_date: str,
    background_tasks: BackgroundTasks
):
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
async def get_daily_tables(
    target_date: str,
    background_tasks: BackgroundTasks
):
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
