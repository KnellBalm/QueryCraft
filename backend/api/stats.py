# backend/api/stats.py
"""통계 API"""
from typing import Optional
from fastapi import APIRouter, Request

from backend.schemas.submission import UserStats, SubmissionHistory
from backend.services.stats_service import get_user_stats, get_submission_history
from backend.services.database import postgres_connection
from backend.api.auth import get_session
from backend.common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])


def get_user_id_from_request(request: Request) -> Optional[str]:
    """요청에서 사용자 ID 추출"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    session = get_session(session_id)
    if not session or not session.get("user"):
        return None
    return session["user"].get("id")


@router.get("/me", response_model=UserStats)
async def get_my_stats(request: Request):
    """내 통계 조회 (개인화)"""
    user_id = get_user_id_from_request(request)
    return get_user_stats(user_id)


@router.get("/history", response_model=list[SubmissionHistory])
async def get_history(request: Request, limit: int = 20, data_type: Optional[str] = None):
    """제출 이력 조회 (개인화)"""
    user_id = get_user_id_from_request(request)
    return get_submission_history(limit, data_type, user_id)



@router.get("/leaderboard")
async def get_leaderboard(limit: int = 20):
    """리더보드 조회 - 닉네임 기준"""
    try:
        with postgres_connection() as pg:
            # 사용자별 정답 수, 연속 일수 계산
            df = pg.fetch_df("""
                WITH user_stats AS (
                    SELECT 
                        u.id,
                        COALESCE(u.nickname, u.name, 'Anonymous') as nickname,
                        COUNT(DISTINCT CASE WHEN s.is_correct THEN s.session_date END) as correct_days,
                        COUNT(CASE WHEN s.is_correct THEN 1 END) as correct_count
                    FROM public.users u
                    LEFT JOIN public.submissions s ON s.user_id = u.id
                    GROUP BY u.id, u.nickname, u.name
                )
                SELECT 
                    nickname,
                    correct_count as correct,
                    correct_days as streak,
                    CASE 
                        WHEN correct_count >= 100 THEN '🏆 Master'
                        WHEN correct_count >= 50 THEN '💎 Diamond'
                        WHEN correct_count >= 20 THEN '🥇 Gold'
                        WHEN correct_count >= 10 THEN '🥈 Silver'
                        WHEN correct_count >= 5 THEN '🥉 Bronze'
                        ELSE '🌱 Beginner'
                    END as level
                FROM user_stats
                WHERE correct_count > 0
                ORDER BY correct_count DESC, streak DESC
                LIMIT %s
            """, [limit])
            
            result = []
            for idx, row in df.iterrows():
                result.append({
                    "rank": idx + 1,
                    "nickname": row['nickname'],
                    "correct": int(row['correct']),
                    "streak": int(row['streak']),
                    "level": row['level']
                })
            
            return result
    except Exception as e:
        logger.error(f"Failed to get leaderboard: {e}")
        from fastapi import HTTPException
        raise HTTPException(500, detail=f"Database connection failed: {str(e)}")


@router.delete("/reset")
async def reset_my_stats(request: Request):
    """내 학습 기록 초기화 (submissions, user_problem_sets 삭제, XP 0으로)"""
    from backend.api.auth import get_session
    
    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            return {"success": False, "error": "로그인이 필요합니다"}
        
        session = get_session(session_id)
        if not session or not session.get("user"):
            return {"success": False, "error": "세션이 만료되었습니다"}
        
        user = session["user"]
        user_id = user["id"]
        
        with postgres_connection() as pg:
            # 1. 제출 기록 삭제
            pg.execute("DELETE FROM public.submissions WHERE user_id = %s", [user_id])
            
            # 2. 문제 세트 할당 삭제 (연속 출석 관련)
            pg.execute("DELETE FROM public.user_problem_sets WHERE user_id = %s", [user_id])
            
            # 3. XP 및 레벨 초기화
            pg.execute("UPDATE public.users SET xp = 0 WHERE id = %s", [user_id])
        
        logger.info(f"User {user['email']} reset their stats completely")
        return {"success": True, "message": "모든 학습 기록이 초기화되었습니다"}
    except Exception as e:
        logger.error(f"Failed to reset stats: {e}")
        return {"success": False, "error": str(e)}
