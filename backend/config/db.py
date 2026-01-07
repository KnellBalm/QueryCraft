# config/db.py
from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # 루트 .env 로딩

@dataclass
class PostgresEnv:
    """PostgreSQL 연결 설정 - 환경에 따라 자동 전환"""
    
    def dsn(self) -> str:
        env = os.getenv("ENV", "development")
        
        if env == "production":
            # 상용 환경: POSTGRES_DSN 직접 사용 (Supabase)
            dsn = os.getenv("POSTGRES_DSN", "")
            if not dsn:
                raise ValueError("POSTGRES_DSN is required in production environment")
            return dsn
        else:
            # 개발 환경: 개별 환경변수 조합
            return (
                f"host={os.getenv('PG_HOST', '')} "
                f"port={os.getenv('PG_PORT', '5432')} "
                f"user={os.getenv('PG_USER', 'postgres')} "
                f"password={os.getenv('PG_PASSWORD', '')} "
                f"dbname={os.getenv('PG_DB', 'postgres')}"
            )

def get_duckdb_path() -> str:
    return os.getenv("DUCKDB_PATH", "data/pa_lab.duckdb")
