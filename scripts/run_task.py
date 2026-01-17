# scripts/run_task.py
"""
QueryCraft 통합 Task 실행 도구
- 확장성을 위해 Registry 패턴 사용
- 문제 생성, 데이터 생성, DB 관리 등 모든 관리 작업을 하나의 인터페이스로 통합
"""
import argparse
import sys
import os
from datetime import date, datetime
from typing import Callable, Dict, Any, Optional

# 경로 추가
sys.path.append(os.getcwd())

from backend.common.logging import get_logger
from backend.engine.postgres_engine import PostgresEngine
from backend.config.db import PostgresEnv

logger = get_logger("run_task")

class TaskRegistry:
    def __init__(self):
        self._tasks: Dict[str, Callable] = {}
        self._descriptions: Dict[str, str] = {}

    def register(self, name: str, description: str):
        def decorator(func: Callable):
            self._tasks[name] = func
            self._descriptions[name] = description
            return func
        return decorator

    def get_task(self, name: str) -> Optional[Callable]:
        return self._tasks.get(name)

    def list_tasks(self):
        return self._descriptions

registry = TaskRegistry()

# ---------------------------------------------------------
# Tasks 정의
# ---------------------------------------------------------

@registry.register("gen-pa", "PA 문제 생성 (args: --date, --mode)")
def task_gen_pa(args):
    from problems.generator import generate
    target_date = date.fromisoformat(args.date) if args.date else date.today()
    pg = PostgresEngine(PostgresEnv().dsn())
    try:
        path = generate(target_date, pg, mode=args.mode or "pa")
        print(f"✅ PA 문제 생성 완료: {path}")
    finally:
        pg.close()

@registry.register("gen-stream", "Stream 문제 생성 (args: --date)")
def task_gen_stream(args):
    from problems.generator_stream import generate_stream_problems
    target_date = date.fromisoformat(args.date) if args.date else date.today()
    pg = PostgresEngine(PostgresEnv().dsn())
    try:
        path = generate_stream_problems(target_date, pg)
        print(f"✅ Stream 문제 생성 완료: {path}")
    finally:
        pg.close()

@registry.register("gen-data", "기초 데이터 생성 (args: --modes=pa,stream)")
def task_gen_data(args):
    from backend.generator.data_generator_advanced import generate_data
    modes = tuple(args.modes.split(",")) if args.modes else ("pa",)
    generate_data(modes=modes)
    print(f"✅ 데이터 생성 완료 (modes: {modes})")

@registry.register("db-init", "데이터베이스 스키마 초기화")
def task_db_init(args):
    from scripts.init_postgres import init_db
    init_db()
    print("✅ DB 초기화 완료")

@registry.register("verify", "전체 시스템 검증 (Build & Test)")
def task_verify(args):
    print("🔍 검증 시작...")
    # 실제로는 스킬 레벨에서 subprocess로 실행할 수도 있지만, 
    # 여기서는 안내 메시지만 출력하거나 핵심 테스트 로직 호출
    import subprocess
    
    print("\n1. Backend Tests...")
    res = subprocess.run(["pytest", "tests/test_grader.py", "-v"])
    
    print("\n2. Frontend Build Check...")
    # frontend 디렉토리 존재 확인
    if os.path.exists("frontend"):
        res_fe = subprocess.run(["npm", "run", "build"], cwd="frontend")
    
    print("\n✅ 검증 프로세스 종료")

@registry.register("ls-tables", "데이터베이스 테이블 목록 및 스키마 확인 (args: --table)")
def task_ls_tables(args):
    pg = PostgresEngine(PostgresEnv().dsn())
    try:
        if args.table:
            print(f"\n--- Columns in '{args.table}' ---")
            cols = pg.fetch_df("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, [args.table])
            print(cols)
        else:
            print("\n--- Public Tables ---")
            df = pg.fetch_df("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            print(df)
    finally:
        pg.close()

@registry.register("logs", "시스템 로그 확인 (args: --level, --limit)")
def task_logs(args):
    from backend.services.db_logger import get_logs
    import json
    level = args.mode or None  # --mode를 level로 전용 제안
    limit = int(args.limit) if hasattr(args, 'limit') and args.limit else 50
    
    print(f"\n--- Recent Logs (level={level}, limit={limit}) ---")
    logs = get_logs(level=level, limit=limit)
    for log in logs:
        if isinstance(log.get('created_at'), datetime):
            log['created_at'] = log['created_at'].isoformat()
        print(json.dumps(log, ensure_ascii=False))

@registry.register("check-user", "특정 사용자 상태 및 최근 제출 확인 (args: --email)")
def task_check_user(args):
    if not args.email:
        print("❌ --email 파라미터가 필요합니다.")
        return
        
    pg = PostgresEngine(PostgresEnv().dsn())
    try:
        user = pg.fetch_df("SELECT id, email, xp, level, is_admin FROM public.users WHERE email = %s", [args.email])
        if user.empty:
            print(f"❌ User {args.email} not found")
            return
            
        user_info = user.to_dict('records')[0]
        print(f"\n--- User Info: {args.email} ---")
        for k, v in user_info.items():
            print(f"  {k:10}: {v}")
            
        subs = pg.fetch_df("""
            SELECT id, problem_id, is_correct, submitted_at 
            FROM public.submissions 
            WHERE user_id = %s 
            ORDER BY submitted_at DESC 
            LIMIT 10
        """, [user_info['id']])
        print(f"\n--- Recent 10 Submissions ---")
        if subs.empty:
            print("  (기록 없음)")
        else:
            print(subs)
    finally:
        pg.close()

@registry.register("diagnose", "전체 시스템 문제 현황 진단")
def task_diagnose(args):
    pg = PostgresEngine(PostgresEnv().dsn())
    try:
        print("\n--- Database Status ---")
        count_res = pg.fetch_df("SELECT data_type, COUNT(*) as count FROM public.problems GROUP BY data_type")
        print(count_res)
        
        today = date.today()
        today_df = pg.fetch_df(
            "SELECT id, title, problem_date, data_type, set_index FROM public.problems WHERE problem_date = %s", 
            [today]
        )
        print(f"\n--- Problems for today ({today}): {len(today_df)} ---")
        for _, p in today_df.iterrows():
            print(f"  - [{p['data_type']}] Set {p['set_index']}: {p['title']}")
            
        latest = pg.fetch_df("SELECT MAX(problem_date) as max_date FROM public.problems")
        print(f"\nLatest problem date in DB: {latest.iloc[0]['max_date']}")
    finally:
        pg.close()

# ---------------------------------------------------------
# Main CLI
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="QueryCraft Task Runner")
    parser.add_argument("task", help="실행할 태스크 이름", choices=list(registry.list_tasks().keys()) + ["list"])
    parser.add_argument("--date", help="대상 날짜 (YYYY-MM-DD)")
    parser.add_argument("--mode", help="생성 모드 또는 로그 레벨 (pa, error 등)")
    parser.add_argument("--modes", help="데이터 생성 대상 (콤마로 구분)")
    parser.add_argument("--table", help="상세 정보를 확인할 테이블명")
    parser.add_argument("--email", help="대상 사용자 이메일")
    parser.add_argument("--limit", help="로그 출력 제한 (기본 50)", default="50")
    
    args = parser.parse_args()

    if args.task == "list":
        print("\nAvailable Tasks:")
        for name, desc in registry.list_tasks().items():
            print(f"  - {name:15}: {desc}")
        return

    task_func = registry.get_task(args.task)
    if not task_func:
        print(f"❌ 알 수 없는 태스크: {args.task}")
        sys.exit(1)

    print(f"🚀 태스크 실행: {args.task}...")
    try:
        task_func(args)
    except Exception as e:
        logger.error(f"❌ 태스크 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
