# scripts/run_daily.py
"""
일일 데이터 생성 및 문제 출제 스케줄러
- Docker 컨테이너에서 상시 실행
- 매일 09:00에 파이프라인 실행
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta
import os

from dotenv import load_dotenv
load_dotenv()

from engine.postgres_engine import PostgresEngine
from engine.duckdb_engine import DuckDBEngine
from generator.data_generator_advanced import generate_data
from config.db import PostgresEnv

from common.logging import get_logger
logger = get_logger(__name__)

# -------------------------------------------------
# 환경 변수
# -------------------------------------------------
STREAM_REFRESH_WEEKDAY = int(os.getenv("STREAM_REFRESH_WEEKDAY", "6"))  # Sunday = 6
RUN_HOUR = int(os.getenv("RUN_HOUR", "9"))  # 매일 9시 실행


def init_duckdb_schema(duck: DuckDBEngine):
    """DuckDB 스키마 초기화 및 마이그레이션"""
    try:
        duck.execute(open("sql/init_duckdb.sql").read())
    except FileNotFoundError:
        logger.warning("[WARN] sql/init_duckdb.sql not found")
    
    # 마이그레이션: problem_set_path 컬럼이 없으면 추가
    try:
        duck.execute("SELECT problem_set_path FROM daily_sessions LIMIT 1")
    except Exception:
        logger.info("[MIGRATION] Adding problem_set_path column to daily_sessions")
        try:
            duck.execute("ALTER TABLE daily_sessions ADD COLUMN problem_set_path TEXT")
        except Exception:
            pass  # 이미 있으면 무시


def run_daily_pipeline():
    """일일 파이프라인 실행"""
    today = date.today()
    weekday = today.weekday()

    logger.info(f"[START] Daily pipeline for {today}")

    pg = PostgresEngine(PostgresEnv().dsn())
    duck = DuckDBEngine("data/pa_lab.duckdb")

    # DuckDB 스키마 초기화 및 마이그레이션
    init_duckdb_schema(duck)

    # ---------------------------------------------
    # 1. 전날 세션 자동 SKIPPED 처리
    # ---------------------------------------------
    try:
        duck.execute(
            """
            UPDATE daily_sessions
            SET status='SKIPPED', finished_at=now()
            WHERE session_date = ?
              AND status IN ('GENERATED','STARTED')
            """,
            [(today - timedelta(days=1)).isoformat()],
        )
    except Exception as e:
        logger.warning(f"[WARN] Failed to update yesterday's session: {e}")

    # ---------------------------------------------
    # 2. 오늘 세션 이미 있으면 종료
    # ---------------------------------------------
    if duck.exists("daily_sessions", session_date=today.isoformat()):
        logger.info("[INFO] today's session already exists")
        pg.close()
        duck.close()
        return

    # ---------------------------------------------
    # 3. PA 데이터는 매일 생성
    # ---------------------------------------------
    logger.info("[INFO] generating PA data (daily)")
    try:
        generate_data(modes=("pa",))
    except Exception as e:
        logger.error(f"[ERROR] PA data generation failed: {e}")

    # ---------------------------------------------
    # 4. Stream 데이터는 주 1회만 생성
    # ---------------------------------------------
    if weekday == STREAM_REFRESH_WEEKDAY:
        logger.info("[INFO] generating STREAM data (weekly)")
        try:
            generate_data(modes=("stream",))
        except Exception as e:
            logger.error(f"[ERROR] Stream data generation failed: {e}")
    else:
        logger.info("[INFO] skipping STREAM data generation today")

    # ---------------------------------------------
    # 5. PA 문제 생성 (매일)
    # ---------------------------------------------
    logger.info("[INFO] generating PA problems")
    pa_problem_path = None
    try:
        from problems.generator import generate as gen_pa_problems
        pa_problem_path = gen_pa_problems(today, pg)
        logger.info(f"[INFO] PA problems saved to {pa_problem_path}")
    except Exception as e:
        logger.error(f"[ERROR] PA problem generation failed: {e}")

    # ---------------------------------------------
    # 6. Stream 문제 생성 (매일)
    # ---------------------------------------------
    logger.info("[INFO] generating Stream problems")
    stream_problem_path = None
    try:
        from problems.generator_stream import generate_stream_problems
        stream_problem_path = generate_stream_problems(today, pg)
        logger.info(f"[INFO] Stream problems saved to {stream_problem_path}")
    except Exception as e:
        logger.error(f"[ERROR] Stream problem generation failed: {e}")

    # ---------------------------------------------
    # 7. 세션 기록
    # ---------------------------------------------
    try:
        duck.insert("daily_sessions", {
            "session_date": today.isoformat(),
            "problem_set_path": pa_problem_path or "",
            "generated_at": datetime.now(),
            "status": "GENERATED"
        })
    except Exception as e:
        logger.error(f"[ERROR] Failed to insert session: {e}")

    pg.close()
    duck.close()
    logger.info("[DONE] Daily pipeline completed")


def run_scheduler():
    """스케줄러 루프 - Docker 컨테이너에서 상시 실행"""
    logger.info(f"[SCHEDULER] Starting, will run at {RUN_HOUR}:00 daily")
    
    # 시작 시 데이터/문제 체크 및 초기화
    check_and_init_on_startup()
    
    while True:
        now = datetime.now()
        
        # 다음 실행 시각 계산 (오늘 또는 내일 RUN_HOUR시)
        next_run = now.replace(hour=RUN_HOUR, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        
        wait_seconds = (next_run - now).total_seconds()
        logger.info(f"[SCHEDULER] Next run at {next_run}, waiting {wait_seconds/3600:.1f} hours")
        
        time.sleep(wait_seconds)
        
        try:
            run_daily_pipeline()
        except Exception as e:
            logger.error(f"[SCHEDULER] Pipeline error: {e}")


def check_and_init_on_startup():
    """시작 시 데이터/문제 체크 및 초기화"""
    today = date.today()
    logger.info(f"[STARTUP] Checking data and problems for {today}")
    
    pg = PostgresEngine(PostgresEnv().dsn())
    duck = DuckDBEngine("data/pa_lab.duckdb")
    
    # DuckDB 스키마 초기화
    init_duckdb_schema(duck)
    
    # 1. PA 데이터 체크
    try:
        df = pg.fetch_df("SELECT COUNT(*) as cnt FROM pa_users")
        pa_count = int(df.iloc[0]["cnt"])
        logger.info(f"[STARTUP] PA users count: {pa_count}")
        
        if pa_count == 0:
            logger.info("[STARTUP] PA data missing, generating...")
            generate_data(modes=("pa",))
            logger.info("[STARTUP] PA data generated")
    except Exception as e:
        logger.warning(f"[STARTUP] PA data check failed: {e}, generating...")
        try:
            generate_data(modes=("pa",))
        except Exception as e2:
            logger.error(f"[STARTUP] PA data generation failed: {e2}")
    
    # 2. 오늘 PA 문제 체크
    pa_problem_path = f"problems/daily/{today.isoformat()}.json"
    if not os.path.exists(pa_problem_path):
        logger.info(f"[STARTUP] Today's PA problems missing, generating...")
        try:
            from problems.generator import generate as gen_pa_problems
            gen_pa_problems(today, pg)
            logger.info(f"[STARTUP] PA problems generated: {pa_problem_path}")
        except Exception as e:
            logger.error(f"[STARTUP] PA problem generation failed: {e}")
    else:
        logger.info(f"[STARTUP] Today's PA problems exist: {pa_problem_path}")
    
    # 3. 오늘 Stream 문제 체크
    stream_problem_path = f"problems/daily/stream_{today.isoformat()}.json"
    if not os.path.exists(stream_problem_path):
        logger.info(f"[STARTUP] Today's Stream problems missing, generating...")
        try:
            from problems.generator_stream import generate_stream_problems
            generate_stream_problems(today, pg)
            logger.info(f"[STARTUP] Stream problems generated: {stream_problem_path}")
        except Exception as e:
            logger.error(f"[STARTUP] Stream problem generation failed: {e}")
    else:
        logger.info(f"[STARTUP] Today's Stream problems exist: {stream_problem_path}")
    
    pg.close()
    duck.close()
    logger.info("[STARTUP] Initialization complete")


if __name__ == "__main__":
    run_scheduler()


