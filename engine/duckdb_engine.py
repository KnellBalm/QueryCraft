# engine/duckdb_engine.py
from __future__ import annotations
import duckdb
from pathlib import Path
from datetime import datetime
from typing import Any, Iterable

INIT_SQL = """
CREATE TABLE IF NOT EXISTS daily_sessions (
    session_date DATE PRIMARY KEY,
    data_version TEXT,
    problem_set_id TEXT,
    generated_at TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    status TEXT
);

CREATE TABLE IF NOT EXISTS submissions (
    session_date DATE,
    problem_id TEXT,
    difficulty TEXT,
    submitted_at TIMESTAMP,

    is_correct BOOLEAN,

    error_category TEXT,  -- ENGINE_ERROR | LOGIC_ERROR
    error_type TEXT,
    error_message TEXT
);
"""

class DuckDBEngine:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(self.db_path))
        self._init_schema()

    def _init_schema(self):
        self.conn.execute(INIT_SQL)

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        if params is None:
            self.conn.execute(sql)
        else:
            self.conn.execute(sql, params)

    def fetchone(self, sql: str, params: Iterable[Any] | None = None) -> dict | None:
        cur = self.conn.execute(sql, params) if params is not None else self.conn.execute(sql)
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

    def fetchall(self, sql: str, params: Iterable[Any] | None = None) -> list[dict]:
        cur = self.conn.execute(sql, params) if params is not None else self.conn.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    def exists(self, table: str, **where) -> bool:
        if not where:
            r = self.fetchone(f"SELECT 1 FROM {table} LIMIT 1")
            return r is not None
        cond = " AND ".join([f"{k} = ?" for k in where.keys()])
        params = list(where.values())
        r = self.fetchone(f"SELECT 1 FROM {table} WHERE {cond} LIMIT 1", params)
        return r is not None

    def insert(self, table: str, row: dict) -> None:
        cols = list(row.keys())
        placeholders = ",".join(["?"] * len(cols))
        sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
        self.execute(sql, [row[c] for c in cols])

    def close(self):
        self.conn.close()
