# backend/services/sql_service.py
"""SQL 실행 서비스"""
import time
import re
from typing import Tuple, Optional, List, Dict, Any

from backend.services.database import postgres_connection


# 허용되지 않는 SQL 키워드
DANGEROUS_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", 
    "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
]


def is_safe_sql(sql: str) -> Tuple[bool, Optional[str]]:
    """SQL 안전성 검사"""
    clean = sql.strip().upper()
    
    for keyword in DANGEROUS_KEYWORDS:
        if clean.startswith(keyword):
            return False, f"{keyword} 문은 실행할 수 없습니다."
    
    # 세미콜론으로 구분된 다중 쿼리 방지
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    if len(statements) > 1:
        return False, "하나의 SELECT 문만 실행할 수 있습니다."
    
    return True, None


def execute_sql(
    sql: str,
    limit: int = 100
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[List[str]], Optional[str], float]:
    """
    SQL 실행
    
    Returns:
        (data, columns, error, execution_time_ms)
    """
    # 안전성 검사
    is_safe, error_msg = is_safe_sql(sql)
    if not is_safe:
        return None, None, error_msg, 0
    
    # 쿼리 정리
    query = sql.strip().rstrip(";")
    
    # LIMIT 자동 추가
    if "LIMIT" not in query.upper():
        query = f"{query} LIMIT {limit}"
    
    try:
        start = time.time()
        
        with postgres_connection() as pg:
            df = pg.fetch_df(query)
        
        elapsed = (time.time() - start) * 1000  # ms
        
        columns = list(df.columns)
        data = df.to_dict(orient="records")
        
        return data, columns, None, elapsed
    
    except Exception as e:
        return None, None, str(e), 0
