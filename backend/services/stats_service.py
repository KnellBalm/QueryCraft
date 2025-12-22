# backend/services/stats_service.py
"""통계 서비스"""
from datetime import date, timedelta
from typing import List

from backend.services.database import duckdb_connection
from backend.schemas.submission import UserStats, SubmissionHistory


def get_user_stats() -> UserStats:
    """사용자 통계 조회"""
    streak = get_streak()
    level_info = get_level()
    
    try:
        with duckdb_connection() as duck:
            result = duck.fetchone("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
                FROM pa_submissions
            """)
        
        total = result.get("total", 0) or 0
        correct = result.get("correct", 0) or 0
        accuracy = (correct / total * 100) if total > 0 else 0
    except:
        total, correct, accuracy = 0, 0, 0
    
    return UserStats(
        streak=streak["current"],
        max_streak=streak["max"],
        level=level_info["name"],
        total_solved=total,
        correct=correct,
        accuracy=round(accuracy, 1),
        next_level_threshold=level_info["next"]
    )


def get_streak() -> dict:
    """연속 출석 스트릭 계산"""
    try:
        with duckdb_connection() as duck:
            result = duck.fetchall("""
                SELECT DISTINCT session_date 
                FROM pa_submissions 
                ORDER BY session_date DESC 
                LIMIT 30
            """)
    except:
        result = []
    
    if not result:
        return {"current": 0, "max": 0}
    
    dates = {r["session_date"] for r in result}
    
    streak = 0
    check = date.today()
    for _ in range(30):
        if check.isoformat() in dates:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    
    return {"current": streak, "max": len(dates)}


def get_level() -> dict:
    """레벨 계산"""
    try:
        with duckdb_connection() as duck:
            result = duck.fetchone("""
                SELECT SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
                FROM pa_submissions
            """)
        correct = result.get("correct", 0) or 0
    except:
        correct = 0
    
    levels = [
        (0, "🌱 Beginner"),
        (5, "🌿 Learner"),
        (15, "🌳 Analyst"),
        (30, "⭐ Senior"),
        (50, "🏆 Expert"),
        (100, "👑 Master")
    ]
    
    level_name = "🌱 Beginner"
    next_threshold = 5
    
    for threshold, name in levels:
        if correct >= threshold:
            level_name = name
        else:
            next_threshold = threshold
            break
    
    return {"name": level_name, "correct": correct, "next": next_threshold}


def get_submission_history(limit: int = 20) -> List[SubmissionHistory]:
    """제출 이력 조회"""
    try:
        with duckdb_connection() as duck:
            rows = duck.fetchall(f"""
                SELECT problem_id, session_date, is_correct, submitted_at, feedback
                FROM pa_submissions
                ORDER BY submitted_at DESC
                LIMIT {limit}
            """)
        
        return [SubmissionHistory(**r) for r in rows]
    except:
        return []
