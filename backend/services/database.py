# backend/services/database.py
"""데이터베이스 연결 서비스"""
from contextlib import contextmanager
from typing import Generator

from backend.engine.postgres_engine import PostgresEngine
from backend.engine.duckdb_engine import DuckDBEngine
from backend.config.db import PostgresEnv, get_duckdb_path


def get_postgres() -> PostgresEngine:
    """PostgreSQL 연결 생성"""
    return PostgresEngine(PostgresEnv().dsn())


def get_duckdb() -> DuckDBEngine:
    """DuckDB 연결 생성"""
    return DuckDBEngine(get_duckdb_path())


@contextmanager
def postgres_connection() -> Generator[PostgresEngine, None, None]:
    """PostgreSQL 연결 컨텍스트 매니저"""
    pg = get_postgres()
    try:
        yield pg
    finally:
        pg.close()


@contextmanager
def duckdb_connection() -> Generator[DuckDBEngine, None, None]:
    """DuckDB 연결 컨텍스트 매니저"""
    duck = get_duckdb()
    try:
        yield duck
    finally:
        duck.close()
