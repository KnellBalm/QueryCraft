# config/db.py
from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # 루트 .env 로딩

@dataclass
class PostgresEnv:
    host: str = os.getenv("PG_HOST", "")
    port: int = int(os.getenv("PG_PORT", "25432"))
    user: str = os.getenv("PG_USER", "postgres")
    password: str = os.getenv("PG_PASSWORD", "")
    db: str = os.getenv("PG_DB", "postgres")

    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} "
            f"user={self.user} password={self.password} dbname={self.db}"
        )

def get_duckdb_path() -> str:
    return os.getenv("DUCKDB_PATH", "data/pa_lab.duckdb")
