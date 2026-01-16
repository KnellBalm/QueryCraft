# backend/api/health.py
"""헬스 체크 API"""
from fastapi import APIRouter
from datetime import date
import os

from backend.common.date_utils import get_today_kst
from backend.services.database import postgres_connection
from backend.common.logging import get_logger

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)


@router.get("/ping")
async def ping():
    """기본 헬스 체크"""
    return {"status": "ok", "service": "QueryCraft Backend"}


@router.get("/daily-problems")
async def check_daily_problems():
    """오늘의 문제 확인 및 자동 생성 트리거
    
    - 오늘 날짜 문제가 있으면: 200 OK
    - 문제가 없으면: 자동 생성 트리거 후 202 Accepted
    - Cloud Monitoring Uptime Check에서 호출됨
    """
    today = get_today_kst()
    
    try:
        with postgres_connection() as pg:
            # PA와 Stream 문제 개수 확인
            df = pg.fetch_df("""
                SELECT data_type, COUNT(*) as cnt 
                FROM public.problems 
                WHERE problem_date = %s
                GROUP BY data_type
            """, [today])
            
            pa_count = 0
            stream_count = 0
            
            for _, row in df.iterrows():
                if row.get("data_type") == "pa":
                    pa_count = int(row.get("cnt", 0))
                elif row.get("data_type") == "stream":
                    stream_count = int(row.get("cnt", 0))
            
            total_count = pa_count + stream_count
            
            # 문제가 이미 있으면 OK 반환
            if total_count > 0:
                return {
                    "status": "ok",
                    "today": str(today),
                    "pa_problems": pa_count,
                    "stream_problems": stream_count,
                    "total": total_count
                }
            
            # 문제가 없으면 자동 생성 트리거
            logger.info(f"[HEALTH] No problems found for {today}, triggering auto-generation")
            
            try:
                import requests
                
                # Cloud Functions를 통해 생성 트리거
                function_url = "https://us-central1-querycraft-483512.cloudfunctions.net/problem-worker"
                scheduler_key = os.environ.get("SCHEDULER_API_KEY", "")
                
                if scheduler_key:
                    # 백그라운드로 비동기 호출 (응답 대기 안 함)
                    import asyncio
                    asyncio.create_task(trigger_generation_async(function_url, scheduler_key))
                    
                    return {
                        "status": "generating",
                        "today": str(today),
                        "pa_problems": 0,
                        "stream_problems": 0,
                        "total": 0,
                        "message": "자동 생성 트리거됨"
                    }
                else:
                    logger.warning("[HEALTH] SCHEDULER_API_KEY not set, cannot trigger auto-generation")
                    return {
                        "status": "missing",
                        "today": str(today),
                        "pa_problems": 0,
                        "stream_problems": 0,
                        "total": 0,
                        "message": "문제 없음, SCHEDULER_API_KEY 미설정"
                    }
                    
            except Exception as e:
                logger.error(f"[HEALTH] Failed to trigger auto-generation: {e}")
                return {
                    "status": "missing",
                    "today": str(today),
                    "pa_problems": 0,
                    "stream_problems": 0,
                    "total": 0,
                    "message": f"문제 없음, 자동 생성 실패: {str(e)}"
                }
                
    except Exception as e:
        logger.error(f"[HEALTH] Database check failed: {e}")
        return {
            "status": "error",
            "today": str(today),
            "message": f"DB 조회 실패: {str(e)}"
        }


async def trigger_generation_async(url: str, api_key: str):
    """비동기로 문제 생성 트리거"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"X-Scheduler-Key": api_key}
            async with session.post(url, headers=headers, timeout=5) as response:
                logger.info(f"[HEALTH] Auto-generation triggered: {response.status}")
    except Exception as e:
        logger.error(f"[HEALTH] Async trigger failed: {e}")
