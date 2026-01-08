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
                CREATE TABLE IF NOT EXISTS public.users (
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
                CREATE TABLE IF NOT EXISTS public.user_problem_sets (
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
                CREATE TABLE IF NOT EXISTS public.daily_sessions (
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
                CREATE TABLE IF NOT EXISTS public.submissions (
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
                CREATE TABLE IF NOT EXISTS public.api_usage_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    purpose VARCHAR(100),
                    model VARCHAR(50),
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    user_id TEXT
                )
            """)
            logger.info("✓ api_usage_logs table ready")
            
            # 6. logs 테이블 (시스템 로그)
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
            logger.info("✓ logs table ready")
            
            # 7. problems 테이블 (파일 → DB 이전)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.problems (
                    id SERIAL PRIMARY KEY,
                    problem_date DATE NOT NULL,
                    data_type VARCHAR(20) NOT NULL,
                    set_index INTEGER DEFAULT 0,
                    difficulty VARCHAR(20),
                    title TEXT NOT NULL,
                    description TEXT,
                    initial_sql TEXT,
                    answer_sql TEXT,
                    expected_columns JSONB,
                    hints JSONB,
                    schema_info TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(problem_date, data_type, set_index, title)
                )
            """)
            pg.execute("CREATE INDEX IF NOT EXISTS idx_problems_date ON public.problems(problem_date DESC)")
            pg.execute("CREATE INDEX IF NOT EXISTS idx_problems_type ON public.problems(data_type)")
            logger.info("✓ problems table ready")
            
            # 8. daily_tips 테이블
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.daily_tips (
                    id SERIAL PRIMARY KEY,
                    tip_date DATE UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    category VARCHAR(50),
                    model_used VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            logger.info("✓ daily_tips table ready")
            
            # 9. worker_logs 테이블 (Cloud Functions 로그)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.worker_logs (
                    id SERIAL PRIMARY KEY,
                    job_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    model_used VARCHAR(50),
                    tokens_used INTEGER,
                    duration_ms INTEGER,
                    result_count INTEGER,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            logger.info("✓ worker_logs table ready")

            # 10. persistent_sessions 테이블 (다중 인스턴스 세션 공유)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.persistent_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            pg.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON public.persistent_sessions(expires_at)")
            logger.info("✓ persistent_sessions table ready")

            # 11. [분석용] stream_events & stream_daily_metrics
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.stream_events (
                    user_id INT,
                    session_id TEXT,
                    event_name TEXT,
                    event_time TIMESTAMP,
                    device TEXT,
                    channel TEXT
                );
            """)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.stream_daily_metrics (
                    date DATE,
                    revenue DOUBLE PRECISION,
                    purchases INT
                );
            """)
            logger.info("✓ stream tables ready")

            # 11. [분석용] PA 테이블 (pa_users, pa_sessions, pa_events, pa_orders)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.pa_users (
                    user_id TEXT PRIMARY KEY,
                    signup_at TIMESTAMP NOT NULL,
                    country TEXT NOT NULL,
                    channel TEXT NOT NULL
                );
            """)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.pa_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES public.pa_users(user_id) ON DELETE CASCADE,
                    started_at TIMESTAMP NOT NULL,
                    device TEXT NOT NULL
                );
            """)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.pa_events (
                    event_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES public.pa_users(user_id) ON DELETE CASCADE,
                    session_id TEXT NOT NULL REFERENCES public.pa_sessions(session_id) ON DELETE CASCADE,
                    event_time TIMESTAMP NOT NULL,
                    event_name TEXT NOT NULL
                );
            """)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.pa_orders (
                    order_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES public.pa_users(user_id) ON DELETE CASCADE,
                    order_time TIMESTAMP NOT NULL,
                    amount INT NOT NULL
                );
            """)
            logger.info("✓ PA tables ready")

            # 12. dataset_versions & current_product_type
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.dataset_versions (
                    version_id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT NOW(),
                    generator_type TEXT,
                    start_date DATE,
                    end_date DATE,
                    n_users BIGINT,
                    n_events BIGINT
                );
            """)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.current_product_type (
                    id INT PRIMARY KEY DEFAULT 1,
                    product_type TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            logger.info("✓ versioning tables ready")
            
            # 관리자 설정
            pg.execute("""
                UPDATE public.users SET is_admin = TRUE 
                WHERE email IN ('naca11@mobigen.com', 'naca11@naver.com')
            """)
            
            logger.info("✅ Database initialization completed successfully!")
            return True, None
            
    except Exception as e:
        err = str(e)
        logger.error(f"Database initialization failed: {err}")
        return False, err
