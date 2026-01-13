# backend/services/database.py
"""데이터베이스 연결 서비스"""
from contextlib import contextmanager
from typing import Generator

from psycopg2.pool import ThreadedConnectionPool
import os

from backend.engine.postgres_engine import PostgresEngine
from backend.engine.duckdb_engine import DuckDBEngine
from backend.config.db import PostgresEnv, get_duckdb_path

# 글로벌 테이블 풀 (앱 시작 시 초기화)
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        env = PostgresEnv()
        # 최소 1개, 최대 20개 연결 유지 (프로덕션 환경 고려)
        _pool = ThreadedConnectionPool(1, 20, env.dsn())
    return _pool

def get_postgres() -> PostgresEngine:
    """PostgreSQL 연결 생성 (단일 연결용 - 가급적 사용 자제)"""
    env = PostgresEnv()
    return PostgresEngine(dsn=env.dsn())


def get_duckdb() -> DuckDBEngine:
    """DuckDB 연결 생성"""
    return DuckDBEngine(get_duckdb_path())


@contextmanager
def postgres_connection() -> Generator[PostgresEngine, None, None]:
    """PostgreSQL 연결 컨텍스트 매니저 (Connection Pool 사용)"""
    pool = get_pool()
    conn = pool.getconn()
    conn.autocommit = True
    try:
        pg = PostgresEngine(connection=conn)
        yield pg
    finally:
        pool.putconn(conn)


@contextmanager
def duckdb_connection() -> Generator[DuckDBEngine, None, None]:
    """DuckDB 연결 컨텍스트 매니저"""
    duck = get_duckdb()
    try:
        yield duck
    finally:
        duck.close()
