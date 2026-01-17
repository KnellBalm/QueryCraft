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
    Daily Challenge를 파일로 저장
    
    Args:
        scenario: BusinessScenario 객체
        problems: 문제 리스트
        target_date: YYYY-MM-DD (없으면 scenario.date 사용)
    
    Returns:
        저장된 파일 경로
    """
    if target_date is None:
        target_date = scenario.date
    
    # 디렉토리 생성
    os.makedirs(PROBLEMS_DIR, exist_ok=True)
    
    # 파일 경로
    filename = f"{target_date}.json"
    filepath = os.path.join(PROBLEMS_DIR, filename)
    
    # 데이터 구조
    daily_challenge = {
        "version": "2.0",  # 새 통합 버전
        "scenario": serialize_scenario(scenario),
        "problems": problems,
        "metadata": {
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
    }
    
    # JSON 저장 (pretty print)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(daily_challenge, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Daily Challenge saved: {filepath}")
    return filepath


def load_daily_challenge(target_date: str) -> Optional[dict]:
    """
    특정 날짜의 Daily Challenge 로드
    
    Args:
        target_date: YYYY-MM-DD
    
    Returns:
        Daily challenge dict or None
    """
    filename = f"{target_date}.json"
    filepath = os.path.join(PROBLEMS_DIR, filename)
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_latest_challenge() -> Optional[dict]:
    """
    가장 최근 Daily Challenge 로드
    
    Returns:
        Latest daily challenge dict or None
    """
    if not os.path.exists(PROBLEMS_DIR):
        return None
    
    # 모든 .json 파일 찾기
    files = [
        f for f in os.listdir(PROBLEMS_DIR)
        if f.endswith('.json') and f.count('-') == 2  # YYYY-MM-DD.json 형식
    ]
    
    if not files:
        return None
    
    # 날짜순 정렬 (최신순)
    files.sort(reverse=True)
    latest_file = files[0]
    
    filepath = os.path.join(PROBLEMS_DIR, latest_file)
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
