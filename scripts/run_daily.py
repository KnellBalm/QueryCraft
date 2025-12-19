# scripts/run_daily.py
from __future__ import annotations

from datetime import date, datetime, timedelta
import os

from dotenv import load_dotenv
load_dotenv()

from engine.postgres_engine import PostgresEngine
from engine.duckdb_engine import DuckDBEngine
from generator.data_generator_advanced import generate_data
from problems.generator import generate as gen_problems
from problems.stream_generator import generate_stream_problems
from problems.stream_generator import generate_stream_tasks

from config.db import PostgresEnv

from common.logging import get_logger
logger = get_logger(__name__)

# -------------------------------------------------
# 환경 변수
# -------------------------------------------------
STREAM_REFRESH_WEEKDAY = int(os.getenv("STREAM_REFRESH_WEEKDAY", "6")) # Monday = 0
# Stream 생성한 날에만
if weekday == STREAM_REFRESH_WEEKDAY:
    stream_problem_path = generate_stream_problems(today, pg)
    logger.info(f"[INFO] stream problems generated: {stream_problem_path}")

if weekday == STREAM_REFRESH_WEEKDAY:
    generate_stream_tasks(today, pg)


# -------------------------------------------------
# 메인
# -------------------------------------------------
def run_daily():
    today = date.today()
    weekday = today.weekday()

    pg = PostgresEngine(PostgresEnv().dsn())
    duck = DuckDBEngine("data/pa_lab.duckdb")

    # DuckDB 스키마 초기화
    duck.execute(open("sql/init_duckdb.sql").read())

    # ---------------------------------------------
    # 1. 전날 세션 자동 SKIPPED 처리
    # ---------------------------------------------
    duck.execute(
        """
        UPDATE daily_sessions
        SET status='SKIPPED', finished_at=now()
        WHERE session_date = ?
          AND status IN ('GENERATED','STARTED')
        """,
        [(today - timedelta(days=1)).isoformat()],
    )

    # ---------------------------------------------
    # 2. 오늘 세션 이미 있으면 종료
    # ---------------------------------------------
    if duck.exists("daily_sessions", session_date=today.isoformat()):
        logger.info("[INFO] today's session already exists")
        return

    # ---------------------------------------------
    # 3. PA 데이터는 매일 생성
    # ---------------------------------------------
    logger.info("[INFO] generating PA data (daily)")
    generate_data(modes=("pa",))

    # ---------------------------------------------
    # 4. Stream 데이터는 주 1회만 생성
    # ---------------------------------------------
    if weekday == STREAM_REFRESH_WEEKDAY:
        logger.info("[INFO] generating STREAM data (weekly)")
        generate_data(modes=("stream",))
    else:
        logger.info("[INFO] skipping STREAM generation today")

    # ---------------------------------------------
    # 5. 문제 + expected 테이블 생성 (PA 기준)
    # ---------------------------------------------
    problem_path = gen_problems(today, pg)

    # ---------------------------------------------
    # 6. 세션 기록
    # ---------------------------------------------
    duck.execute(
        """
        INSERT INTO daily_sessions
        (session_date, problem_set_path, generated_at, status)
        VALUES (?, ?, ?, 'GENERATED')
        """,
        [today.isoformat(), problem_path, datetime.now()],
    )

    logger.info("[DONE] daily pipeline completed")

if __name__ == "__main__":
    run_daily()
