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
            
            # API 사용량 로그 - 누락된 컬럼 추가 (스키마 변경 시 자동 반영용)
            try:
                cols = pg.fetch_df("SELECT column_name FROM information_schema.columns WHERE table_name = 'api_usage_logs'")
                existing_cols = set(cols['column_name'].tolist())
                if 'purpose' not in existing_cols:
                    pg.execute("ALTER TABLE public.api_usage_logs ADD COLUMN purpose VARCHAR(100)")
                if 'total_tokens' not in existing_cols:
                    pg.execute("ALTER TABLE public.api_usage_logs ADD COLUMN total_tokens INTEGER DEFAULT 0")
            except Exception as e:
                logger.warning(f"Failed to update api_usage_logs columns: {e}")

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
            # problems 테이블 - updated_at 컬럼 수동 체크 (CREAT TABLE IF NOT EXISTS에서 누락될 수 있음)
            try:
                cols = pg.fetch_df("SELECT column_name FROM information_schema.columns WHERE table_name = 'problems'")
                if 'updated_at' not in set(cols['column_name'].tolist()):
                    pg.execute("ALTER TABLE public.problems ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()")
            except Exception as e:
                logger.warning(f"Failed to add updated_at to problems table: {e}")

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

            # 12. dataset_versions - 문제/데이터 생성 이력 관리
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.dataset_versions (
                    version_id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT NOW(),
                    generation_date DATE NOT NULL,
                    generation_type TEXT NOT NULL,
                    data_type TEXT DEFAULT 'pa',
                    problem_count INTEGER DEFAULT 0,
                    n_users INTEGER DEFAULT 0,
                    n_events INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    duration_ms INTEGER
                );
            """)
            # 기존 테이블에 새 컬럼 추가 (호환성)
            try:
                cols = pg.fetch_df("SELECT column_name FROM information_schema.columns WHERE table_name = 'dataset_versions'")
                existing_cols = set(cols['column_name'].tolist())
                if 'generation_date' not in existing_cols:
                    pg.execute("ALTER TABLE public.dataset_versions ADD COLUMN generation_date DATE")
                if 'generation_type' not in existing_cols:
                    pg.execute("ALTER TABLE public.dataset_versions ADD COLUMN generation_type TEXT")
                if 'data_type' not in existing_cols:
                    pg.execute("ALTER TABLE public.dataset_versions ADD COLUMN data_type TEXT DEFAULT 'pa'")
                if 'problem_count' not in existing_cols:
                    pg.execute("ALTER TABLE public.dataset_versions ADD COLUMN problem_count INTEGER DEFAULT 0")
                if 'status' not in existing_cols:
                    pg.execute("ALTER TABLE public.dataset_versions ADD COLUMN status TEXT DEFAULT 'success'")
                if 'error_message' not in existing_cols:
                    pg.execute("ALTER TABLE public.dataset_versions ADD COLUMN error_message TEXT")
                if 'duration_ms' not in existing_cols:
                    pg.execute("ALTER TABLE public.dataset_versions ADD COLUMN duration_ms INTEGER")
            except Exception as e:
                logger.warning(f"Failed to update dataset_versions columns: {e}")
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.scheduler_status (
                    job_id TEXT PRIMARY KEY,
                    job_name TEXT NOT NULL,
                    last_run_at TIMESTAMP,
                    next_run_at TIMESTAMP,
                    status TEXT,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            logger.info("✓ versioning tables ready")

            # 13. rca_anomaly_metadata - RCA 시나리오 이상 패턴 메타데이터
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.rca_anomaly_metadata (
                    id SERIAL PRIMARY KEY,
                    problem_date DATE NOT NULL,
                    product_type VARCHAR(50) NOT NULL,
                    anomaly_type VARCHAR(100) NOT NULL,
                    anomaly_params JSONB NOT NULL DEFAULT '{}',
                    affected_scope TEXT,
                    description TEXT,
                    hints JSONB NOT NULL DEFAULT '[]',
                    root_cause TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            pg.execute("CREATE INDEX IF NOT EXISTS idx_rca_anomaly_date ON public.rca_anomaly_metadata(problem_date)")
            pg.execute("CREATE INDEX IF NOT EXISTS idx_rca_anomaly_type ON public.rca_anomaly_metadata(anomaly_type)")
            logger.info("✓ rca_anomaly_metadata table ready")

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
