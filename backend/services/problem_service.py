# backend/services/problem_service.py
"""문제 관련 서비스"""
import json
from pathlib import Path
from datetime import date
from typing import List, Optional, Dict, Any

from backend.schemas.problem import Problem, TableSchema, TableColumn
from backend.services.database import postgres_connection, duckdb_connection


PROBLEM_DIR = Path("problems/daily")
STREAM_PROBLEM_DIR = Path("problems/stream_daily")


def get_problems(
    data_type: str = "pa",
    target_date: Optional[date] = None
) -> List[Problem]:
    """문제 목록 조회"""
    if target_date is None:
        target_date = date.today()
    
    if data_type == "pa":
        path = PROBLEM_DIR / f"{target_date}.json"
    else:
        path = STREAM_PROBLEM_DIR / f"{target_date}.json"
    
    if not path.exists():
        return []
    
    with open(path, encoding="utf-8") as f:
        problems_data = json.load(f)
    
    # 완료 상태 조회
    completed_map = get_submission_status(target_date)
    
    problems = []
    for p in problems_data:
        problem = Problem(**p)
        if problem.problem_id in completed_map:
            problem.is_completed = True
            problem.is_correct = completed_map[problem.problem_id]
        else:
            problem.is_completed = False
        problems.append(problem)
    
    return problems


def get_problem_by_id(
    problem_id: str,
    data_type: str = "pa",
    target_date: Optional[date] = None
) -> Optional[Problem]:
    """문제 상세 조회"""
    problems = get_problems(data_type, target_date)
    for p in problems:
        if p.problem_id == problem_id:
            return p
    return None


def get_submission_status(target_date: date) -> Dict[str, bool]:
    """제출 상태 조회"""
    try:
        with duckdb_connection() as duck:
            rows = duck.fetchall(
                "SELECT problem_id, is_correct FROM pa_submissions WHERE session_date = ?",
                [target_date.isoformat()]
            )
        return {r["problem_id"]: r["is_correct"] for r in rows}
    except Exception:
        return {}


def get_table_schema(prefix: str = "pa_") -> List[TableSchema]:
    """테이블 스키마 조회"""
    tables = []
    
    try:
        with postgres_connection() as pg:
            # 테이블 목록
            table_df = pg.fetch_df(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '{prefix}%'
                ORDER BY table_name
            """)
            
            for _, row in table_df.iterrows():
                tbl_name = row["table_name"]
                
                # 컬럼 정보
                col_df = pg.fetch_df(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = '{tbl_name}' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                
                columns = [
                    TableColumn(
                        column_name=c["column_name"],
                        data_type=c["data_type"]
                    )
                    for _, c in col_df.iterrows()
                ]
                
                # 행 수
                try:
                    count_df = pg.fetch_df(f"SELECT COUNT(*) as cnt FROM {tbl_name}")
                    row_count = int(count_df.iloc[0]["cnt"])
                except:
                    row_count = None
                
                tables.append(TableSchema(
                    table_name=tbl_name,
                    columns=columns,
                    row_count=row_count
                ))
    except Exception:
        pass
    
    return tables
