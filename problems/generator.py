# problems/generator.py
"""PA 문제 생성기 - 월별 JSON + 정답 통합"""
import json
from pathlib import Path
from datetime import date
from problems.templates import build_expected_sql
from problems.prompt import build_prompt
from backend.engine.postgres_engine import PostgresEngine
from backend.common.logging import get_logger

logger = get_logger(__name__)

PROBLEM_DIR = Path("problems/monthly")
PROBLEM_DIR.mkdir(parents=True, exist_ok=True)

# 기존 daily 폴더도 유지 (호환성)
Path("problems/daily").mkdir(parents=True, exist_ok=True)

NUM_PROBLEM_SETS = 2  # 하루에 생성할 문제 세트 수 (2세트 = 12문제)

REQUIRED_FIELDS = {
    "problem_id",
    "difficulty",
    "topic",
    "question",
    "expected_columns",
    "sort_keys",
}


def load_monthly_file(month_str: str) -> dict:
    """월별 JSON 파일 로드 (없으면 빈 구조 반환)"""
    path = PROBLEM_DIR / f"pa_{month_str}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"month": month_str, "problems": []}


def save_monthly_file(month_str: str, data: dict):
    """월별 JSON 파일 저장"""
    path = PROBLEM_DIR / f"pa_{month_str}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"saved monthly file to {path}")


def get_expected_result(pg: PostgresEngine, answer_sql: str, limit: int = 1000) -> list:
    """정답 SQL 실행하여 결과 데이터 반환"""
    try:
        # Remove SQL comments (single-line -- and multi-line /* */)
        import re
        # Remove multi-line comments /* ... */
        clean_sql = re.sub(r'/\*.*?\*/', '', answer_sql, flags=re.DOTALL)
        # Remove single-line comments --
        clean_sql = re.sub(r'--[^\n]*', '', clean_sql)
        # Remove extra whitespace and semicolons
        clean_sql = clean_sql.strip().rstrip(";")
        
        # LIMIT 추가하여 너무 큰 결과 방지
        limited_sql = f"SELECT * FROM ({clean_sql}) AS _result LIMIT {limit}"
        df = pg.fetch_df(limited_sql)

        
        # DataFrame을 리스트로 변환
        result = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                # JSON 직렬화 가능하도록 변환
                if hasattr(val, 'isoformat'):  # datetime, date
                    record[col] = val.isoformat()
                elif hasattr(val, 'item'):  # numpy types
                    record[col] = val.item()
                else:
                    record[col] = val
            result.append(record)
        
        return result
    except Exception as e:
        logger.error(f"Failed to get expected result: {e}")
        return []


def generate_single_set(today: date, pg: PostgresEngine, set_index: int, mode: str = "pa") -> list:
    """단일 문제 세트 생성 - 정답 데이터 포함"""
    logger.info(f"generating {mode.upper()} problems set {set_index} for {today}")
    problems = build_prompt(mode=mode)  # Gemini 호출
    logger.info(f"generated {len(problems)} problems from Gemini for set {set_index} (mode: {mode})")

    # 검증
    if len(problems) != 6:
        raise ValueError(f"문제는 반드시 6개여야 합니다. (세트 {set_index}, 모드 {mode})")

    # 난이도 정규화 및 검증
    diff_cnt = {"easy": 0, "medium": 0, "hard": 0}
    for p in problems:
        if not REQUIRED_FIELDS.issubset(p.keys()):
            raise ValueError(f"문제 스키마 누락: {p}")
        # advanced -> hard 정규화
        if p["difficulty"] == "advanced":
            p["difficulty"] = "hard"
        if p["difficulty"] not in diff_cnt:
            logger.warning(f"Unknown difficulty: {p['difficulty']}, treating as medium")
            p["difficulty"] = "medium"
        diff_cnt[p["difficulty"]] += 1
        
        # 문제 ID에 날짜 + 세트 인덱스 + 모드 포함
        original_id = p["problem_id"]
        p["problem_id"] = f"{today}_{original_id}_set{set_index}_{mode}"
        p["date"] = today.isoformat()
        p["set_index"] = set_index
        p["data_type"] = mode
        
        # XP 값 설정
        if "xp_value" not in p:
            if p["difficulty"] == "easy":
                p["xp_value"] = 3
            elif p["difficulty"] == "medium":
                p["xp_value"] = 5
            else:  # hard
                p["xp_value"] = 8
        
        # 정답 결과 데이터 생성
        answer_sql = p.get("answer_sql")
        if answer_sql:
            expected_result = get_expected_result(pg, answer_sql)
            p["expected_result"] = expected_result
            p["expected_row_count"] = len(expected_result)
            logger.info(f"generated expected_result for {p['problem_id']} with {len(expected_result)} rows")
        else:
            logger.warning(f"answer_sql missing for {p['problem_id']}")
            p["expected_result"] = []
            p["expected_row_count"] = 0

    return problems


def save_problems_to_db(pg: PostgresEngine, problems: list, today: date, data_type: str):
    """문제를 PostgreSQL DB에 저장"""
    logger.info(f"saving {len(problems)} problems to DB for {today}")
    
    for p in problems:
        try:
            # Table schema in db_init.py:
            # problem_date, data_type, set_index, difficulty, title, description, 
            # initial_sql, answer_sql, expected_columns, hints, schema_info
            
            # Problem schema fields to map:
            # problem_id, difficulty, topic, question, expected_columns, sort_keys, expected_result
            
            def clean_nan(obj):
                if isinstance(obj, float) and (obj != obj): # check for NaN
                    return None
                if isinstance(obj, dict):
                    return {k: clean_nan(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [clean_nan(v) for v in obj]
                return obj

            p_clean = clean_nan(p)
            
            pg.execute("""
                INSERT INTO public.problems (
                    problem_date, data_type, set_index, difficulty, title, 
                    description, answer_sql, expected_columns, hints
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (problem_date, data_type, set_index, title) 
                DO UPDATE SET 
                    difficulty = EXCLUDED.difficulty,
                    description = EXCLUDED.description,
                    answer_sql = EXCLUDED.answer_sql,
                    expected_columns = EXCLUDED.expected_columns,
                    hints = EXCLUDED.hints,
                    updated_at = NOW()
            """, [
                today, 
                data_type, 
                p_clean.get("set_index", 0), 
                p_clean.get("difficulty"), 
                p_clean.get("problem_id"), 
                json.dumps(p_clean, ensure_ascii=False),
                p_clean.get("answer_sql"),
                json.dumps(p_clean.get("expected_columns", []), ensure_ascii=False),
                json.dumps({"hint": p_clean.get("hint"), "expected_result": p_clean.get("expected_result")}, ensure_ascii=False)
            ])
        except Exception as e:
            logger.error(f"Failed to save problem {p.get('problem_id')} to DB: {e}")


def ensure_dir(path: Path):
    """디렉토리가 존재하는지 확인하고 없으면 생성"""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")


def generate(today: date, pg: PostgresEngine, mode: str = "pa") -> str:
    """
    문제 세트 생성 - 월별 JSON에 누적 + DB 저장 (통합 generator)

    Args:
        today: 생성 날짜
        pg: PostgreSQL Engine
        mode: "pa" (2세트=12문제) | "stream" (1세트=6문제) | "rca" (1세트=6문제)

    Returns:
        생성된 월별 파일 경로
    """
    # Cloud Run 환경 확인 (휘발성 파일 시스템 대응)
    is_cloud_run = os.environ.get("K_SERVICE") is not None
    
    # Mode별 세트 수 결정
    num_sets = 2 if mode == "pa" else 1

    logger.info(f"start generating {num_sets} {mode.upper()} problem set(s) for {today}")

    month_str = today.strftime("%Y-%m")
    path = PROBLEM_DIR / f"{mode}_{month_str}.json"
    ensure_dir(PROBLEM_DIR)

    monthly_data = {"month": month_str, "data_type": mode, "problems": []}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    monthly_data = json.loads(content)
        except Exception as e:
            logger.warning(f"Failed to load existing monthly file {path}: {e}")

    all_problems = []
    for set_idx in range(num_sets):
        try:
            problems = generate_single_set(today, pg, set_idx, mode=mode)
            if problems:
                all_problems.extend(problems)
        except Exception as e:
            logger.error(f"Failed to generate {mode} set {set_idx}: {e}")

    if not all_problems:
        logger.error(f"No problems generated for {mode} on {today}. AI might have failed.")
        return ""

    # 1. DB 저장 (Primary Source - 필수)
    try:
        save_problems_to_db(pg, all_problems, today, mode)
    except Exception as e:
        logger.error(f"CRITICAL: Failed to save problems to DB: {e}")
        # DB 저장이 실패하면 로직을 계속 진행하되 에러를 남김 (파일이라도 남기기 위해)

    # Cloud Run 환경이면 파일 저장은 옵션 (실패해도 중단하지 않음)
    def safe_save_json(target_path: Path, data: any):
        try:
            ensure_dir(target_path.parent)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully saved to {target_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to save file to {target_path}: {e}")
            return False

    # 2. 월별 파일에 추가
    monthly_data["problems"].extend(all_problems)
    safe_save_json(path, monthly_data)

    # 3. 기존 daily 폴더 호환
    daily_filename = f"{mode}_{today}.json" if mode != "pa" else f"{today}.json"
    daily_path = Path("problems/daily") / daily_filename
    safe_save_json(daily_path, all_problems)

    # 4. 세트별 파일 저장
    for set_idx in range(num_sets):
        set_problems = [p for p in all_problems if p.get("set_index") == set_idx]
        if set_problems:
            set_filename = f"{mode}_{today}_set{set_idx}.json" if mode != "pa" else f"{today}_set{set_idx}.json"
            set_path = Path("problems/daily") / set_filename
            safe_save_json(set_path, set_problems)

    logger.info(f"✅ Generated and saved {len(all_problems)} {mode} problems for {today}")
    return str(path)
