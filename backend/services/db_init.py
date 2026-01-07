# backend/services/db_init.py
"""
데이터베이스 초기화 - 백엔드 시작 시 모든 테이블 생성
"""
from backend.services.database import postgres_connection
from backend.common.logging import get_logger

logger = get_logger(__name__)


def init_database():
    """PostgreSQL 데이터베이스 초기화 - 모든 테이블 생성"""
    try:
        with postgres_connection() as pg:
            logger.info("Initializing PostgreSQL database...")
            
            # 1. users 테이블
            pg.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    nickname TEXT,
                    password_hash TEXT,
                    provider TEXT,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            logger.info("✓ users table ready")
            
            # 2. user_problem_sets 테이블
            pg.execute("""
                CREATE TABLE IF NOT EXISTS user_problem_sets (
                    user_id TEXT NOT NULL,
                    session_date DATE NOT NULL,
                    data_type VARCHAR(20) NOT NULL,
                    set_index INTEGER NOT NULL,
                    assigned_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (user_id, session_date, data_type)
                )
            """)
            logger.info("✓ user_problem_sets table ready")
            
            # 3. daily_sessions 테이블
            pg.execute("""
                CREATE TABLE IF NOT EXISTS daily_sessions (
                    session_date DATE PRIMARY KEY,
                    problem_set_path TEXT NOT NULL,
                    generated_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    status TEXT CHECK (status IN ('GENERATED','STARTED','FINISHED','SKIPPED')) NOT NULL
                )
            """)
            logger.info("✓ daily_sessions table ready")
            
            # 4. submissions 테이블
            pg.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    session_date DATE NOT NULL,
                    problem_id TEXT NOT NULL,
                    data_type TEXT DEFAULT 'pa',
                    difficulty TEXT NOT NULL,
                    submitted_sql TEXT,
                    submitted_at TIMESTAMP NOT NULL,
                    is_correct BOOLEAN NOT NULL,
                    error_category TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    execution_time_ms INTEGER,
                    note TEXT
                )
            """)
            logger.info("✓ submissions table ready")
            
            # 5. api_usage_logs 테이블
            pg.execute("""
                CREATE TABLE IF NOT EXISTS api_usage_logs (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    endpoint TEXT NOT NULL,
                    model TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    cost_usd DECIMAL(10, 6),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            logger.info("✓ api_usage_logs table ready")
            
            # 6. logs 테이블 (시스템 로그)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS logs (
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
            pg.execute("CREATE INDEX IF NOT EXISTS idx_logs_category ON logs(category)")
            pg.execute("CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC)")
            logger.info("✓ logs table ready")
            
            # 관리자 설정
            pg.execute("""
                UPDATE users SET is_admin = TRUE 
                WHERE email IN ('naca11@mobigen.com', 'naca11@naver.com')
            """)
            
            logger.info("✅ Database initialization completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
