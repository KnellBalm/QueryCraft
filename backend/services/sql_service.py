# backend/services/sql_service.py
"""SQL 실행 서비스"""
import time
import re
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any

from backend.services.database import postgres_connection


# 허용되는 SQL 키워드 (Allowlist 방식)
ALLOWED_KEYWORDS = ["SELECT", "WITH", "EXPLAIN"]


def is_safe_sql(sql: str) -> Tuple[bool, Optional[str]]:
    """SQL 안전성 검사 (Allowlist 방식)"""
    clean = sql.strip().upper()

    # 빈 쿼리 체크
    if not clean:
        return False, "SQL 쿼리가 비어있습니다."

    # 세미콜론으로 구분된 다중 쿼리 방지
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    if len(statements) > 1:
        return False, "하나의 쿼리만 실행할 수 있습니다."

    # Allowlist 검증: 허용된 키워드로만 시작해야 함
    is_allowed = False
    for keyword in ALLOWED_KEYWORDS:
        if clean.startswith(keyword):
            is_allowed = True
            break

    if not is_allowed:
        return False, f"SELECT, WITH, EXPLAIN 쿼리만 실행할 수 있습니다."

    # 추가 보안 검사: 위험한 함수 호출 차단
    dangerous_patterns = [
        r"pg_sleep",  # 시간 지연 공격
        r"copy\s+",   # 파일 읽기/쓰기
        r"lo_import", r"lo_export",  # Large Object 파일 작업
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, clean, re.IGNORECASE):
            return False, "보안상 허용되지 않는 함수가 포함되어 있습니다."

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
        return None, None, error_msg, 0.0
    
    # 쿼리 정리
    query = sql.strip().rstrip(";")
    
    # LIMIT 자동 추가
    if "LIMIT" not in query.upper():
        query = f"{query} LIMIT {limit}"
    
    try:
        start = time.time()
        
        with postgres_connection() as pg:
            df = pg.fetch_df(query)
        
        elapsed = round((time.time() - start) * 1000, 2)  # ms, 소수점 2자리
        
        # 중복 컬럼 처리: 고유 컬럼명 생성
        original_columns = list(df.columns)
        unique_columns = []
        seen = {}
        
        for col in original_columns:
            if col in seen:
                seen[col] += 1
                unique_columns.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                unique_columns.append(col)
        
        df.columns = unique_columns
        
        # NaN 값을 None으로 변환 (Pydantic/JSON 직렬화 안정성)
        data_df = df.where(pd.notnull(df), None)
        data = data_df.to_dict(orient="records")
        
        return data, unique_columns, None, elapsed
    
    except Exception as e:
        return None, None, str(e), 0.0
