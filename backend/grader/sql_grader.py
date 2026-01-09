# backend/grader/sql_grader.py
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.services.database import postgres_connection
from backend.services.sql_service import execute_sql

class SQLGrader:
    """SQL 연습 문제 채점 엔진"""
    
    def execute_sql(self, sql: str, data_type: str = "pa") -> Dict[str, Any]:
        """SQL 실행 결과 반환"""
        data, columns, error, elapsed = execute_sql(sql)
        
        if error:
            return {
                "success": False,
                "error": error,
                "elapsed": elapsed
            }
        
        return {
            "success": True,
            "data": data,
            "columns": columns,
            "elapsed": elapsed
        }

    def compare_results(self, expected_data: List[Dict[str, Any]], user_data: List[Dict[str, Any]]) -> bool:
        """두 결과 데이터프레임 비교"""
        if not expected_data and not user_data:
            return True
        if not expected_data or not user_data:
            return False
            
        expected_df = pd.DataFrame(expected_data)
        user_df = pd.DataFrame(user_data)
        
        # 1. 컬럼 수 및 행 수 확인
        if len(expected_df.columns) != len(user_df.columns):
            return False
        if len(expected_df) != len(user_df):
            return False
            
        # 2. 컬럼명 정규화 (소문자)
        expected_df.columns = [c.lower() for c in expected_df.columns]
        user_df.columns = [c.lower() for c in user_df.columns]
        
        # 3. 데이터 정규화 및 정렬
        # 컬럼 순서 및 행 순서 불일치를 방지하기 위해 정렬 시도
        try:
            sort_cols = sorted(list(expected_df.columns))
            expected_df = expected_df[sort_cols].sort_values(by=sort_cols).reset_index(drop=True)
            user_df = user_df[sort_cols].sort_values(by=sort_cols).reset_index(drop=True)
        except:
            # 정렬 실패 시 (복합 타입 등) 기본 정렬 시도
            expected_df = expected_df.reset_index(drop=True)
            user_df = user_df.reset_index(drop=True)

        # 4. 값 비교 (날짜 및 숫자 정규화 포함)
        for col in expected_df.columns:
            # 날짜 정규화
            try:
                expected_df[col] = pd.to_datetime(expected_df[col], errors='ignore')
                user_df[col] = pd.to_datetime(user_df[col], errors='ignore')
                
                # Timestamp인 경우 tz 삭제 및 문자열 비교를 위해 정규화할 수도 있으나 .equals()가 대략 처리함
            except:
                pass

        # Pandas의 equals는 데이터 타입과 값을 모두 체크하므로 
        # API 응답 간의 비교(JSON 직렬화되었다가 돌아온 데이터)에서는 미세한 차이로 False가 날 수 있음
        # 따라서 값 자체를 반복문으로 체크하거나, astype(str)로 비교하는 전략 사용
        
        try:
            # 문자열 변환 비교 (가장 견고함)
            return expected_df.astype(str).equals(user_df.astype(str))
        except:
            return False
