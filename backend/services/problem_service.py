# backend/services/problem_service.py
"""문제 서비스 - DB 기반 문제 관리"""
from datetime import date
from typing import Optional, List
from backend.services.database import postgres_connection
from backend.common.logging import get_logger

logger = get_logger(__name__)


def get_problems_from_db(problem_date: date, data_type: str, set_index: int = 0) -> List[dict]:
    """DB에서 문제 조회"""
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT id, problem_date, data_type, set_index, difficulty,
                       title, description, initial_sql, answer_sql,
                       expected_columns, hints, schema_info
                FROM problems
                WHERE problem_date = %s AND data_type = %s AND set_index = %s
                ORDER BY id
            """, [problem_date, data_type, set_index])
            
            if len(df) > 0:
                return df.to_dict(orient="records")
            return []
    except Exception as e:
        logger.error(f"Failed to get problems from DB: {e}")
        return []


def save_problems_to_db(problems: List[dict], problem_date: date, data_type: str, set_index: int = 0) -> int:
    """문제를 DB에 저장"""
    saved = 0
    try:
        with postgres_connection() as pg:
            for p in problems:
                try:
                    pg.execute("""
                        INSERT INTO problems (problem_date, data_type, set_index, difficulty,
                                             title, description, initial_sql, answer_sql,
                                             expected_columns, hints, schema_info)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (problem_date, data_type, set_index, title) DO UPDATE SET
                            description = EXCLUDED.description,
                            answer_sql = EXCLUDED.answer_sql,
                            expected_columns = EXCLUDED.expected_columns,
                            hints = EXCLUDED.hints
                    """, (
                        problem_date, data_type, set_index,
                        p.get("difficulty"),
                        p.get("title", "Untitled"),
                        p.get("description"),
                        p.get("initial_sql"),
                        p.get("answer_sql"),
                        p.get("expected_columns"),
                        p.get("hints"),
                        p.get("schema_info")
                    ))
                    saved += 1
                except Exception as e:
                    logger.warning(f"Failed to save problem '{p.get('title')}': {e}")
        
        logger.info(f"Saved {saved}/{len(problems)} problems to DB")
        return saved
    except Exception as e:
        logger.error(f"Failed to save problems to DB: {e}")
        return 0


def get_daily_tip(tip_date: date) -> Optional[dict]:
    """오늘의 팁 조회"""
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT content, category, model_used
                FROM daily_tips
                WHERE tip_date = %s
            """, [tip_date])
            
            if len(df) > 0:
                return df.iloc[0].to_dict()
            return None
    except Exception as e:
        logger.error(f"Failed to get daily tip: {e}")
        return None


def save_daily_tip(tip_date: date, content: str, category: str = None, model_used: str = None) -> bool:
    """오늘의 팁 저장"""
    try:
        with postgres_connection() as pg:
            pg.execute("""
                INSERT INTO daily_tips (tip_date, content, category, model_used)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (tip_date) DO UPDATE SET
                    content = EXCLUDED.content,
                    category = EXCLUDED.category,
                    model_used = EXCLUDED.model_used
            """, (tip_date, content, category, model_used))
        return True
    except Exception as e:
        logger.error(f"Failed to save daily tip: {e}")
        return False


def log_worker_execution(job_type: str, status: str, model_used: str = None,
                         tokens_used: int = None, duration_ms: int = None,
                         result_count: int = None, error_message: str = None):
    """워커 실행 로그 기록"""
    try:
        with postgres_connection() as pg:
            pg.execute("""
                INSERT INTO worker_logs (job_type, status, model_used, tokens_used,
                                        duration_ms, result_count, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (job_type, status, model_used, tokens_used, duration_ms, result_count, error_message))
    except Exception as e:
        logger.error(f"Failed to log worker execution: {e}")
