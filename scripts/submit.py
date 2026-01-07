# scripts/submit.py
import json
from datetime import date, datetime
from backend.engine.postgres_engine import PostgresEngine
from backend.engine.duckdb_engine import DuckDBEngine
from backend.grader.grader import grade, EngineError, LogicError
from backend.config.db import PostgresEnv

def submit():
    today = date.today().isoformat()

    pg = PostgresEngine(PostgresEnv().dsn())
    duck = DuckDBEngine("data/pa_lab.duckdb")

    duck.execute("""
        UPDATE daily_sessions
        SET started_at=now(), status='STARTED'
        WHERE session_date=? AND started_at IS NULL
    """, [today])

    session = duck.fetchone(
        "SELECT problem_set_path FROM daily_sessions WHERE session_date=?",
        [today]
    )
    if session is None:
        print("오늘 세션이 없습니다.")
        return

    with open(session["problem_set_path"], encoding="utf-8") as f:
        problems = json.load(f)

    submitted = duck.fetchall(
        "SELECT problem_id FROM submissions WHERE session_date=?",
        [today]
    )
    submitted_ids = {r["problem_id"] for r in submitted}

    remaining = [p for p in problems if p["problem_id"] not in submitted_ids]
    if not remaining:
        print("오늘 문제를 모두 제출했습니다.")
        duck.execute("""
            UPDATE daily_sessions
            SET finished_at=now(), status='FINISHED'
            WHERE session_date=?
        """, [today])
        return

    target = remaining[0]

    try:
        grade(pg, target)
        duck.insert("submissions", {
            "session_date": today,
            "problem_id": target["problem_id"],
            "difficulty": target["difficulty"],
            "submitted_at": datetime.now(),
            "is_correct": True
        })
        print(f"✅ {target['problem_id']} 정답")

    except EngineError as e:
        duck.insert("submissions", {
            "session_date": today,
            "problem_id": target["problem_id"],
            "difficulty": target["difficulty"],
            "submitted_at": datetime.now(),
            "is_correct": False,
            "error_category": "ENGINE_ERROR",
            "error_type": e.error_type,
            "error_message": e.message
        })
        print(f"❌ SQL 실행 오류")

    except LogicError as e:
        duck.insert("submissions", {
            "session_date": today,
            "problem_id": target["problem_id"],
            "difficulty": target["difficulty"],
            "submitted_at": datetime.now(),
            "is_correct": False,
            "error_category": "LOGIC_ERROR",
            "error_type": e.error_type,
            "error_message": e.message
        })
        print(f"❌ 오답: {e.message}")

if __name__ == "__main__":
    submit()
