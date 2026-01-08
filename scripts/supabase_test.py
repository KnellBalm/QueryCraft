#!/usr/bin/env python3
"""Supabase 연결 테스트 및 데이터 생성 스크립트"""
import os
import sys

# DSN 설정
os.environ["POSTGRES_DSN"] = "postgresql://postgres:querycraft1!@db.iropxqwnqojopemnnbks.supabase.co:5432/postgres?sslmode=require"

from backend.services.database import postgres_connection
from backend.common.logging import get_logger

logger = get_logger(__name__)

def test_connection():
    """연결 테스트"""
    print("=" * 50)
    print("Supabase 연결 테스트")
    print("=" * 50)
    
    try:
        with postgres_connection() as pg:
            # 테이블 목록 조회
            df = pg.fetch_df("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' ORDER BY table_name
            """)
            print(f"✅ 연결 성공! Public 테이블 {len(df)}개 발견")
            for t in df['table_name'].tolist():
                print(f"  - {t}")
            return True
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False

def generate_data():
    """PA/Stream 데이터 생성"""
    print("\n" + "=" * 50)
    print("데이터 생성 시작")
    print("=" * 50)
    
    try:
        from backend.generator.data_generator_advanced import generate_data as gen
        gen(modes=("pa", "stream"))
        print("✅ PA/Stream 데이터 생성 완료!")
        return True
    except Exception as e:
        print(f"❌ 데이터 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_problems():
    """문제 생성"""
    print("\n" + "=" * 50)
    print("문제 생성 시작")
    print("=" * 50)
    
    from datetime import date
    today = date.today()
    
    try:
        from problems.generator import generate as gen_pa
        with postgres_connection() as pg:
            path = gen_pa(today, pg)
        print(f"✅ PA 문제 생성 완료: {path}")
    except Exception as e:
        print(f"❌ PA 문제 생성 실패: {e}")
    
    try:
        from problems.generator_stream import generate_stream_problems
        with postgres_connection() as pg:
            path = generate_stream_problems(today, pg)
        print(f"✅ Stream 문제 생성 완료: {path}")
    except Exception as e:
        print(f"❌ Stream 문제 생성 실패: {e}")

if __name__ == "__main__":
    if not test_connection():
        sys.exit(1)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        generate_data()
        generate_problems()
    else:
        print("\n데이터 생성하려면: python3 scripts/supabase_test.py --generate")
