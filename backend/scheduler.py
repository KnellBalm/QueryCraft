# backend/scheduler.py
"""백엔드 내장 스케줄러 - APScheduler 기반
- 월~금 새벽 1:00 (KST): PA 문제, Stream 문제, PA 데이터 생성
- 일요일 새벽 1:00 (KST): Stream 데이터 생성
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, timedelta, datetime
import os
import glob

from backend.common.logging import get_logger
from backend.services.db_logger import db_log, LogCategory, LogLevel

logger = get_logger(__name__)

scheduler = BackgroundScheduler()

# 보관 일수 (이전 문제 파일 및 정답 테이블)
RETENTION_DAYS = 30

# 마지막 실행 시간 기록
last_run_times = {
    "weekday_job": None,
    "sunday_job": None,
    "cleanup_job": None
}


def cleanup_old_data():
    """오래된 문제 파일과 정답 테이블 정리"""
    cutoff_date = date.today() - timedelta(days=RETENTION_DAYS)
    cutoff_month = (date.today() - timedelta(days=90)).strftime("%Y-%m")
    logger.info(f"[SCHEDULER] Cleaning up data older than {cutoff_date}")
    
    deleted_files = 0
    deleted_tables = 0
    
    try:
        # 1. 오래된 daily 문제 파일 삭제
        problem_files = glob.glob("problems/daily/*.json")
        for filepath in problem_files:
            filename = os.path.basename(filepath)
            try:
                if filename.startswith("stream_"):
                    date_str = filename[7:17]
                else:
                    date_str = filename[:10]
                
                file_date = date.fromisoformat(date_str)
                if file_date < cutoff_date:
                    os.remove(filepath)
                    deleted_files += 1
                    logger.info(f"[CLEANUP] Deleted old daily file: {filepath}")
            except (ValueError, IndexError):
                continue
        
        # 2. 오래된 monthly 파일 삭제 (3개월 이전)
        monthly_files = glob.glob("problems/monthly/*.json")
        for filepath in monthly_files:
            filename = os.path.basename(filepath)
            try:
                if filename.startswith("pa_"):
                    month_str = filename[3:10]
                elif filename.startswith("stream_"):
                    month_str = filename[7:14]
                else:
                    continue
                
                if month_str < cutoff_month:
                    os.remove(filepath)
                    deleted_files += 1
                    logger.info(f"[CLEANUP] Deleted old monthly file: {filepath}")
            except (ValueError, IndexError):
                continue
        
        # 3. 오래된 grading 테이블 삭제
        from backend.services.database import postgres_connection
        with postgres_connection() as pg:
            tables_df = pg.fetch_df("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'grading' AND table_name LIKE 'expected_%'
            """)
            
            for _, row in tables_df.iterrows():
                table_name = row["table_name"]
                try:
                    if len(table_name) > 19 and table_name[9:19].count("-") == 2:
                        date_str = table_name[9:19]
                        table_date = date.fromisoformat(date_str)
                        if table_date < cutoff_date:
                            pg.execute(f"DROP TABLE IF EXISTS grading.{table_name}")
                            deleted_tables += 1
                            logger.info(f"[CLEANUP] Dropped old grading table: {table_name}")
                except (ValueError, IndexError):
                    continue
        
        last_run_times["cleanup_job"] = datetime.now()
        
        if deleted_files > 0 or deleted_tables > 0:
            db_log(
                category=LogCategory.SCHEDULER,
                message=f"데이터 정리: {deleted_files}개 파일, {deleted_tables}개 테이블 삭제",
                level=LogLevel.INFO,
                source="scheduler"
            )
            logger.info(f"[CLEANUP] Deleted {deleted_files} files, {deleted_tables} tables")
        
    except Exception as e:
        logger.error(f"[CLEANUP] Error: {str(e)}")


def run_weekday_generation():
    """월~금 새벽 1:00 실행: PA 문제, Stream 문제, PA 데이터 생성"""
    today = date.today()
    weekday = today.weekday()  # 0=월, 6=일
    
    # 주말 체크 (혹시나)
    if weekday >= 5:  # 토(5), 일(6)
        logger.info(f"[SCHEDULER] Skipping weekday job on weekend: {today}")
        return
    
    logger.info(f"[SCHEDULER] Starting weekday generation for {today} (weekday={weekday})")
    
    db_log(
        category=LogCategory.SCHEDULER,
        message=f"평일 문제/데이터 생성 시작: {today}",
        level=LogLevel.INFO,
        source="scheduler"
    )
    
    try:
        from backend.engine.postgres_engine import PostgresEngine
        from backend.config.db import PostgresEnv
        
        pg = PostgresEngine(PostgresEnv().dsn())
        
        # 1. PA 문제 생성
        pa_problem_path = f"problems/daily/{today}.json"
        if not os.path.exists(pa_problem_path):
            logger.info("[SCHEDULER] Generating PA problems...")
            from problems.generator import generate as gen_pa_problems
            gen_pa_problems(today, pg)
            db_log(
                category=LogCategory.PROBLEM_GENERATION,
                message=f"PA 문제 생성 완료: {today}",
                level=LogLevel.INFO,
                source="scheduler"
            )
        else:
            logger.info(f"[SCHEDULER] PA problems already exist: {pa_problem_path}")
        
        # 2. Stream 문제 생성
        stream_problem_path = f"problems/daily/stream_{today}.json"
        if not os.path.exists(stream_problem_path):
            logger.info("[SCHEDULER] Generating Stream problems...")
            from problems.generator_stream import generate_stream_problems
            generate_stream_problems(today, pg)
            db_log(
                category=LogCategory.PROBLEM_GENERATION,
                message=f"Stream 문제 생성 완료: {today}",
                level=LogLevel.INFO,
                source="scheduler"
            )
        else:
            logger.info(f"[SCHEDULER] Stream problems already exist: {stream_problem_path}")
        
        # 3. PA 데이터 생성 (TODO: 실제 PA 데이터 생성 로직)
        logger.info("[SCHEDULER] PA data generation would run here (if implemented)")
        
        pg.close()
        
        last_run_times["weekday_job"] = datetime.now()
        
        db_log(
            category=LogCategory.SCHEDULER,
            message=f"평일 문제/데이터 생성 완료: {today}",
            level=LogLevel.INFO,
            source="scheduler"
        )
        logger.info(f"[SCHEDULER] Weekday generation completed for {today}")
        
    except Exception as e:
        error_msg = f"평일 생성 실패: {str(e)}"
        logger.error(f"[SCHEDULER] {error_msg}")
        db_log(
            category=LogCategory.SCHEDULER,
            message=error_msg,
            level=LogLevel.ERROR,
            source="scheduler"
        )


def run_sunday_generation():
    """일요일 새벽 1:00 실행: Stream 데이터 생성"""
    today = date.today()
    weekday = today.weekday()
    
    # 일요일(6) 체크
    if weekday != 6:
        logger.info(f"[SCHEDULER] Skipping sunday job on non-sunday: {today}")
        return
    
    logger.info(f"[SCHEDULER] Starting Sunday Stream data generation for {today}")
    
    db_log(
        category=LogCategory.SCHEDULER,
        message=f"일요일 Stream 데이터 생성 시작: {today}",
        level=LogLevel.INFO,
        source="scheduler"
    )
    
    try:
        # Stream 데이터 생성 (TODO: 실제 Stream 데이터 생성 로직)
        logger.info("[SCHEDULER] Stream data generation would run here (if implemented)")
        
        last_run_times["sunday_job"] = datetime.now()
        
        db_log(
            category=LogCategory.SCHEDULER,
            message=f"일요일 Stream 데이터 생성 완료: {today}",
            level=LogLevel.INFO,
            source="scheduler"
        )
        logger.info(f"[SCHEDULER] Sunday generation completed for {today}")
        
    except Exception as e:
        error_msg = f"일요일 생성 실패: {str(e)}"
        logger.error(f"[SCHEDULER] {error_msg}")
        db_log(
            category=LogCategory.SCHEDULER,
            message=error_msg,
            level=LogLevel.ERROR,
            source="scheduler"
        )


def get_scheduler_status():
    """스케줄러 상태 반환"""
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name or job.id,
            "next_run": next_run.isoformat() if next_run else None,
            "last_run": last_run_times.get(job.id.replace("_generation", "_job"), {})
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs,
        "last_run_times": {
            k: v.isoformat() if v else None 
            for k, v in last_run_times.items()
        }
    }


def start_scheduler():
    """스케줄러 시작
    - KST 1:00 = UTC 16:00 (전날)
    - 월~금: day_of_week='0-4' (APScheduler: 0=월)
    - 일요일: day_of_week='6'
    """
    
    # 1. 평일 작업: 월~금 KST 1:00 (= UTC 16:00 전날)
    # KST 월요일 1:00 = UTC 일요일 16:00, 따라서 UTC 기준으로는 일~목
    # APScheduler: 0=월, 6=일이므로 sun-thu = 6,0,1,2,3
    scheduler.add_job(
        run_weekday_generation,
        CronTrigger(hour=16, minute=0, day_of_week='6,0,1,2,3'),  # UTC 일~목 = KST 월~금
        id="weekday_generation",
        name="평일 문제/데이터 생성 (월~금 KST 1:00)",
        replace_existing=True
    )
    
    # 2. 일요일 작업: KST 1:00 (= UTC 토요일 16:00)
    scheduler.add_job(
        run_sunday_generation,
        CronTrigger(hour=16, minute=0, day_of_week='5'),  # UTC 토요일 = KST 일요일
        id="sunday_generation",
        name="일요일 Stream 데이터 생성 (일 KST 1:00)",
        replace_existing=True
    )
    
    # 3. 정리 작업: 매일 KST 4:00 (= UTC 19:00 전날)
    scheduler.add_job(
        cleanup_old_data,
        CronTrigger(hour=19, minute=0),
        id="cleanup_job",
        name="오래된 데이터 정리 (매일 KST 4:00)",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("[SCHEDULER] Started with new schedule:")
    logger.info("  - 평일 문제/데이터: 월~금 KST 1:00 (UTC 전날 16:00)")
    logger.info("  - 일요일 Stream: 일 KST 1:00 (UTC 토 16:00)")
    logger.info("  - 데이터 정리: 매일 KST 4:00 (UTC 전날 19:00)")
    
    db_log(
        category=LogCategory.SCHEDULER,
        message="스케줄러 시작됨 - 평일 KST 1:00, 일요일 KST 1:00",
        level=LogLevel.INFO,
        source="scheduler"
    )
    


def stop_scheduler():
    """스케줄러 중지"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[SCHEDULER] Stopped")
