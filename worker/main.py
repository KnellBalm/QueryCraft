"""
QueryCraft Worker Job - Main Entry Point

Cloud Run Job으로 실행되어 데이터 및 문제 생성을 백그라운드에서 처리합니다.
API 서버와 독립적으로 실행되어 블로킹 문제가 없습니다.

Usage:
    python -m worker.main                    # 전체 생성 (데이터 + 문제)
    python -m worker.main --task=data        # 데이터만 생성
    python -m worker.main --task=problems    # 문제만 생성
    python -m worker.main --task=cleanup     # 정리 작업
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# 즉시 출력 확인을 위한 디버그 프린트
print("DEBUG: worker.main module loading...", flush=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("worker")


def get_today_kst():
    """한국 시간 기준 오늘 날짜"""
    from datetime import timezone, timedelta
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).date()


def generate_data(use_scenario=True, target_date=None):
    """데이터 생성 (Scenario 기반 또는 기존 방식)"""
    logger.info("=== 데이터 생성 시작 ===")
    
    if use_scenario:
        # 새로운 시나리오 기반 데이터 생성
        logger.info("Scenario 기반 통합 데이터 생성 사용")
        
        if target_date is None:
            target_date = get_today_kst()
        
        try:
            from backend.generator.scenario_generator import generate_scenario
            from backend.generator.scenario_data_generator import generate_scenario_data
            from backend.config import settings
            import psycopg2
            
            # 시나리오 생성
            scenario = generate_scenario(str(target_date))
            logger.info(f"시나리오 생성: {scenario.company_name} - {scenario.product_type}")
            
            # PostgreSQL 연결
            conn = psycopg2.connect(settings.POSTGRES_DSN)
            
            try:
                # 동적 테이블 생성 및 데이터 삽입
                generate_scenario_data(scenario, conn)
                logger.info(f"✅ Scenario 데이터 생성 완료")
                
                for tbl in scenario.table_configs:
                    logger.info(f"   - {tbl.full_name}: {tbl.row_count:,} rows")
                    
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Scenario 데이터 생성 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    else:
        # 기존 방식 (기본 PA/Stream 데이터)
        logger.info("기존 방식 데이터 생성 사용")
        try:
            from backend.generator.data_generator_advanced import generate_data as gen_data
            gen_data(modes=("pa",))
            logger.info("PA 데이터 생성 완료")
        except Exception as e:
            logger.error(f"PA 데이터 생성 실패: {e}")
            raise
        
        # Stream 데이터 생성 활성화
        try:
            gen_data(modes=("stream",))
            logger.info("Stream 데이터 생성 완료")
        except Exception as e:
            logger.error(f"Stream 데이터 생성 실패: {e}")
            # Stream 실패가 PA에 영향을 주지 않도록 함
            pass


def generate_problems(target_date=None):
    """Daily Challenge 생성 (통합: PA 3 + Stream 3)"""
    logger.info("=== Daily Challenge 생성 시작 ===")
    
    if target_date is None:
        target_date = get_today_kst()
    
    logger.info(f"대상 날짜: {target_date}")
    
    try:
        # 새로운 통합 Daily Challenge 생성
        from backend.generator.daily_challenge_writer import generate_and_save_daily_challenge
        
        # 시나리오 생성 + 문제 생성 + 파일 저장
        filepath = generate_and_save_daily_challenge(str(target_date))
        
        logger.info(f"✅ Daily Challenge 생성 완료: {filepath}")
        logger.info(f"   - 6문제 생성 (PA: 3, Stream: 3)")
        logger.info(f"   - 난이도: Easy 2, Medium 2, Hard 2")
        
        # 파일 검증
        from backend.generator.daily_challenge_writer import load_daily_challenge
        challenge = load_daily_challenge(str(target_date))
        
        if challenge:
            logger.info(f"   - Company: {challenge['scenario']['company_name']}")
            logger.info(f"   - Product Type: {challenge['scenario']['product_type']}")
            logger.info(f"   - Situation: {challenge['scenario']['situation'][:50]}...")
            
            for tbl in challenge['scenario']['table_configs']:
                logger.info(f"   - Table: {tbl['full_name']} ({tbl['row_count']:,} rows)")
        
    except Exception as e:
        logger.error(f"Daily Challenge 생성 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def cleanup_old_data():
    """오래된 데이터 정리 (30일 이상)"""
    logger.info("=== 정리 작업 시작 ===")
    
    try:
        from backend.services.database import postgres_connection
        from datetime import timedelta
        
        today = get_today_kst()
        cutoff = today - timedelta(days=30)
        
        with postgres_connection() as pg:
            # 오래된 제출 기록 삭제
            result = pg.execute("""
                DELETE FROM public.submissions 
                WHERE session_date < %s
            """, [cutoff])
            logger.info(f"삭제된 제출 기록: {result.rowcount if hasattr(result, 'rowcount') else 'unknown'}")
            
    except Exception as e:
        logger.error(f"정리 작업 실패: {e}")
        # 정리 작업 실패는 치명적이지 않음
        pass


def run_full_pipeline(target_date=None, use_scenario=True):
    """전체 파이프라인 실행 (데이터 → 문제 → 정리)"""
    logger.info("========================================")
    logger.info("QueryCraft Worker Job 시작")
    if target_date:
        logger.info(f"대상 날짜: {target_date}")
    logger.info(f"실행 시간: {datetime.now()}")
    logger.info(f"모드: {'Scenario 기반 (NEW)' if use_scenario else '기존 방식'}")
    logger.info("========================================")
    
    start_time = datetime.now()
    
    try:
        # 1. 데이터 생성 (Scenario 기반 동적 테이블)
        generate_data(use_scenario=use_scenario, target_date=target_date)
        
        # 2. 문제 생성 (Daily Challenge: PA 3 + Stream 3)
        generate_problems(target_date)
        
        # 3. 정리 작업
        cleanup_old_data()
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("========================================")
        logger.info(f"Worker Job 완료 (소요시간: {duration:.1f}초)")
        logger.info("========================================")
        
    except Exception as e:
        logger.error(f"Worker Job 실패: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="QueryCraft Worker Job")
    parser.add_argument(
        "--task",
        choices=["all", "data", "problems", "cleanup"],
        default="all",
        help="실행할 작업 (기본: all)"
    )
    parser.add_argument(
        "--date",
        help="대상 날짜 (YYYY-MM-DD, 기본: 오늘)"
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="기존 방식 사용 (기본: 새로운 Scenario 기반)"
    )
    args = parser.parse_args()
    
    print(f"DEBUG: main() started with args: {args}", flush=True)
    
    # 환경 변수 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    # 필수 환경 변수 체크
    required_vars = ["POSTGRES_DSN", "GEMINI_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.error(f"필수 환경 변수 누락: {missing}")
        sys.exit(1)
    
    target_date = None
    if args.date:
        from datetime import date
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            logger.error(f"잘못된 날짜 형식: {args.date} (YYYY-MM-DD 필요)")
            sys.exit(1)

    use_scenario = not args.legacy  # --legacy 없으면 새 방식 사용
    
    # 작업 실행
    if args.task == "all":
        run_full_pipeline(target_date, use_scenario=use_scenario)
    elif args.task == "data":
        generate_data(use_scenario=use_scenario, target_date=target_date)
    elif args.task == "problems":
        generate_problems(target_date)
    elif args.task == "cleanup":
        cleanup_old_data()


if __name__ == "__main__":
    main()
