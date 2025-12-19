# scripts/smoke_test_generator.py
from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

import psycopg2
from config.db import PostgresEnv
from generator.data_generator_advanced import generate_data

def main():
    # 1) PG 연결 테스트
    pg = PostgresEnv()
    con = psycopg2.connect(pg.dsn())
    con.autocommit = True
    cur = con.cursor()
    cur.execute("SELECT 1;")
    print("[OK] Postgres connection")

    # 2) generator 실행(환경값 기반)
    generate_data()

    # 3) 최소 검증
    cur.execute("SELECT COUNT(*) FROM stream_events;")
    se = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM pa_users;")
    pu = cur.fetchone()[0]
    print(f"[OK] stream_events={se}, pa_users={pu}")

    assert se > 0 or pu > 0, "생성된 데이터가 없습니다. env의 GENERATOR_MODES를 확인하세요."

    cur.close()
    con.close()
    print("[DONE] smoke test passed")

if __name__ == "__main__":
    main()
