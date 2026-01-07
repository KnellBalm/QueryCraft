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
            # 상용 환경: POSTGRES_DSN 직접 사용 (Supabase)
            dsn = os.getenv("POSTGRES_DSN", "")
            if not dsn:
                raise ValueError("POSTGRES_DSN is required in production environment")
            
            # DSN 형식 검증
            if "postgresql://" in dsn:
                # URI 형식 검증: 최소한의 구성 요소 확인
                if "@" not in dsn:
                    raise ValueError("Malformed POSTGRES_DSN (URI): host separator '@' missing")
            else:
                # Keyword 형식 검증
                if "host=" not in dsn:
                    raise ValueError("Malformed POSTGRES_DSN: must be a URI (postgresql://) or contain 'host='")
                if re.search(r'host=.*[\[\]]', dsn) or ']@' in dsn or '[@' in dsn:
                    raise ValueError("Malformed POSTGRES_DSN (Keyword): contains invalid characters near host")
            
            return dsn
        else:
            # 개발 환경: 개별 환경변수 조합
            return (
                f"host={os.getenv('PG_HOST', '')} "
                f"port={os.getenv('PG_PORT', '5432')} "
                f"user={os.getenv('PG_USER', 'postgres')} "
                f"dbname={os.getenv('PG_DB', 'postgres')}"
            )
    
    def masked_dsn(self) -> str:
        """비밀번호가 마스킹된 DSN 반환 (로깅용)"""
        try:
            # dsn()을 호출하면 검증 예외로 인해 마스킹 로그를 못 찍을 수 있으므로 직접 환경변수 참조
            raw_dsn = (
                os.getenv("POSTGRES_DSN", "") if os.getenv("ENV") == "production" 
                else f"host={os.getenv('PG_HOST')} password={os.getenv('PG_PASSWORD')}"
            )
            
            if "postgresql://" in raw_dsn:
                # URI: postgresql://user:pass@host:port/db -> postgresql://user:****@host:port/db
                return re.sub(r'(://.*?:).*?(@)', r'\1****\2', raw_dsn)
            else:
                # Keyword: host=... password=... -> host=... password=****
                return re.sub(r'(password=).*?(\s|$)', r'\1****\2', raw_dsn)
        except:
            return "DSN_MASKING_FAILED"

def get_duckdb_path() -> str:
    return os.getenv("DUCKDB_PATH", "data/pa_lab.duckdb")

