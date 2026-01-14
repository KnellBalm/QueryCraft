# backend/services/grading_service.py
"""채점 서비스 - grading 스키마 테이블 비교 방식"""
import time
import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional
import pandas as pd

from backend.services.database import postgres_connection, duckdb_connection
from backend.schemas.submission import SubmitResponse
from backend.services.db_logger import db_log, LogCategory, LogLevel
from backend.common.date_utils import get_today_kst
from backend.services.problem_service import get_problem_by_id

GRADING_SCHEMA = "grading"

DIFFICULTY_XP = {
    'easy': 10,
    'medium': 25,
    'hard': 50
}


def get_difficulty_xp(difficulty: str) -> int:
    """난이도별 XP 반환"""
    return DIFFICULTY_XP.get(difficulty.lower(), 25)


def load_problem(problem_id: str, data_type: str) -> Optional[dict]:
    """문제 로드 - 모든 파일 검색 (오늘 날짜뿐만 아니라 과거 문제도)"""
    problems_dir = Path("problems/daily")
    
    # 모든 파일에서 검색
    if data_type == "stream":
        # 모든 stream 파일 검색 (최신 순)
        paths = sorted(problems_dir.glob("stream_*.json"), reverse=True)
    elif data_type == "rca":
        # 모든 RCA 파일 검색 (최신 순)
        paths = sorted(problems_dir.glob("rca_*.json"), reverse=True)
    else:
        # 모든 PA 파일 검색 (최신 순)
        all_files = sorted(problems_dir.glob("20??-??-??*.json"), reverse=True)
        paths = [f for f in all_files if not f.name.startswith("stream_")]
    
    for path in paths:
        try:
            problems = json.loads(path.read_text(encoding="utf-8"))
            for p in problems:
                if p.get("problem_id") == problem_id:
                    return p
        except Exception:
            continue
    
    return None


def compare_results(user_df: pd.DataFrame, expected_df: pd.DataFrame, sort_keys: list = None) -> tuple[bool, str]:
    """사용자 결과와 정답 결과 비교 (간소화된 로직)
    - 컬럼 수/이름 확인
    - 행 수 확인
    - 날짜 비교 시 날짜 부분만 비교 (시간 무시)
    """
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
    user_df = user_df.copy()
    expected_df = expected_df.copy()
    user_df.columns = [c.lower() for c in user_df.columns]
    expected_df.columns = [c.lower() for c in expected_df.columns]
    
    # 정렬
    sort_cols = [k.lower() for k in (sort_keys or [])] if sort_keys else list(user_df.columns)
    sort_cols = [c for c in sort_cols if c in user_df.columns]
    
    if sort_cols:
        user_df = user_df.sort_values(by=sort_cols).reset_index(drop=True)
        expected_df = expected_df.sort_values(by=sort_cols).reset_index(drop=True)
    else:
        user_df = user_df.reset_index(drop=True)
        expected_df = expected_df.reset_index(drop=True)
    
    # 동일 컬럼 순서로 정렬
    common_cols = sorted(user_df.columns)
    user_df = user_df[common_cols]
    expected_df = expected_df[common_cols]
    
    # 값 비교 (날짜 관대 처리 포함)
    for i in range(len(user_df)):
        for col in common_cols:
            u_val = user_df.iloc[i][col]
            e_val = expected_df.iloc[i][col]
            
            # None/NaN 비교
            u_is_null = pd.isna(u_val)
            e_is_null = pd.isna(e_val)
            if u_is_null and e_is_null:
                continue
            if u_is_null != e_is_null:
                return False, f"{i+1}번째 행 '{col}' 값 불일치: 제출={u_val}, 정답={e_val}"
            
            # 날짜/시간 비교 (DATE 부분만 비교하여 관대하게 처리)
            if _is_date_like(u_val) or _is_date_like(e_val):
                try:
                    u_date = _extract_date(u_val)
                    e_date = _extract_date(e_val)
                    if u_date == e_date:
                        continue
                    return False, f"{i+1}번째 행 '{col}' 날짜 불일치: 제출={u_date}, 정답={e_date}"
                except:
                    pass
            
            # 숫자 비교 (소수점 차이 허용)
            if isinstance(u_val, (int, float)) and isinstance(e_val, (int, float)):
                if abs(float(u_val) - float(e_val)) < 0.0001:
                    continue
                return False, f"{i+1}번째 행 '{col}' 값 불일치: 제출={u_val}, 정답={e_val}"
            
            # 문자열 비교 (strip 후)
            if str(u_val).strip() == str(e_val).strip():
                continue
            
            return False, f"{i+1}번째 행 '{col}' 값 불일치: 제출={u_val}, 정답={e_val}"
    
    return True, "정답입니다! 🎉"


def _is_date_like(val) -> bool:
    """값이 날짜/시간처럼 보이는지 확인"""
    if pd.isna(val):
        return False
    if isinstance(val, (datetime, pd.Timestamp)):
        return True
    if isinstance(val, date):
        return True
    if isinstance(val, str):
        # YYYY-MM-DD 또는 YYYY-MM-DD HH:MM:SS 형식
        return len(val) >= 10 and val[4:5] == '-' and val[7:8] == '-'
    return False


def _extract_date(val) -> date:
    """값에서 날짜 부분만 추출"""
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, pd.Timestamp):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        # YYYY-MM-DD 부분만 추출
        return date.fromisoformat(val[:10])
    raise ValueError(f"Cannot extract date from {val}")


def grade_submission(
    problem_id: str,
    sql: str,
    data_type: str = "pa",
    note: Optional[str] = None,
    user_id: Optional[str] = None
) -> SubmitResponse:
    """문제 제출 채점 - grading 스키마 테이블 비교 방식"""
    start = time.time()
    session_date = date.today().isoformat()
    
    try:
        # 1. 문제 로드 (DB 우선, 파일 폴백 - problem_service 활용)
        problem = get_problem_by_id(problem_id, data_type, user_id=user_id)
        if not problem:
            return SubmitResponse(
                is_correct=False,
                feedback="문제를 찾을 수 없습니다.",
                execution_time_ms=0,
                diff=None
            )
        
        sort_keys = problem.sort_keys or []
        expected_result = problem.expected_result
        
        # 2. 정답 데이터 가져오기
        with postgres_connection() as pg:
            # 사용자 SQL 실행
            user_df = pg.fetch_df(sql.strip().rstrip(";"))
            
            # JSON에서 expected_result 사용
            if expected_result and len(expected_result) > 0:
                expected_df = pd.DataFrame(expected_result)
            else:
                # [개선] JSON에 없으면 정답 SQL을 실시간으로 실행
                answer_sql = problem.answer_sql
                if answer_sql:
                    try:
                        expected_df = pg.fetch_df(answer_sql.strip().rstrip(";"))
                    except Exception as e:
                        return SubmitResponse(
                            is_correct=False,
                            feedback=f"정답 SQL 실행 오류: {str(e)}",
                            execution_time_ms=0,
                            diff=str(e)
                        )
                else:
                    # 기존 방식: grading 테이블에서 정답 로드
                    grading_table = f"{GRADING_SCHEMA}.expected_{problem_id}"
                    try:
                        expected_df = pg.fetch_df(f"SELECT * FROM {grading_table}")
                    except Exception as e:
                        return SubmitResponse(
                            is_correct=False,
                            feedback="정답 데이터를 찾을 수 없습니다. (JSON/SQL/DB 모두 부재)",
                            execution_time_ms=0,
                            diff=str(e)
                        )
        
        # 3. 결과 비교
        is_correct, feedback = compare_results(user_df, expected_df, sort_keys)
        today = get_today_kst()
        
        from backend.common.logging import get_logger
        logger = get_logger("grading_service")
        logger.info(f"Grading result for {user_id}: problem={problem_id}, is_correct={is_correct}")
    
    # 1. PostgreSQL에 제출 기록 저장 (PostgreSQL) - 로그인한 사용자만
        if user_id:
            save_submission_pg(
                session_date=session_date,
                problem_id=problem_id,
                data_type=data_type,
                sql_text=sql,
                is_correct=is_correct,
                feedback=feedback,
                user_id=user_id,
                difficulty=problem.difficulty if hasattr(problem, 'difficulty') else 'medium'
            )
        
        # 5. 정답 시 XP 지급 (난이도 기반)
        if is_correct and user_id:
            diff = problem.difficulty if hasattr(problem, 'difficulty') else 'medium'
            xp_value = get_difficulty_xp(diff)
            award_xp(user_id, xp_value)
            feedback += f" (+{xp_value} XP)"
        
        # 6. 로깅
        result_text = "정답" if is_correct else "오답"
        db_log(
            category=LogCategory.USER_ACTION,
            message=f"문제 제출: {problem_id} ({result_text})",
            level=LogLevel.INFO,
            source="grading_service",
            user_id=user_id
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
            feedback=feedback,
            user_id=user_id,
            difficulty='medium'  # Error case fallback
        )
        
        return SubmitResponse(
            is_correct=False,
            feedback=feedback,
            execution_time_ms=0,
            diff=str(e)
        )


def get_hint(problem_id: str, sql: str, data_type: str = "pa") -> str:
    """AI 힌트 요청 - 문제 전체 컨텍스트 전달"""
    try:
        from problems.gemini import grade_pa_submission
        
        # 문제 정보 로드하여 컨텍스트 강화
        problem = get_problem_by_id(problem_id, data_type)
        
        # 스키마 정보 문자열화
        schema_info = None
        if problem and problem.schema:
            schema_lines = []
            for table in problem.schema:
                cols = ", ".join([f"{c.name} ({c.type})" for c in table.columns])
                schema_lines.append(f"{table.name}: {cols}")
            schema_info = "\n".join(schema_lines)
        
        return grade_pa_submission(
            problem_id=problem_id,
            sql_text=sql,
            is_correct=False,
            diff=None,
            note="사용자가 도움을 요청했습니다. 틀린 부분을 친절하게 설명해주세요.",
            problem_question=problem.question if problem else None,
            table_schema=schema_info,
            answer_sql=problem.answer_sql if problem else None,
        )
    except Exception as e:
        return f"힌트 생성 실패: {str(e)}"


def save_submission_pg(
    session_date: str,
    problem_id: str,
    data_type: str,
    sql_text: str,
    is_correct: bool,
    feedback: str,
    user_id: str = None,
    difficulty: str = 'medium'
):
    """제출 기록 저장 (PostgreSQL)
    
    Note: submissions 테이블은 db_init.py에서 초기화됨
    """
    try:
        with postgres_connection() as pg:
            pg.execute("""
                INSERT INTO public.submissions (session_date, problem_id, data_type, sql_text, is_correct, feedback, user_id, difficulty)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (session_date, problem_id, data_type, sql_text, is_correct, feedback, user_id, difficulty))
    except Exception as e:
        from backend.common.logging import get_logger
        logger = get_logger("grading_service")
        logger.error(f"Failed to save submission to PG: {e}")


def award_xp(user_id: str, xp_amount: int):
    """XP 지급 및 레벨업 처리"""
    if not user_id or xp_amount <= 0:
        return
    
    try:
        with postgres_connection() as pg:
            # XP 추가 및 레벨 계산 (100 XP당 1레벨)
            pg.execute("""
                UPDATE public.users 
                SET xp = xp + %s,
                    level = ((xp + %s) / 100) + 1
                WHERE id = %s
            """, (xp_amount, xp_amount, user_id))
    except Exception as e:
        from backend.common.logging import get_logger
        logger = get_logger("grading_service")
        logger.error(f"Failed to award XP: {e}")
