
import os
import sys
import json
from datetime import date
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

from backend.engine.postgres_engine import PostgresEngine
from backend.config.db import PostgresEnv
from problems.generator import save_problems_to_db
from problems.generator_stream import save_problems_to_db as save_stream_to_db

def sync():
    try:
        dsn = PostgresEnv().dsn()
        pg = PostgresEngine(dsn)
        
        problem_dir = Path("problems/daily")
        if not problem_dir.exists():
            print("No problems/daily directory found.")
            return

        # 1. PA 문제 동기화
        pa_files = list(problem_dir.glob("*.json"))
        pa_files = [f for f in pa_files if not f.name.startswith("stream_") and "set" not in f.name]
        
        print(f"Found {len(pa_files)} daily PA files.")
        for f in pa_files:
            try:
                # 파일명에서 날짜 추출 (YYYY-MM-DD.json)
                date_str = f.stem
                target_date = date.fromisoformat(date_str)
                
                with open(f, "r", encoding="utf-8") as fp:
                    problems = json.load(fp)
                
                if problems:
                    print(f"Syncing {len(problems)} PA problems for {target_date}...")
                    save_problems_to_db(pg, problems, target_date, "pa")
            except Exception as e:
                print(f"Error syncing {f.name}: {e}")

        # 2. Stream 문제 동기화
        stream_files = list(problem_dir.glob("stream_*.json"))
        print(f"Found {len(stream_files)} daily Stream files.")
        for f in stream_files:
            try:
                # 파일명에서 날짜 추출 (stream_YYYY-MM-DD.json)
                date_str = f.stem.replace("stream_", "")
                target_date = date.fromisoformat(date_str)
                
                with open(f, "r", encoding="utf-8") as fp:
                    problems = json.load(fp)
                
                if problems:
                    print(f"Syncing {len(problems)} Stream problems for {target_date}...")
                    save_stream_to_db(pg, problems, target_date, "stream")
            except Exception as e:
                print(f"Error syncing {f.name}: {e}")

        print("Sync completed.")
        
    except Exception as e:
        print(f"Fatal error during sync: {e}")

if __name__ == "__main__":
    sync()
