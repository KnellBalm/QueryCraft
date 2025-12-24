# backend/services/stats_service.py
"""통계 서비스 - PostgreSQL submissions 테이블 사용"""
from datetime import date, timedelta
from typing import List

from backend.services.database import postgres_connection
from backend.schemas.submission import UserStats, SubmissionHistory


def get_user_stats() -> UserStats:
    """사용자 통계 조회"""
    streak = get_streak()
    level_info = get_level()
    
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
                FROM submissions
            """)
        
        total = int(df.iloc[0]["total"]) if len(df) > 0 else 0
        correct = int(df.iloc[0]["correct"]) if len(df) > 0 and df.iloc[0]["correct"] else 0
        accuracy = (correct / total * 100) if total > 0 else 0
    except Exception:
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
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT DISTINCT session_date::date as session_date
                FROM submissions 
                ORDER BY session_date DESC 
                LIMIT 30
            """)
        dates = {row["session_date"].isoformat() if hasattr(row["session_date"], 'isoformat') else str(row["session_date"]) for _, row in df.iterrows()}
    except Exception:
        dates = set()
    
    if not dates:
        return {"current": 0, "max": 0}
    
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
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
                FROM submissions
            """)
        correct = int(df.iloc[0]["correct"]) if len(df) > 0 and df.iloc[0]["correct"] else 0
    except Exception:
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


def get_submission_history(limit: int = 20, data_type: str = None) -> List[SubmissionHistory]:
    """제출 이력 조회 (data_type으로 필터링 가능)"""
    try:
        with postgres_connection() as pg:
            where_clause = ""
            if data_type:
                where_clause = f"WHERE data_type = '{data_type}'"
            
            df = pg.fetch_df(f"""
                SELECT problem_id, session_date::date as session_date, is_correct, 
                       submitted_at, feedback, data_type
                FROM submissions
                {where_clause}
                ORDER BY submitted_at DESC
                LIMIT {limit}
            """)
        
        return [
            SubmissionHistory(
                problem_id=row["problem_id"],
                session_date=str(row["session_date"]),
                is_correct=row["is_correct"],
                submitted_at=row["submitted_at"].isoformat() if row["submitted_at"] else None,
                feedback=row.get("feedback")
            )
            for _, row in df.iterrows()
        ]
    except Exception:
        return []


