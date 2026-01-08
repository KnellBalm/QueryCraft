
import os
import sys
from datetime import date
import json

# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

from backend.engine.postgres_engine import PostgresEngine
from backend.config.db import PostgresEnv
from backend.common.logging import get_logger

logger = get_logger(__name__)

def diagnose():
    try:
        dsn = PostgresEnv().dsn()
        pg = PostgresEngine(dsn)
        
        # 1. 전체 문제 수 확인
        count_res = pg.fetch_df("SELECT data_type, COUNT(*) as count FROM public.problems GROUP BY data_type").to_dict('records')
        print(f"--- Database Status ---")
        print(f"Total problems by type: {count_res}")
        
        # 2. 오늘 날짜 문제 확인
        today = date.today()
        today_df = pg.fetch_df(
            "SELECT id, title, problem_date, data_type, set_index FROM public.problems WHERE problem_date = %s", 
            [today]
        )
        today_res = today_df.to_dict('records')
        print(f"Problems for today ({today}): {len(today_res)}")
        for p in today_res:
            print(f"  - [{p['data_type']}] Set {p['set_index']}: {p['title']}")
            
        # 3. 가장 최근 문제 날짜 확인
        latest_res = pg.fetch_df("SELECT MAX(problem_date) as max_date FROM public.problems").to_dict('records')
        print(f"Latest problem date in DB: {latest_res[0]['max_date']}")
        
        # 4. 파일 시스템 확인 (호환성용)
        prob_dir = "problems/daily"
        if os.path.exists(prob_dir):
            files = [f for f in os.listdir(prob_dir) if f.endswith('.json')]
            print(f"Files in {prob_dir}: {len(files)}")
            print(f"Recent files: {sorted(files, reverse=True)[:5]}")
        else:
            print(f"Directory {prob_dir} does not exist")

    except Exception as e:
        import traceback
        print(f"ERROR during diagnosis: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
