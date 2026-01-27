# backend/generator/daily_challenge_writer.py
"""
Daily Challenge 파일 작성/읽기
scenario + problems를 YYYY-MM-DD.json 형식으로 통합 저장
"""
import json
import os
from datetime import date
from typing import Optional, Dict, List

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.scenario_generator import BusinessScenario, TableConfig
from generator.unified_problem_generator import generate_daily_problems
from backend.common.date_utils import get_today_kst


def clean_nan(obj):
    """NaN/Inf 값을 JSON 직렬화 가능한 None으로 변환"""
    import math
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj


# 파일 경로
PROBLEMS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "problems",
    "daily"
)


def serialize_scenario(scenario: BusinessScenario) -> dict:
    """BusinessScenario를 JSON 직렬화 가능한 dict로 변환"""
    return {
        "date": scenario.date,
        "company_name": scenario.company_name,
        "company_description": scenario.company_description,
        "product_type": scenario.product_type,
        "situation": scenario.situation,
        "stake": scenario.stake,
        "data_period": {
            "start": scenario.data_period[0],
            "end": scenario.data_period[1]
        },
        "table_configs": [
            {
                "schema_name": tbl.schema_name,
                "table_name": tbl.table_name,
                "full_name": tbl.full_name,
                "purpose": tbl.purpose,
                "row_count": tbl.row_count
            }
            for tbl in scenario.table_configs
        ],
        "data_story": scenario.data_story,
        "north_star": scenario.north_star,
        "key_metrics": scenario.key_metrics
    }


def save_daily_challenge(
    scenario: BusinessScenario,
    problems: List[dict],
    target_date: Optional[str] = None
) -> str:
    """
    Daily Challenge를 파일 및 DB로 저장
    """
    if target_date is None:
        target_date = scenario.date
    
    # 데이터 구조
    scenario_data = serialize_scenario(scenario)
    metadata = {
        "total_problems": len(problems),
        "pa_count": sum(1 for p in problems if p['problem_type'] == 'pa'),
        "stream_count": sum(1 for p in problems if p['problem_type'] == 'stream'),
        "difficulty_distribution": {
            "easy": sum(1 for p in problems if p['difficulty'] == 'easy'),
            "medium": sum(1 for p in problems if p['difficulty'] == 'medium'),
            "hard": sum(1 for p in problems if p['difficulty'] == 'hard'),
        },
    }
    filepath = os.path.join(PROBLEMS_DIR, f"{target_date}.json")
    daily_challenge = clean_nan({
        "version": "2.0",
        "scenario": scenario_data,
        "problems": problems,
        "metadata": metadata
    })
    
    # DB 저장 (PostgreSQL) - 정규화된 데이터 사용
    try:
        from backend.services.database import postgres_connection
        with postgres_connection() as pg:
            pg.execute("""
                INSERT INTO public.daily_challenges (
                    challenge_date, version, scenario_data, problems_data, metadata
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (challenge_date) DO UPDATE SET
                    version = EXCLUDED.version,
                    scenario_data = EXCLUDED.scenario_data,
                    problems_data = EXCLUDED.problems_data,
                    metadata = EXCLUDED.metadata,
                    created_at = NOW()
            """, (
                target_date, 
                "2.0", 
                json.dumps(daily_challenge["scenario"], ensure_ascii=False), 
                json.dumps(daily_challenge["problems"], ensure_ascii=False), 
                json.dumps(daily_challenge["metadata"], ensure_ascii=False)
            ))
            
            # 하위 호환성을 위해 개별 문제 저장 (public.problems 테이블)
            problems = daily_challenge.get("problems", [])
            for p in problems:
                p_type = p.get("problem_type", "pa")
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
                    target_date, 
                    p_type, 
                    p.get("set_index", 0), 
                    p.get("difficulty"), 
                    p.get("problem_id"), 
                    json.dumps(p, ensure_ascii=False),
                    p.get("answer_sql"),
                    json.dumps(p.get("expected_columns", []), ensure_ascii=False),
                    json.dumps({"hint": p.get("hint"), "expected_result": p.get("expected_result")}, ensure_ascii=False)
                ])
            
            print(f"✅ Daily Challenge and {len(problems)} problems saved to DB: {target_date}")
    except Exception as e:
        print(f"⚠️ Failed to save to DB: {e}")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(daily_challenge, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Daily Challenge saved to file: {filepath}")
    return filepath


def load_daily_challenge(target_date: str) -> Optional[dict]:
    """
    특정 날짜의 Daily Challenge 로드 (DB 우선, 없으면 파일)
    """
    # 1. DB 시도
    try:
        from backend.services.database import postgres_connection
        with postgres_connection() as pg:
            res = pg.fetch_one("""
                SELECT version, scenario_data, problems_data, metadata
                FROM public.daily_challenges
                WHERE challenge_date = %s
            """, (target_date,))
            
            if res:
                # v2.0 형식으로 조립 (Tuple이 아닌 Dict로 접근)
                challenge_data = {
                    "version": res.get("version", "2.0"),
                    "scenario": res.get("scenario_data"),
                    "problems": res.get("problems_data"),
                    "metadata": res.get("metadata")
                }
                # JSON 문자열 처리 (DB에 JSONB가 아닌 TEXT로 저장된 경우 대비)
                for key in ["scenario", "problems", "metadata"]:
                    if isinstance(challenge_data[key], str):
                        try:
                            challenge_data[key] = json.loads(challenge_data[key])
                        except: pass
                
                # v1.0->v2.0 보정
                if isinstance(challenge_data["problems"], list) and challenge_data["scenario"] is None:
                    first_item = challenge_data["problems"][0] if challenge_data["problems"] else {}
                    challenge_data["scenario"] = first_item.get("scenario", "Daily SQL Challenge")
                
                return challenge_data
    except Exception as e:
        print(f"⚠️ Failed to load from DB: {e}")

    # 2. 파일 시도
    filename = f"{target_date}.json"
    filepath = os.path.join(PROBLEMS_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # v1.0 (list) -> v2.0 (dict) 변환
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            data = {
                "version": "1.0",
                "scenario": first_item.get("scenario", "Daily SQL Challenge"),
                "problems": data,
                "metadata": {}
            }
        return data


def get_latest_challenge() -> Optional[dict]:
    """
    가장 최근 Daily Challenge 로드 (DB 우선, 없으면 파일)
    """
    # 1. DB 시도
    try:
        from backend.services.database import postgres_connection
        with postgres_connection() as pg:
            res = pg.fetch_one("""
                SELECT version, scenario_data, problems_data, metadata, challenge_date
                FROM public.daily_challenges
                ORDER BY challenge_date DESC
                LIMIT 1
            """)
            
            if res:
                # v2.0 형식으로 조립 (Dict)
                challenge_data = {
                    "version": res.get("version", "2.0"),
                    "scenario": res.get("scenario_data"),
                    "problems": res.get("problems_data"),
                    "metadata": res.get("metadata")
                }
                # JSON 문자열 처리
                for key in ["scenario", "problems", "metadata"]:
                    if isinstance(challenge_data[key], str):
                        try:
                            challenge_data[key] = json.loads(challenge_data[key])
                        except: pass
                
                return challenge_data
    except Exception as e:
        print(f"⚠️ Failed to load latest from DB: {e}")

    # 2. 파일 시도 (기존 로직)
    if not os.path.exists(PROBLEMS_DIR):
        return None
    files = [
        f for f in os.listdir(PROBLEMS_DIR)
        if f.endswith('.json') and f.count('-') == 2
    ]
    if not files:
        return None
    files.sort(reverse=True)
    filepath = os.path.join(PROBLEMS_DIR, files[0])
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # v1.0->v2.0 보정
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            data = {
                "version": "1.0",
                "scenario": first_item.get("scenario", "Daily SQL Challenge"),
                "problems": data,
                "metadata": {}
            }
        return data


def archive_old_format_files():
    """
    기존 포맷 파일들을 archive로 이동
    """
    archive_dir = os.path.join(
        os.path.dirname(PROBLEMS_DIR),
        "archive"
    )
    os.makedirs(archive_dir, exist_ok=True)
    
    if not os.path.exists(PROBLEMS_DIR):
        return
    
    archived_count = 0
    for filename in os.listdir(PROBLEMS_DIR):
        # 기존 포맷 파일 감지
        if ('_set' in filename or filename.startswith('stream_')) and filename.endswith('.json'):
            old_path = os.path.join(PROBLEMS_DIR, filename)
            new_path = os.path.join(archive_dir, filename)
            
            # 이동
            os.rename(old_path, new_path)
            archived_count += 1
            print(f"📦 Archived: {filename}")
    
    if archived_count > 0:
        print(f"✅ Archived {archived_count} old format files to problems/archive/")


# 전체 파이프라인
def generate_and_save_daily_challenge(target_date: Optional[str] = None) -> str:
    """
    Daily Challenge 생성 및 저장 (전체 파이프라인)
    """
    from generator.scenario_generator import generate_scenario
    
    if target_date is None:
        target_date = get_today_kst().isoformat()
    
    print(f"\n🎯 Generating Daily Challenge for {target_date}...")
    
    # 1. Scenario 생성
    scenario = generate_scenario(target_date)
    
    # 2. 문제 생성
    problems = generate_daily_problems(scenario)
    
    # 3. 파일 저장
    filepath = save_daily_challenge(scenario, problems, target_date)
    
    return filepath


if __name__ == "__main__":
    import sys
    
    # CLI: python daily_challenge_writer.py [YYYY-MM-DD]
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    
    # 기존 파일 아카이빙 (첫 실행 시)
    archive_old_format_files()
    
    # Daily Challenge 생성
    filepath = generate_and_save_daily_challenge(target_date)
    
    # 검증
    print("\n🔍 Verifying saved file...")
    loaded = load_daily_challenge(target_date or date.today().isoformat())
    if loaded:
        print(f"✅ Successfully loaded {len(loaded['problems'])} problems")
    else:
        print("❌ Failed to load file")
