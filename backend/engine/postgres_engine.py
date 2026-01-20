# engine/postgres_engine.py
from __future__ import annotations
import psycopg2
import psycopg2.extras
import pandas as pd
import warnings
from typing import Iterable, Any

# pandas-psycopg2 호환성 경고 무시
warnings.filterwarnings("ignore", category=UserWarning, message=".*pandas only supports SQLAlchemy connectable.*")

class PostgresEngine:
    def __init__(self, dsn: str | None = None, connection=None):
        if connection:
            self.conn = connection
            self.is_pooled = True
        elif dsn:
            self.conn = psycopg2.connect(dsn)
            self.conn.autocommit = True
            self.is_pooled = False
        else:
            raise ValueError("Either dsn or connection must be provided")
            
        # 세션 기본 스키마를 public으로 설정 (사용자 쿼리 편의성 및 안정성)
        with self.conn.cursor() as cur:
            cur.execute("SET search_path TO public")

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)

    def execute_many(self, sql: str, rows: list[tuple]) -> None:
        if not rows:
            return
        with self.conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, sql, rows, page_size=5000)

    def fetch_df(self, sql: str, params: Iterable[Any] | None = None) -> pd.DataFrame:
        return pd.read_sql_query(sql, self.conn, params=params)

    def table_exists(self, table: str) -> bool:
        q = """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema='public' AND table_name=%s
        """
        df = self.fetch_df(q, [table])
        return len(df) > 0

    def close(self):
        if not hasattr(self, 'is_pooled') or not self.is_pooled:
            self.conn.close()
