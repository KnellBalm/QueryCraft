# engine/postgres_engine.py
from __future__ import annotations
import psycopg2
import psycopg2.extras
import pandas as pd
from typing import Iterable, Any

class PostgresEngine:
    def __init__(self, dsn: str):
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = True

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
        self.conn.close()
