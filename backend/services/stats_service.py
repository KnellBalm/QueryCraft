# backend/services/stats_service.py
"""통계 서비스 - PostgreSQL submissions 테이블 사용 (개인화)"""
from datetime import date, timedelta
from typing import List, Optional
import pandas as pd

from backend.services.database import postgres_connection
from backend.common.date_utils import get_today_kst
from backend.schemas.stats import UserStats, LevelInfo
from backend.schemas.submission import SubmissionHistory


def get_user_stats(user_id: Optional[str] = None) -> UserStats:
    """사용자 통계 조회 (개인화)"""
    streak = get_streak(user_id)
    level_info = get_level(user_id)
    
    try:
        with postgres_connection() as pg:
            if user_id:
                df = pg.fetch_df("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
                    FROM public.submissions
                    WHERE user_id = %s
                """, [user_id])
            else:
                df = pg.fetch_df("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
                    FROM public.submissions
                """)
        
        total = int(df.iloc[0]["total"]) if len(df) > 0 and pd.notnull(df.iloc[0]["total"]) else 0
        correct = int(df.iloc[0]["correct"]) if len(df) > 0 and pd.notnull(df.iloc[0]["correct"]) else 0
        accuracy = (correct / total * 100) if total > 0 else 0
    except Exception:
        total, correct, accuracy = 0, 0, 0
    
    return UserStats(
        streak=streak["current"],
        max_streak=streak["max"],
        level=f"Lv.{level_info.get('level_num', 1)} {level_info['name']}",
        total_solved=total,
        correct=level_info.get("correct", correct),
        accuracy=round(accuracy, 1),
        next_level_threshold=level_info["next"],
        score=level_info.get("score", 0),
        level_progress=level_info.get("progress", 0)
    )


def get_streak(user_id: Optional[str] = None) -> dict:
    """연속 출석 스트릭 계산 (개인화)"""
    try:
        with postgres_connection() as pg:
            if user_id:
                df = pg.fetch_df("""
                    SELECT DISTINCT session_date::date as session_date
                    FROM public.submissions 
                    WHERE user_id = %s
                    ORDER BY session_date DESC 
                    LIMIT 30
                """, [user_id])
            else:
                df = pg.fetch_df("""
                    SELECT DISTINCT session_date::date as session_date
                    FROM public.submissions 
                    ORDER BY session_date DESC 
                    LIMIT 30
                """)
        dates = {row["session_date"].isoformat() if hasattr(row["session_date"], 'isoformat') else str(row["session_date"]) for _, row in df.iterrows()}
    except Exception:
        dates = set()
    
    if not dates:
        return {"current": 0, "max": 0}
    
    streak = 0
    today = get_today_kst()
    
    # 최근 30일 데이터
    check = today
    for _ in range(30):
        if check.isoformat() in dates:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    
    return {"current": streak, "max": len(dates)}


def get_level(user_id: Optional[str] = None) -> dict:
    """사용자 레벨 및 XP 조회 (DB 저장값 우선)"""
    try:
        with postgres_connection() as pg:
            if user_id:
                # 1. users 테이블에서 직접 조회
                user_row = pg.fetch_one("SELECT xp, level FROM public.users WHERE id = %s", [user_id])
                if user_row:
                    total_score = int(user_row.get("xp", 0))
                    # DB 레벨이 100단위가 아닐 경우를 대비해 재계산 로직 유지하거나 원본 노출
                    db_level = int(user_row.get("level", 1))
                else:
                    total_score, db_level = 0, 1
            else:
                # 전체 평균 등 (필요 시 submissions 활용)
                df = pg.fetch_df("""
                    SELECT 
                        COALESCE(SUM(
                            CASE difficulty
                                WHEN 'easy' THEN 10
                                WHEN 'medium' THEN 25
                                WHEN 'hard' THEN 50
                                ELSE 25
                            END
                        ), 0) as total_score
                    FROM public.submissions
                    WHERE is_correct = true
                """)
                total_score = int(df.iloc[0]["total_score"]) if len(df) > 0 else 0
                db_level = (total_score // 100) + 1

            # 정답 개수는 여전히 submissions에서 가져옴
            if user_id:
                cnt_df = pg.fetch_df("SELECT COUNT(*) as correct_count FROM public.submissions WHERE is_correct = true AND user_id = %s", [user_id])
                correct_count = int(cnt_df.iloc[0]["correct_count"]) if len(cnt_df) > 0 else 0
            else:
                cnt_df = pg.fetch_df("SELECT COUNT(*) as correct_count FROM public.submissions WHERE is_correct = true")
                correct_count = int(cnt_df.iloc[0]["correct_count"]) if len(cnt_df) > 0 else 0
                
    except Exception:
        total_score = 0
        correct_count = 0
        db_level = 1
    
    # 레벨 명칭 (UI 표시용)
    levels = [
        (0, "🌱 Beginner"),
        (50, "🌿 Learner"),
        (150, "🌳 Analyst"),
        (400, "⭐ Senior"),
        (800, "🏆 Expert"),
        (1500, "👑 Master")
    ]
    
    level_name = "🌱 Beginner"
    next_threshold = 50
    current_threshold = 0
    
    for threshold, name in levels:
        if total_score >= threshold:
            level_name = name
            current_threshold = threshold
        else:
            next_threshold = threshold
            break
    else:
        next_threshold = total_score
    
    progress = 0
    if next_threshold > current_threshold:
        progress = int((total_score - current_threshold) / (next_threshold - current_threshold) * 100)
    
    # DB에 레벨 이름이 저장되어 있지 않으므로 계산된 이름 사용, 단 레벨 숫자는 DB값 존중 가능
    return {
        "name": level_name,
        "score": total_score,
        "level_num": db_level,
        "next": next_threshold,
        "correct": correct_count,
        "progress": min(progress, 100)
    }


def get_submission_history(limit: int = 20, data_type: str = None, user_id: Optional[str] = None) -> List[SubmissionHistory]:
    """제출 이력 조회 (개인화)"""
    try:
        with postgres_connection() as pg:
            conditions = []
            params = []
            
            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)
            
            if data_type:
                conditions.append("data_type = %s")
                params.append(data_type)
            
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            params.append(limit)
            
            df = pg.fetch_df(f"""
                SELECT problem_id, data_type, is_correct, feedback, submitted_at
                FROM public.submissions
                {where_clause}
                ORDER BY submitted_at DESC
                LIMIT %s
            """, params)
        return [
            SubmissionHistory(
                problem_id=row["problem_id"],
                data_type=row["data_type"],
                is_correct=row["is_correct"],
                feedback=row["feedback"] or "",
                submitted_at=(row["submitted_at"].isoformat() if hasattr(row["submitted_at"], "isoformat") else str(row["submitted_at"]))
            )
            for _, row in df.iterrows()
        ]
    except Exception:
        return []
