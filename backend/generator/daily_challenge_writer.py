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
        "created_at": date.today().isoformat()
    }
    
    # 1. DB 저장 (PostgreSQL)
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
            """, (target_date, "2.0", json.dumps(scenario_data), json.dumps(problems), json.dumps(metadata)))
            print(f"✅ Daily Challenge saved to DB: {target_date}")
    except Exception as e:
        print(f"⚠️ Failed to save to DB: {e}")

    # 2. 로컬 파일 저장 (백업/로컬 개발용)
    os.makedirs(PROBLEMS_DIR, exist_ok=True)
    filepath = os.path.join(PROBLEMS_DIR, f"{target_date}.json")
    daily_challenge = {
        "version": "2.0",
        "scenario": scenario_data,
        "problems": problems,
        "metadata": metadata
    }
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
                return {
                    "version": res[0],
                    "scenario": res[1],
                    "problems": res[2],
                    "metadata": res[3]
                }
    except Exception as e:
        print(f"⚠️ Failed to load from DB: {e}")

    # 2. 파일 시도
    filename = f"{target_date}.json"
    filepath = os.path.join(PROBLEMS_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


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
                return {
                    "version": res[0],
                    "scenario": res[1],
                    "problems": res[2],
                    "metadata": res[3]
                }
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
        return json.load(f)


def archive_old_format_files():
    """
    기존 포맷 파일들을 archive로 이동
    - YYYY-MM-DD_set0.json
    - YYYY-MM-DD_set1.json
    - stream_YYYY-MM-DD.json
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
    
    Args:
        target_date: YYYY-MM-DD (없으면 오늘)
    
    Returns:
        저장된 파일 경로
    """
    from generator.scenario_generator import generate_scenario
    
    if target_date is None:
        target_date = date.today().isoformat()
    
    print(f"\n🎯 Generating Daily Challenge for {target_date}...")
    
    # 1. Scenario 생성
    print("1️⃣ Generating business scenario...")
    scenario = generate_scenario(target_date)
    print(f"   ✓ Company: {scenario.company_name}")
    print(f"   ✓ Product Type: {scenario.product_type}")
    print(f"   ✓ Situation: {scenario.situation}")
    
    # 2. 문제 생성
    print("\n2️⃣ Generating problems...")
    problems = generate_daily_problems(scenario)
    print(f"   ✓ Generated {len(problems)} problems")
    print(f"   ✓ PA: {sum(1 for p in problems if p['problem_type'] == 'pa')}, Stream: {sum(1 for p in problems if p['problem_type'] == 'stream')}")
    
    # 3. 파일 저장
    print("\n3️⃣ Saving to file...")
    filepath = save_daily_challenge(scenario, problems, target_date)
    
    print(f"\n✅ Daily Challenge complete!")
    print(f"📁 File: {filepath}")
    
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
        print(f"   Scenario: {loaded['scenario']['situation']}")
    else:
        print("❌ Failed to load file")
