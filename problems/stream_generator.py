# problems/stream_generator.py
from datetime import date
from pathlib import Path
import json

from engine.postgres_engine import PostgresEngine
from problems.stream_summary import build_stream_summary
from problems.prompt_stream import call_gemini
from common.logging import get_logger

logger = get_logger(__name__)

STREAM_DIR = Path("problems/stream_daily")
STREAM_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_KEYS = {
    "task_id",
    "domain",
    "difficulty",
    "context",
    "request",
    "constraints",
    "deliverables",
}

def generate_stream_tasks(today: date, pg: PostgresEngine) -> str:
    logger.info(f"start generating stream tasks for {today}")
    summary = build_stream_summary(pg)
    logger.debug(f"stream summary: {summary[:100]}...")

    prompt = build_prompt(summary)  # 위 1번에서 정의한 프롬프트 함수

    tasks = call_gemini(prompt)
    logger.info(f"generated {len(tasks)} tasks from Gemini")

    # 최소 스키마 검증
    for t in tasks:
        missing = REQUIRED_KEYS - t.keys()
        if missing:
            raise ValueError(f"업무 요청 스키마 누락: {missing}")

    path = STREAM_DIR / f"{today}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    logger.info(f"saved stream tasks to {path}")
    return str(path)
