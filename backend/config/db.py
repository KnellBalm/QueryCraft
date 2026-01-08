# config/db.py
from __future__ import annotations
import os
import re
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # 루트 .env 로딩

@dataclass
class PostgresEnv:
    """PostgreSQL 연결 설정 - 환경에 따라 자동 전환"""
    
    def dsn(self) -> str:
        env = os.getenv("ENV", "development")
        
        if env == "production":
            # 프로덕션: 반드시 POSTGRES_DSN 사용 (Supabase)
            dsn = os.getenv("POSTGRES_DSN", "").strip()
            if not dsn:
                raise ValueError("POSTGRES_DSN is required in production environment")
            if "@@" in dsn:
                dsn = dsn.replace("@@", "@")
            
            # Supabase 연결 안정성을 위해 sslmode=require 추가 (명시적으로 없는 경우)
            if "sslmode=" not in dsn:
                separator = "&" if "?" in dsn else "?"
                dsn += f"{separator}sslmode=require"
                
            return dsn
        else:
            # 개발 환경: 로컬 PostgreSQL 환경변수 사용
            return (
                f"host={os.getenv('PG_HOST', '').strip()} "
                f"port={os.getenv('PG_PORT', '5432').strip()} "
                f"user={os.getenv('PG_USER', 'postgres').strip()} "
                f"password={os.getenv('PG_PASSWORD', '').strip()} "
                f"dbname={os.getenv('PG_DB', 'postgres').strip()}"
            )
    
    def masked_dsn(self) -> str:
        """비밀번호가 마스킹된 DSN 반환 (로깅용)"""
        try:
            # dsn() 호출 시의 검증/변환 로직을 일관되게 적용하기 위해 dsn() 결과 사용
            # 단, dsn() 내부에서 예외가 날 수 있으므로 안전장치 마련
            raw_dsn = (
                os.getenv("POSTGRES_DSN", "") if os.getenv("ENV") == "production" 
                else f"host={os.getenv('PG_HOST')} password={os.getenv('PG_PASSWORD')}"
            )
            
            # @@ 치환 (로그에서도 동일하게 적용)
            if "@@" in raw_dsn:
                raw_dsn = raw_dsn.replace("@@", "@")
                
            if "postgresql://" in raw_dsn:
                return re.sub(r'(://.*?:).*?(@)', r'\1****\2', raw_dsn)
            else:
                return re.sub(r'(password=).*?(\s|$)', r'\1****\2', raw_dsn)
        except:
            return "DSN_MASKING_FAILED"

def get_duckdb_path() -> str:
    return os.getenv("DUCKDB_PATH", "data/pa_lab.duckdb")
