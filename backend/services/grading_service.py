# backend/services/grading_service.py
"""채점 서비스 - grading 스키마 테이블 비교 방식"""
import time
import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional
import pandas as pd

from backend.services.database import postgres_connection
from backend.schemas.submission import SubmitResponse

GRADING_SCHEMA = "grading"


def load_problem(problem_id: str, data_type: str) -> Optional[dict]:
    """문제 로드"""
    today = date.today().isoformat()
    if data_type == "stream":
        path = Path(f"problems/stream_daily/{today}.json")
    else:
        path = Path(f"problems/daily/{today}.json")
    
    if not path.exists():
        return None
    
    try:
        problems = json.loads(path.read_text(encoding="utf-8"))
        for p in problems:
            if p.get("problem_id") == problem_id:
                return p
        return None
    except Exception:
        return None


def compare_results(user_df: pd.DataFrame, expected_df: pd.DataFrame, sort_keys: list = None) -> tuple[bool, str]:
    """사용자 결과와 정답 결과 비교 (정렬 키 사용)"""
    # 컬럼 수 확인
    if len(user_df.columns) != len(expected_df.columns):
        return False, f"컬럼 수가 다릅니다. (제출: {len(user_df.columns)}, 정답: {len(expected_df.columns)})"
    
    # 행 수 확인
    if len(user_df) != len(expected_df):
        return False, f"행 수가 다릅니다. (제출: {len(user_df)}, 정답: {len(expected_df)})"
    
    # 컬럼명 확인 (순서 무관, 대소문자 무관)
    user_cols = set(c.lower() for c in user_df.columns)
    expected_cols = set(c.lower() for c in expected_df.columns)
    if user_cols != expected_cols:
        missing = expected_cols - user_cols
        extra = user_cols - expected_cols
        msg = "컬럼명이 다릅니다."
        if missing:
            msg += f" 누락: {missing}"
        if extra:
            msg += f" 추가: {extra}"
        return False, msg
    
    # 컬럼명 정규화 (소문자)
    user_df.columns = [c.lower() for c in user_df.columns]
    expected_df.columns = [c.lower() for c in expected_df.columns]
    
    # 정렬 후 비교
    try:
        # sort_keys가 있으면 사용, 없으면 모든 컬럼으로 정렬
        if sort_keys:
            sort_cols = [k.lower() for k in sort_keys if k.lower() in user_df.columns]
        else:
            sort_cols = list(user_df.columns)
        
        if sort_cols:
            user_sorted = user_df.sort_values(by=sort_cols).reset_index(drop=True)
            expected_sorted = expected_df.sort_values(by=sort_cols).reset_index(drop=True)
        else:
            user_sorted = user_df.reset_index(drop=True)
            expected_sorted = expected_df.reset_index(drop=True)
        
        # 같은 컬럼 순서로 정렬
        common_cols = sorted(user_sorted.columns)
        user_sorted = user_sorted[common_cols]
        expected_sorted = expected_sorted[common_cols]
        
        # 값 비교
        if user_sorted.equals(expected_sorted):
            return True, "정답입니다! 🎉"
        else:
            # 디버깅을 위해 첫 번째 차이점 찾기
            for i in range(min(len(user_sorted), len(expected_sorted))):
                for col in common_cols:
                    u_val = user_sorted.iloc[i][col]
                    e_val = expected_sorted.iloc[i][col]
                    if pd.isna(u_val) and pd.isna(e_val):
                        continue
                    if u_val != e_val:
                        return False, f"{i+1}번째 행 '{col}' 값 불일치: 제출={u_val}, 정답={e_val}"
            return False, "결과 값이 다릅니다."
    except Exception as e:
        return False, f"비교 오류: {str(e)}"


def grade_submission(
    problem_id: str,
    sql: str,
    data_type: str = "pa",
    note: Optional[str] = None
) -> SubmitResponse:
    """문제 제출 채점 - grading 스키마 테이블 비교 방식"""
    start = time.time()
    session_date = date.today().isoformat()
    
    try:
        # 1. 문제 로드
        problem = load_problem(problem_id, data_type)
        if not problem:
            return SubmitResponse(
                is_correct=False,
                feedback="문제를 찾을 수 없습니다.",
                execution_time_ms=0,
                diff=None
            )
        
        sort_keys = problem.get("sort_keys", [])
        expected_meta = problem.get("expected_meta", {})
        grading_table = expected_meta.get("grading_table")
        
        # 2. grading 테이블 존재 확인
        if not grading_table:
            grading_table = f"{GRADING_SCHEMA}.expected_{problem_id}"
        
        with postgres_connection() as pg:
            # 사용자 SQL 실행
            user_df = pg.fetch_df(sql.strip().rstrip(";"))
            
            # grading 테이블에서 정답 로드
            try:
                expected_df = pg.fetch_df(f"SELECT * FROM {grading_table}")
            except Exception as e:
                return SubmitResponse(
                    is_correct=False,
                    feedback=f"정답 테이블을 찾을 수 없습니다: {grading_table}",
                    execution_time_ms=0,
                    diff=str(e)
                )
        
        # 3. 결과 비교
        is_correct, feedback = compare_results(user_df, expected_df, sort_keys)
        
        # 4. 제출 기록 저장 (PostgreSQL)
        save_submission_pg(
            session_date=session_date,
            problem_id=problem_id,
            data_type=data_type,
            sql_text=sql,
            is_correct=is_correct,
            feedback=feedback
        )
        
        elapsed = (time.time() - start) * 1000
        
        return SubmitResponse(
            is_correct=is_correct,
            feedback=feedback,
            execution_time_ms=elapsed,
            diff=None
        )
    
    except Exception as e:
        feedback = f"SQL 실행 오류: {str(e)}"
        
        save_submission_pg(
            session_date=session_date,
            problem_id=problem_id,
            data_type=data_type,
            sql_text=sql,
            is_correct=False,
            feedback=feedback
        )
        
        return SubmitResponse(
            is_correct=False,
            feedback=feedback,
            execution_time_ms=0,
            diff=str(e)
        )


def get_hint(problem_id: str, sql: str, data_type: str = "pa") -> str:
    """AI 힌트 요청"""
    try:
        from problems.gemini import grade_pa_submission
        return grade_pa_submission(
            problem_id=problem_id,
            sql_text=sql,
            is_correct=False,
            diff=None,
            note="사용자가 도움을 요청했습니다. 틀린 부분을 친절하게 설명해주세요."
        )
    except Exception as e:
        return f"힌트 생성 실패: {str(e)}"


def save_submission_pg(
    session_date: str,
    problem_id: str,
    data_type: str,
    sql_text: str,
    is_correct: bool,
    feedback: str
):
    """제출 기록 저장 (PostgreSQL)"""
    try:
        with postgres_connection() as pg:
            # submissions 테이블 생성 (없으면)
            pg.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id SERIAL PRIMARY KEY,
                    session_date DATE NOT NULL,
                    problem_id VARCHAR(100) NOT NULL,
                    data_type VARCHAR(20) NOT NULL,
                    sql_text TEXT,
                    is_correct BOOLEAN,
                    feedback TEXT,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            pg.execute("""
                INSERT INTO submissions (session_date, problem_id, data_type, sql_text, is_correct, feedback)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session_date, problem_id, data_type, sql_text, is_correct, feedback))
    except Exception:
        pass

