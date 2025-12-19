# problems/generator.py
import json
from pathlib import Path
from datetime import date
from problems.templates import build_expected_sql
from problems.prompt import build_prompt
from engine.postgres_engine import PostgresEngine
from common.logging import get_logger

logger = get_logger(__name__)

PROBLEM_DIR = Path("problems/daily")
PROBLEM_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_FIELDS = {
    "problem_id",
    "difficulty",
    "topic",
    "question",
    "expected_columns",
    "sort_keys",
}

def generate(today: date, pg: PostgresEngine) -> str:
    logger.info(f"start generating PA problems for {today}")
    problems = build_prompt()  # Gemini 호출
    logger.info(f"generated {len(problems)} problems from Gemini")

    # 검증
    if len(problems) != 6:
        raise ValueError("문제는 반드시 6개여야 합니다.")

    diff_cnt = {"easy": 0, "medium": 0, "advanced": 0}
    for p in problems:
        if not REQUIRED_FIELDS.issubset(p.keys()):
            raise ValueError(f"문제 스키마 누락: {p}")
        diff_cnt[p["difficulty"]] += 1

    if any(v != 2 for v in diff_cnt.values()):
        raise ValueError(f"난이도 분배 오류: {diff_cnt}")

    # expected 테이블 생성
    logger.info("creating expected tables in postgres")
    for p in problems:
        table = f"expected_{p['problem_id']}"
        sql = build_expected_sql(p)
        pg.execute(f"DROP TABLE IF EXISTS {table}")
        pg.execute(f"CREATE TABLE {table} AS {sql}")
    logger.info("expected tables created")

    path = PROBLEM_DIR / f"{today}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)

    logger.info(f"saved problems to {path}")
    return str(path)
