import logging
from datetime import datetime
from typing import Optional
from backend.services.database import postgres_connection

# 기본 로거
logger = logging.getLogger(__name__)

# 로그 카테고리
class LogCategory:
    PROBLEM_GENERATION = "problem_generation"
    USER_ACTION = "user_action"
    SCHEDULER = "scheduler"
    SYSTEM = "system"
    API = "api"

# 로그 레벨
class LogLevel:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"

class PostgresLoggingHandler(logging.Handler):
    """표준 logging 모듈과 연동되는 DB 핸들러"""
    def emit(self, record):
        try:
            # 재귀 루프 방지 (db_logger 자체 로그는 DB에 안 쌓음)
            if record.name == __name__:
                return
                
            message = self.format(record)
            category = getattr(record, 'category', LogCategory.SYSTEM)
            
            with postgres_connection() as pg:
                pg.execute("""
                    INSERT INTO public.logs (category, level, message, source, user_id, extra_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    category,
                    record.levelname.lower(),
                    message,
                    record.name,
                    getattr(record, 'user_id', None),
                    getattr(record, 'extra_data', None)
                ))
        except Exception:
            # DB 연결 실패 시 조용히 넘김 (GCP 로그가 있으므로)
            pass

def ensure_logs_table():
    """logs 테이블 생성"""
    try:
        with postgres_connection() as pg:
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.logs (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR(50) NOT NULL,
                    level VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    source VARCHAR(100),
                    user_id VARCHAR(100),
                    extra_data TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            pg.execute("CREATE INDEX IF NOT EXISTS idx_logs_category ON public.logs(category)")
            pg.execute("CREATE INDEX IF NOT EXISTS idx_logs_created_at ON public.logs(created_at DESC)")
    except Exception as e:
        logger.error(f"Failed to create logs table: {e}")

def db_log(category, message, level=LogLevel.INFO, source=None, user_id=None, extra_data=None):
    """수동 로그 기록 (기존 코드 호환용)"""
    try:
        with postgres_connection() as pg:
            pg.execute("""
                INSERT INTO public.logs (category, level, message, source, user_id, extra_data)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (category, level, message, source, user_id, extra_data))
    except Exception as e:
        logger.error(f"Failed to save log to DB: {e}")

def get_logs(category: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> list:
    """로그 조회 (관리자용)"""
    try:
        with postgres_connection() as pg:
            conditions = []
            params = []
            if category:
                conditions.append("category = %s")
                params.append(category)
            if level:
                conditions.append("level = %s")
                params.append(level)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            params.append(limit)
            
            df = pg.fetch_df(f"""
                SELECT id, category, level, message, source, user_id, extra_data, created_at
                FROM public.logs {where_clause}
                ORDER BY created_at DESC LIMIT %s
            """, params)
            
            return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        return []

# 테이블 자동 생성 (모듈 로드 시)
# 주의: 이 시점에는 아직 DB 설정이 안 되어 있을 수 있으므로 init_database 이후에 다시 호출하는 것이 안전
# ensure_logs_table()
