# backend/services/problem_service.py
# [STABLE-FLOW] 이 파일은 핵심 문제 관리 로직을 포함하며 현재 안정 상태로 고정되었습니다. 수정 시 주의하십시오.
"""문제 관련 서비스"""
import json
import random
from pathlib import Path
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import os

from backend.schemas.problem import Problem, TableSchema, TableColumn
from backend.services.database import postgres_connection, duckdb_connection
from backend.common.date_utils import get_today_kst
from backend.common.logging import get_logger

logger = get_logger(__name__)

PROBLEM_DIR = Path("problems/daily")
NUM_PROBLEM_SETS = 2

def get_latest_problem_date(data_type: str = "pa") -> date:
    """DB 또는 파일에서 가장 최신의 문제 날짜를 탐색"""
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT MAX(problem_date) as max_date 
                FROM public.problems 
                WHERE data_type = %s 
                AND description IS NOT NULL
            """, [data_type])
            if not df.empty and df.iloc[0]["max_date"]:
                max_date = df.iloc[0]["max_date"]
                return date.fromisoformat(max_date) if isinstance(max_date, str) else max_date
    except Exception as e:
        logger.warning(f"Failed to get latest date from DB: {e}")

    # Fallback: 파일 시스템
    try:
        files = sorted(PROBLEM_DIR.glob(f"{data_type}_*.json" if data_type != "pa" else "*.json"), reverse=True)
        if files:
            # 파일명에서 날짜 추출 (예: 2024-01-30.json 또는 stream_2024-01-30.json)
            name = files[0].stem
            date_str = name.replace(f"{data_type}_", "") if data_type != "pa" else name
            if "_set" in date_str:
                date_str = date_str.split("_set")[0]
            return date.fromisoformat(date_str)
    except Exception:
        pass
        
    return get_today_kst()


def filter_problems_by_set(problems_raw: List[Any], user_id: Optional[str], target_date: date) -> List[Dict[str, Any]]:
    """사용자 세트에 맞는 문제만 필터링 및 프론트엔드용 필드 정규화"""
    if not problems_raw:
        return []
    
    # 1. Pydantic 모델인 경우 dict로 변환
    problems = []
    for p in problems_raw:
        if hasattr(p, "model_dump"):
            problems.append(p.model_dump())
        elif isinstance(p, dict):
            problems.append(p)
        else:
            problems.append(vars(p))

    # 2. 문제 데이터에 set_index가 있는지 확인 (v2.0+)
    has_set_index = any('set_index' in p for p in problems)
    
    # 3. 사용자 세트 인덱스 조회
    set_index = get_user_set_index(user_id, target_date, "pa")
    
    if not has_set_index:
        filtered = problems[:6]
    else:
        # 4. 필터링 (set_index 매칭)
        filtered = [p for p in problems if p.get('set_index') == set_index]
    
    # 만약 필터링 결과가 없으면 (예: 데이터 생성 오류) 전체 중 6개라도 반환
    if not filtered:
        logger.warning(f"No problems found for set_index {set_index}, falling back to any 6")
        filtered = problems[:6]
    
    # 5. 프론트엔드 호환성을 위한 필드 정규화
    final_problems = []
    for p in filtered:
        p_copy = p.copy()
        # frontend/src/pages/DailyChallenge.tsx는 problem_type을 기대함
        if 'problem_type' not in p_copy:
            p_copy['problem_type'] = p_copy.get('data_type', 'pa')
        # difficulty가 누락된 경우 기본값
        if 'difficulty' not in p_copy:
            p_copy['difficulty'] = 'medium'
        # table_names가 누락된 경우 빈 리스트
        if 'table_names' not in p_copy:
            p_copy['table_names'] = p_copy.get('table_names', [])
            
        final_problems.append(p_copy)

    return final_problems[:6]


def get_user_set_index(user_id: Optional[str], target_date: date, data_type: str) -> int:
    """사용자에게 할당된 문제 세트 인덱스 조회 (없으면 랜덤 할당)"""
    if not user_id:
        # 로그인 안 된 사용자는 set_0 사용
        return 0
    
    try:
        with postgres_connection() as pg:
            # 기존 할당 확인
            df = pg.fetch_df("""
                SELECT set_index FROM public.user_problem_sets 
                WHERE user_id = %s AND session_date = %s AND data_type = %s
            """, [user_id, target_date.isoformat(), data_type])
            
            if len(df) > 0:
                return int(df.iloc[0]["set_index"])
            
            # 새 할당 (랜덤)
            set_index = random.randint(0, NUM_PROBLEM_SETS - 1)
            pg.execute("""
                INSERT INTO public.user_problem_sets (user_id, session_date, data_type, set_index)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, session_date, data_type) DO NOTHING
            """, [user_id, target_date.isoformat(), data_type, set_index])
            
            return set_index
    except Exception:
        return 0


def get_problems(target_date: Optional[date] = None, data_type: str = "pa", user_id: Optional[str] = None) -> List[Problem]:
    """문제 목록 조회 (DB 우선, 파일 폴백)"""
    if target_date is None:
        target_date = get_today_kst()
    
    # 사용자 세트 인덱스 조회
    set_index = get_user_set_index(user_id, target_date, data_type)
    
    problems_data = []
    
    # 1. DB (problems 테이블) 조회 시도
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT description FROM public.problems 
                WHERE problem_date = %s AND data_type = %s AND set_index = %s
                ORDER BY id ASC
            """, [target_date.isoformat(), data_type, set_index])
            
            if len(df) > 0:
                for _, row in df.iterrows():
                    desc = row["description"]
                    if isinstance(desc, str):
                        problems_data.append(json.loads(desc))
                    else:
                        problems_data.append(desc)
            else:
                # 할당된 세트가 없으면 다른 세트라도 있는지 시도
                df_fallback = pg.fetch_df("""
                    SELECT description FROM public.problems 
                    WHERE problem_date = %s AND data_type = %s
                    LIMIT 6
                """, [target_date.isoformat(), data_type])
                
                if len(df_fallback) > 0:
                    logger.warning(f"Assigned set {set_index} empty, falling back to any available set for {target_date}")
                    for _, row in df_fallback.iterrows():
                        desc = row["description"]
                        if isinstance(desc, str):
                            problems_data.append(json.loads(desc))
                        else:
                            problems_data.append(desc)
                else:
                    # [PORTFOLIO-MODE] 오늘 날짜 데이터가 아예 없으면 가장 최근 날짜의 문제를 조회
                    logger.info(f"No problems found for {target_date}, searching for latest available problems")
                    df_latest = pg.fetch_df("""
                        SELECT description FROM public.problems 
                        WHERE data_type = %s
                        ORDER BY problem_date DESC, id ASC
                        LIMIT 6
                    """, [data_type])
                    
                    if len(df_latest) > 0:
                        for _, row in df_latest.iterrows():
                            desc = row["description"]
                            if isinstance(desc, str):
                                problems_data.append(json.loads(desc))
                            else:
                                problems_data.append(desc)
    except Exception as e:
        logger.debug(f"Failed to fetch problems from problems table: {e}")

    # 1.5. daily_challenges 테이블에서 조회 시도 (신규 통합 포맷)
    if not problems_data:
        try:
            from backend.generator.daily_challenge_writer import load_daily_challenge
            challenge = load_daily_challenge(target_date.isoformat())
            if challenge and "problems" in challenge:
                all_problems = challenge["problems"]
                # 세트 인덱스로 필터링
                problems_data = [p for p in all_problems if p.get("set_index") == set_index and p.get("problem_type") == data_type]
                # 만약 해당 세트가 없으면 타입만 맞는 것 중 일부라도 반환
                if not problems_data:
                    problems_data = [p for p in all_problems if p.get("problem_type") == data_type][:6]
        except Exception as e:
            logger.error(f"Failed to fetch from daily_challenges: {e}")

    # 2. DB에 없으면 파일에서 조회 (폴백)
    if not problems_data:
        path = None
        if data_type == "pa":
            path = PROBLEM_DIR / f"{target_date}_set{set_index}.json"
            if not path.exists():
                path = PROBLEM_DIR / f"{target_date}.json"
            
            if not path.exists():
                pa_files = sorted(PROBLEM_DIR.glob("*_set*.json"), reverse=True)
                if pa_files:
                    path = pa_files[0]
        elif data_type == "rca":
            path = PROBLEM_DIR / f"rca_{target_date}_set{set_index}.json"
            if not path.exists():
                path = PROBLEM_DIR / f"rca_{target_date}.json"
            
            if not path.exists():
                rca_files = sorted(PROBLEM_DIR.glob("rca_*_set*.json"), reverse=True)
                if rca_files:
                    path = rca_files[0]
                else:
                    rca_files = sorted(PROBLEM_DIR.glob("rca_*.json"), reverse=True)
                    if rca_files:
                        path = rca_files[0]
        else:
            path = PROBLEM_DIR / f"stream_{target_date}.json"
            if not path.exists():
                stream_files = sorted(PROBLEM_DIR.glob("stream_*.json"), reverse=True)
                if stream_files:
                    path = stream_files[0]
        
        if path and path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    all_data = json.load(f)
                    
                    # v2.0 통합 포맷인 경우 (dict {problems: [...]})
                    if isinstance(all_data, dict) and "problems" in all_data:
                        all_problems = all_data["problems"]
                    else:
                        all_problems = all_data
                    
                    problems_data = [p for p in all_problems if p.get("set_index", 0) == set_index and p.get("problem_type", "pa") == data_type]
                    if not problems_data:
                        problems_data = [p for p in all_problems if p.get("problem_type", "pa") == data_type][:6]
            except:
                pass
    
    if not problems_data:
        # [PORTFOLIO-MODE] 요청한 날짜에 데이터가 없으면 '최신 가용 날짜'로 다시 조회
        latest_date = get_latest_problem_date(data_type)
        if latest_date != target_date:
            logger.info(f"Retrying get_problems for {data_type} with latest date: {latest_date}")
            return get_problems(target_date=latest_date, data_type=data_type, user_id=user_id)
        return []
    
    # 완료 상태 조회 (실제 데이터가 있는 날짜 기준)
    completed_map = get_submission_status(target_date, user_id)
    
    problems = []
    for p in problems_data:
        try:
            problem = Problem(**p)
            if problem.problem_id in completed_map:
                problem.is_completed = True
                problem.is_correct = completed_map[problem.problem_id]
            else:
                problem.is_completed = False
            problems.append(problem)
        except Exception as e:
            logger.error(f"Error parsing problem data: {e}")
    
    return problems


def get_problem_by_id(
    problem_id: str,
    data_type: str = "pa",
    target_date: Optional[date] = None,
    user_id: Optional[str] = None
) -> Optional[Problem]:
    """문제 상세 조회 (DB 우선)"""
    # 1. DB에서 직접 id로 조회 시도 (가장 정확하고 빠름)
    try:
        with postgres_connection() as pg:
            # ID는 그 자체로 유니크하도록 설계되어 있으므로(YYYY-MM-DD-SET-NUM), 
            # 날짜나 data_type 필터 없이 ID로만 먼저 찾습니다.
            df = pg.fetch_df("""
                SELECT description, data_type, problem_date 
                FROM public.problems 
                WHERE (description::jsonb)->>'problem_id' = %s
                LIMIT 1
            """, [problem_id])
            
            if len(df) > 0:
                desc = df.iloc[0]["description"]
                db_data_type = df.iloc[0]["data_type"]
                db_date_str = df.iloc[0]["problem_date"]
                
                p_data = json.loads(desc) if isinstance(desc, str) else desc
                problem = Problem(**p_data)
                
                # 완료 상태 추가 (DB에 저장된 실제 날짜 사용)
                try:
                    status_date = date.fromisoformat(db_date_str) if isinstance(db_date_str, str) else db_date_str
                except:
                    status_date = target_date or get_today_kst()
                    
                completed_map = get_submission_status(status_date, user_id)
                if problem.problem_id in completed_map:
                    problem.is_completed = True
                    problem.is_correct = completed_map[problem.problem_id]
                else:
                    problem.is_completed = False
                return problem
    except Exception as e:
        logger.debug(f"Failed to fetch problem by id from problems table: {e}")

    # 1.5. daily_challenges 테이블에서 조회 시도 (신규 통합 포맷)
    try:
        from backend.generator.daily_challenge_writer import load_daily_challenge
        # target_date가 없으면 ID에서 추출 시도 (YYYY-MM-DD-...)
        extracted_date = target_date
        if extracted_date is None and "-" in problem_id:
            try:
                parts = problem_id.split("-")
                date_str = "-".join(parts[:3])
                extracted_date = date.fromisoformat(date_str)
            except:
                pass
        
        if extracted_date:
            challenge = load_daily_challenge(extracted_date.isoformat())
            if challenge and "problems" in challenge:
                for p in challenge["problems"]:
                    if p.get("problem_id") == problem_id:
                        # Validate problem_type matches data_type
                        problem_type = p.get("problem_type")
                        if problem_type != data_type:
                            logger.warning(
                                f"Problem {problem_id} found but type mismatch: "
                                f"expected {data_type}, got {problem_type}"
                            )
                            continue

                        problem = Problem(**p)
                        # 완료 상태 추가
                        completed_map = get_submission_status(extracted_date, user_id)
                        if problem.problem_id in completed_map:
                            problem.is_completed = True
                            problem.is_correct = completed_map[problem.problem_id]
                        else:
                            problem.is_completed = False
                        return problem
    except Exception as e:
        logger.error(f"Failed to fetch problem by id from daily_challenges: {e}")

    # 2. 없으면 전체 리스트에서 검색 (폴백)
    problems = get_problems(target_date, data_type, user_id)
    for p in problems:
        if p.problem_id == problem_id:
            return p
            
    # 3. 여전히 없으면 날짜 상관없이 모든 문제 검색 (404 방지)
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT description FROM public.problems
                WHERE (description::jsonb)->>'problem_id' = %s
                AND data_type = %s
                LIMIT 1
            """, [problem_id, data_type])

            if len(df) > 0:
                desc = df.iloc[0]["description"]
                p_data = json.loads(desc) if isinstance(desc, str) else desc
                return Problem(**p_data)
    except Exception as e:
        logger.error(f"Fallback fetch by id failed: {e}")

    return None


def get_submission_status(target_date: date, user_id: Optional[str] = None) -> Dict[str, bool]:
    """제출 상태 조회"""
    try:
        with postgres_connection() as pg:
            if user_id:
                df = pg.fetch_df("""
                    SELECT problem_id, is_correct FROM public.submissions
                    WHERE session_date = %s AND user_id = %s
                """, [target_date.isoformat(), user_id])
                return {row["problem_id"]: row["is_correct"] for _, row in df.iterrows()}
            else:
                # 게스트 사용자는 상태를 공유하지 않음
                return {}
    except Exception:
        return {}


def get_table_schema(prefix: str = "pa_") -> List[TableSchema]:
    """테이블 스키마 조회 - PostgreSQL(Supabase)로 단일화"""
    tables = []
    
    try:
        with postgres_connection() as pg:
            # 테이블 목록 (prefix에 상관없이 pa_와 stream_ 모두 조회가 필요할 수도 있지만, 현재는 prefix 필터 유지)
            # 사용자가 특정 모드(PA/Stream)로 진입했을 때 해당 테이블들만 보여주기 위함
            # prefix는 "pa_", "stream_", "rca_" 등 사전에 정의된 값만 허용 (보안)
            if prefix not in ("pa_", "stream_", "rca_"):
                prefix = "pa_"
                
            table_df = pg.fetch_df("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE %s
                ORDER BY table_name
            """, [f"{prefix}%"])
            
            for _, t_row in table_df.iterrows():
                tbl_name = t_row["table_name"]
                
                # 컬럼 정보
                col_df = pg.fetch_df("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, [tbl_name])
                
                columns = [
                    TableColumn(
                        column_name=c["column_name"],
                        data_type=c["data_type"]
                    )
                    for _, c in col_df.iterrows()
                ]
                
                # 행 수 (Supabase/PostgreSQL 속도 최적화를 위해 간단한 COUNT 사용)
                try:
                    # 테이블명은 매개변수화가 불가능하므로 사전에 조회된 테이블 이름만 사용하도록 보장됨 (t_row["table_name"])
                    count_df = pg.fetch_df(f"SELECT COUNT(*) as cnt FROM public.{tbl_name}")
                    row_count = int(count_df.iloc[0]["cnt"])
                except:
                    row_count = 0
                
                tables.append(TableSchema(
                    table_name=tbl_name,
                    columns=columns,
                    row_count=row_count
                ))
    except Exception as e:
        logger.error(f"Error fetching schema: {e}")
    
    return tables
