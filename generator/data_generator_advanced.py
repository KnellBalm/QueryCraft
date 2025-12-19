# generator/data_generator_advanced.py
from __future__ import annotations

import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Callable

import duckdb
import psycopg2
import psycopg2.extras
from tqdm import tqdm
from dotenv import load_dotenv

from generator import config as cfg
from generator.utils import generate_session_id, generate_ts
from config.db import PostgresEnv, get_duckdb_path
from common.logging import get_logger

load_dotenv()
logger = get_logger(__name__)

# 타입 alias
StreamEventRow = Tuple[int, str, str, datetime, str, str]
StreamDailyRow = Tuple[str, float, int]
ProgressCallback = Callable[[int], None]

# ------------------------------------------------------------
# 공통: seed 처리
# ------------------------------------------------------------
def _apply_seed(base_dt: datetime):
    if cfg.GEN_SEED_MODE == "none":
        return
    if cfg.GEN_SEED_MODE == "fixed":
        random.seed(cfg.GEN_SEED_FIXED)
        return
    random.seed(base_dt.strftime("%Y%m%d"))

# ------------------------------------------------------------
# DB 연결
# ------------------------------------------------------------
def _connect_postgres():
    pg = PostgresEnv()
    con = psycopg2.connect(pg.dsn())
    con.autocommit = True
    return con

def _connect_duckdb():
    path = get_duckdb_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return duckdb.connect(path)

# ------------------------------------------------------------
# 스키마 초기화
# ------------------------------------------------------------
def init_postgres_schema(cur) -> None:
    logger.info("init postgres schema")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stream_events (
        user_id INT,
        session_id TEXT,
        event_name TEXT,
        event_time TIMESTAMP,
        device TEXT,
        channel TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stream_daily_metrics (
        date DATE,
        revenue DOUBLE PRECISION,
        purchases INT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dataset_versions (
      version_id BIGSERIAL PRIMARY KEY,
      created_at TIMESTAMP,
      generator_type TEXT,
      start_date DATE,
      end_date DATE,
      n_users BIGINT,
      n_events BIGINT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pa_users (
      user_id TEXT PRIMARY KEY,
      signup_at TIMESTAMP NOT NULL,
      country TEXT NOT NULL,
      channel TEXT NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pa_sessions (
      session_id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL REFERENCES pa_users(user_id),
      started_at TIMESTAMP NOT NULL,
      device TEXT NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pa_events (
      event_id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL REFERENCES pa_users(user_id),
      session_id TEXT NOT NULL REFERENCES pa_sessions(session_id),
      event_time TIMESTAMP NOT NULL,
      event_name TEXT NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pa_orders (
      order_id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL REFERENCES pa_users(user_id),
      order_time TIMESTAMP NOT NULL,
      amount INT NOT NULL
    );
    """)

def init_duckdb_schema(con: duckdb.DuckDBPyConnection) -> None:
    logger.info("init duckdb schema")

    con.execute("""
    CREATE TABLE IF NOT EXISTS stream_events (
        user_id INTEGER,
        session_id VARCHAR,
        event_name VARCHAR,
        event_time TIMESTAMP,
        device VARCHAR,
        channel VARCHAR
    );
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS stream_daily_metrics (
        date DATE,
        revenue DOUBLE,
        purchases INTEGER
    );
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS dataset_versions (
      version_id BIGINT,
      created_at TIMESTAMP,
      generator_type VARCHAR,
      start_date DATE,
      end_date DATE,
      n_users BIGINT,
      n_events BIGINT
    );
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS pa_users (
      user_id VARCHAR,
      signup_at TIMESTAMP,
      country VARCHAR,
      channel VARCHAR
    );
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS pa_sessions (
      session_id VARCHAR,
      user_id VARCHAR,
      started_at TIMESTAMP,
      device VARCHAR
    );
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS pa_events (
      event_id VARCHAR,
      user_id VARCHAR,
      session_id VARCHAR,
      event_time TIMESTAMP,
      event_name VARCHAR
    );
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS pa_orders (
      order_id VARCHAR,
      user_id VARCHAR,
      order_time TIMESTAMP,
      amount INTEGER
    );
    """)

def truncate_targets(pg_cur=None, duck_con=None, modes=("stream","pa")):
    logger.info("truncate targets: %s", modes)

    if pg_cur is not None:
        if "stream" in modes:
            pg_cur.execute("TRUNCATE stream_events, stream_daily_metrics;")
        if "pa" in modes:
            pg_cur.execute("TRUNCATE pa_orders, pa_events, pa_sessions, pa_users;")

    if duck_con is not None:
        if "stream" in modes:
            duck_con.execute("DELETE FROM stream_events;")
            duck_con.execute("DELETE FROM stream_daily_metrics;")
        if "pa" in modes:
            duck_con.execute("DELETE FROM pa_orders;")
            duck_con.execute("DELETE FROM pa_events;")
            duck_con.execute("DELETE FROM pa_sessions;")
            duck_con.execute("DELETE FROM pa_users;")

# ------------------------------------------------------------
# Stream 데이터 생성
# ------------------------------------------------------------
def generate_stream_users() -> Dict[int, Dict[str, object]]:
    users: Dict[int, Dict[str, object]] = {}
    cur_user_id = 1
    total_days = (cfg.STREAM_END_DATE - cfg.STREAM_START_DATE).days

    for d in range(total_days):
        day = cfg.STREAM_START_DATE + timedelta(days=d)
        new_users = random.randint(*cfg.STREAM_NEW_USERS_DAILY)

        for _ in range(new_users):
            users[cur_user_id] = {
                "signup_date": day,
                "device": random.choice(cfg.STREAM_DEVICES),
                "channel": random.choice(cfg.STREAM_CHANNELS),
            }
            cur_user_id += 1

        if cur_user_id > cfg.STREAM_N_USERS:
            break

    logger.info("stream users generated: %d", len(users))
    return users

def generate_stream_events(
    users: Dict[int, Dict[str, object]],
    progress_callback: Optional[ProgressCallback] = None,
):
    total_days = (cfg.STREAM_END_DATE - cfg.STREAM_START_DATE).days
    events_batch: List[StreamEventRow] = []
    daily_batch: List[StreamDailyRow] = []
    BATCH_THRESHOLD = 200_000

    user_ids = list(users.keys())

    for d in tqdm(range(total_days), desc="Generating stream events"):
        day = cfg.STREAM_START_DATE + timedelta(days=d)
        day_str = str(day)

        if progress_callback:
            progress_callback(int((d / total_days) * 100))

        if not user_ids:
            continue

        active_users = random.sample(user_ids, min(len(user_ids), random.randint(3000, 12000)))

        revenue_today = 0
        purchase_count = 0
        boost = cfg.STREAM_PROMOTION_BOOST if day in cfg.STREAM_PROMOTION_DAYS else 1.0

        for user in active_users:
            base = users[user]
            device = base["device"]
            channel = base["channel"]

            session_id = generate_session_id()
            events_batch.append((user, session_id, "visit", generate_ts(day_str), device, channel))

            if random.random() < cfg.STREAM_PROB_VIEW:
                events_batch.append((user, session_id, "view_product", generate_ts(day_str), device, channel))
            if random.random() < cfg.STREAM_PROB_CART:
                events_batch.append((user, session_id, "add_to_cart", generate_ts(day_str), device, channel))
            if random.random() < cfg.STREAM_PROB_CHECKOUT:
                events_batch.append((user, session_id, "checkout", generate_ts(day_str), device, channel))
            if random.random() < cfg.STREAM_PROB_PURCHASE * boost:
                revenue_today += random.randint(5, 200)
                purchase_count += 1
                events_batch.append((user, session_id, "purchase", generate_ts(day_str), device, channel))

        daily_batch.append((day_str, float(revenue_today), purchase_count))

        if len(events_batch) >= BATCH_THRESHOLD:
            yield events_batch, daily_batch
            events_batch, daily_batch = [], []

    if events_batch or daily_batch:
        yield events_batch, daily_batch

# ------------------------------------------------------------
# PA 데이터 생성
# ------------------------------------------------------------
def run_pa(save_to=("postgres","duckdb")):
    logger.info("start PA generator")
    base_dt = datetime.now()
    _apply_seed(base_dt)

    pg_con = pg_cur = None
    duck_con = None

    if "postgres" in save_to:
        pg_con = _connect_postgres()
        pg_cur = pg_con.cursor()
        init_postgres_schema(pg_cur)

    if "duckdb" in save_to:
        duck_con = _connect_duckdb()
        init_duckdb_schema(duck_con)

    truncate_targets(pg_cur=pg_cur, duck_con=duck_con, modes=("pa",))

    users = []
    for _ in tqdm(range(cfg.PA_NUM_USERS), desc="PA: generating users"):
        uid = str(uuid.uuid4())
        signup_at = base_dt - timedelta(days=random.randint(0, cfg.PA_SIGNUP_WINDOW_DAYS))
        users.append((uid, signup_at, random.choice(cfg.PA_COUNTRIES), random.choice(cfg.PA_CHANNELS)))

    sessions, events, orders = [], [], []

    for (user_id, signup_at, _, _) in tqdm(users, desc="PA: generating sessions/events"):
        for _ in range(random.randint(*cfg.PA_SESSIONS_PER_USER)):
            sid = str(uuid.uuid4())
            started_at = signup_at + timedelta(days=random.randint(0, 30), minutes=random.randint(0, 1440))
            sessions.append((sid, user_id, started_at, random.choice(cfg.PA_DEVICES)))

            purchase_time = None
            for _ in range(random.randint(*cfg.PA_EVENTS_PER_SESSION)):
                ev_time = started_at + timedelta(minutes=random.randint(0, 240))
                ev_name = random.choice(cfg.PA_EVENT_NAMES)
                events.append((str(uuid.uuid4()), user_id, sid, ev_time, ev_name))
                if ev_name == "purchase":
                    purchase_time = ev_time

            if purchase_time and random.random() < cfg.PA_ORDER_RATE_IF_PURCHASE:
                orders.append((str(uuid.uuid4()), user_id, purchase_time, random.randint(1000, 50000)))

    logger.info(
        "PA generated: users=%d sessions=%d events=%d orders=%d",
        len(users), len(sessions), len(events), len(orders)
    )

    if pg_cur:
        psycopg2.extras.execute_batch(pg_cur,
            "INSERT INTO pa_users VALUES (%s,%s,%s,%s)", users, page_size=5000)
        psycopg2.extras.execute_batch(pg_cur,
            "INSERT INTO pa_sessions VALUES (%s,%s,%s,%s)", sessions, page_size=5000)
        psycopg2.extras.execute_batch(pg_cur,
            "INSERT INTO pa_events VALUES (%s,%s,%s,%s,%s)", events, page_size=5000)
        if orders:
            psycopg2.extras.execute_batch(pg_cur,
                "INSERT INTO pa_orders VALUES (%s,%s,%s,%s)", orders, page_size=5000)

    if duck_con:
        duck_con.executemany("INSERT INTO pa_users VALUES (?, ?, ?, ?)", users)
        duck_con.executemany("INSERT INTO pa_sessions VALUES (?, ?, ?, ?)", sessions)
        duck_con.executemany("INSERT INTO pa_events VALUES (?, ?, ?, ?, ?)", events)
        if orders:
            duck_con.executemany("INSERT INTO pa_orders VALUES (?, ?, ?, ?)", orders)

    if duck_con: duck_con.close()
    if pg_cur: pg_cur.close()
    if pg_con: pg_con.close()

    logger.info("PA generator finished")

# ------------------------------------------------------------
# 엔트리포인트
# ------------------------------------------------------------
def generate_data(
    save_to: Sequence[str] = tuple(cfg.GENERATOR_TARGETS),
    modes: Sequence[str] = tuple(cfg.GENERATOR_MODES),
    progress_callback: Optional[ProgressCallback] = None,
):
    start = datetime.now()
    logger.info("generate_data start save_to=%s modes=%s", save_to, modes)

    if "stream" in modes:
        logger.info("running stream generator")
        run_stream(save_to=save_to, progress_callback=progress_callback)

    if "pa" in modes:
        logger.info("running pa generator")
        run_pa(save_to=save_to)

    elapsed = (datetime.now() - start).total_seconds()
    logger.info("data generation complete (%.1fs)", elapsed)

    if progress_callback:
        progress_callback(100)

if __name__ == "__main__":
    generate_data()
