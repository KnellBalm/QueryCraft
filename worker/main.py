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


def generate_data():
    """PA 및 Stream 데이터 생성"""
    logger.info("=== 데이터 생성 시작 ===")
    
    try:
        from backend.generator.data_generator_advanced import generate_data as gen_data
        gen_data(modes=("pa",))
        logger.info("PA 데이터 생성 완료")
    except Exception as e:
        logger.error(f"PA 데이터 생성 실패: {e}")
        raise
    
    # Stream 데이터는 시간이 오래 걸려서 별도 처리
    # try:
    #     gen_data(modes=("stream",))
    #     logger.info("Stream 데이터 생성 완료")
    # except Exception as e:
    #     logger.error(f"Stream 데이터 생성 실패: {e}")


def generate_problems():
    """PA 문제 생성"""
    logger.info("=== 문제 생성 시작 ===")
    
    today = get_today_kst()
    
    try:
        # PostgreSQL 연결
        from backend.services.database import postgres_connection
        
        with postgres_connection() as pg:
            from problems.generator import generate as gen_pa
            gen_pa(today, pg)
            logger.info(f"PA 문제 생성 완료: {today}")
            
            # 생성된 문제 수 확인
            df = pg.fetch_df("""
                SELECT COUNT(*) as cnt FROM public.problems 
                WHERE problem_date = %s AND data_type = 'pa'
            """, [today])
            count = int(df.iloc[0]["cnt"]) if len(df) > 0 else 0
            logger.info(f"생성된 문제 수: {count}")
            
    except Exception as e:
        logger.error(f"문제 생성 실패: {e}")
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


def run_full_pipeline():
    """전체 파이프라인 실행 (데이터 → 문제 → 정리)"""
    logger.info("========================================")
    logger.info("QueryCraft Worker Job 시작")
    logger.info(f"실행 시간: {datetime.now()}")
    logger.info("========================================")
    
    start_time = datetime.now()
    
    try:
        # 1. 데이터 생성
        generate_data()
        
        # 2. 문제 생성
        generate_problems()
        
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
    args = parser.parse_args()
    
    # 환경 변수 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    # 필수 환경 변수 체크
    required_vars = ["POSTGRES_DSN", "GEMINI_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.error(f"필수 환경 변수 누락: {missing}")
        sys.exit(1)
    
    # 작업 실행
    if args.task == "all":
        run_full_pipeline()
    elif args.task == "data":
        generate_data()
    elif args.task == "problems":
        generate_problems()
    elif args.task == "cleanup":
        cleanup_old_data()


if __name__ == "__main__":
    main()
