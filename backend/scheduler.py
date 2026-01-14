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
import pytz

from backend.common.logging import get_logger
from backend.services.db_logger import db_log, LogCategory, LogLevel
from backend.common.date_utils import get_today_kst
from backend.services.database import postgres_connection

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
    cutoff_date = get_today_kst() - timedelta(days=RETENTION_DAYS)
    cutoff_month = (get_today_kst() - timedelta(days=90)).strftime("%Y-%m")
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
        
        # 3. 오래된 grading 테이블 삭제 (grading 스키마가 존재할 경우에만)
        with postgres_connection() as pg:
            schema_check = pg.fetch_df("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'grading'")
            if len(schema_check) > 0:
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
            else:
                logger.info("[CLEANUP] 'grading' schema not found, skipping grading table cleanup")
        
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


def update_job_status(job_id: str, job_name: str, status: str = "success", next_run: datetime = None):
    """DB에 스케줄러 작업 상태 기록"""
    try:
        with postgres_connection() as pg:
            pg.execute("""
                INSERT INTO public.scheduler_status (job_id, job_name, last_run_at, next_run_at, status, updated_at)
                VALUES (%s, %s, NOW(), %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    job_name = EXCLUDED.job_name,
                    last_run_at = EXCLUDED.last_run_at,
                    next_run_at = EXCLUDED.next_run_at,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """, [job_id, job_name, next_run, status])
    except Exception as e:
        logger.error(f"[SCHEDULER] Failed to update job status in DB: {e}")

def get_db_last_run_times():
    """DB에서 마지막 실행 시간들을 로드"""
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("SELECT job_id, last_run_at FROM public.scheduler_status")
            return {row["job_id"]: row["last_run_at"] for _, row in df.iterrows()}
    except Exception:
        return {}


def run_weekday_generation():
    """PA 전용 문제/데이터 생성 (KST 01:00, 월~금)"""
    import time as time_module
    start_time = time_module.time()
    today = get_today_kst()
    
    # 주말 스킵로직은 CronTrigger에서 처리되지만, 안전을 위해 유지
    if today.weekday() >= 5:
        return
    
    logger.info(f"[SCHEDULER] Starting PA generation for {today}")
    db_log(LogCategory.SCHEDULER, f"PA 생성 시작: {today}", LogLevel.INFO, "scheduler")
    
    problem_count = 0
    status = "success"
    error_message = None
    
    try:
        from backend.generator.data_generator_advanced import generate_data
        generate_data(modes=("pa",), incremental=False)
        
        from problems.generator import generate as gen_probs
        with postgres_connection() as pg:
            # 1. PA 문제 생성
            if not os.path.exists(f"problems/daily/{today}.json"):
                path_pa = gen_probs(today, pg, mode="pa")
                if path_pa:
                    import json
                    with open(path_pa, "r") as f:
                        pa_data = json.load(f)
                        pa_count = len(pa_data.get("problems", [])) if isinstance(pa_data, dict) else len(pa_data)
                else:
                    pa_count = 0
            else:
                import json
                with open(f"problems/daily/{today}.json", "r") as f:
                    pa_count = len(json.load(f))
            
            # 2. RCA 문제 생성
            if not os.path.exists(f"problems/daily/rca_{today}.json"):
                path_rca = gen_probs(today, pg, mode="rca")
                if path_rca:
                    import json
                    with open(path_rca, "r") as f:
                        rca_data = json.load(f)
                        rca_count = len(rca_data.get("problems", [])) if isinstance(rca_data, dict) else len(rca_data)
                else:
                    rca_count = 0
            else:
                import json
                with open(f"problems/daily/rca_{today}.json", "r") as f:
                    rca_count = len(json.load(f))
            
            # dataset_versions 기록
            duration_ms = int((time_module.time() - start_time) * 1000)
            # PA 기록
            pg.execute("""
                INSERT INTO public.dataset_versions 
                (generation_date, generation_type, data_type, problem_count, status, error_message, duration_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (today, 'scheduled', 'pa', pa_count, status, error_message, duration_ms))
            # RCA 기록
            pg.execute("""
                INSERT INTO public.dataset_versions 
                (generation_date, generation_type, data_type, problem_count, status, error_message, duration_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (today, 'scheduled', 'rca', rca_count, status, error_message, duration_ms))
            
        update_job_status("weekday_generation", "평일 문제/데이터 생성", "success")
        logger.info(f"[SCHEDULER] PA/RCA generation completed for {today}")
    except Exception as e:
        logger.error(f"[SCHEDULER] PA generation failed: {e}")
        update_job_status("weekday_generation", "평일 문제/데이터 생성", f"error: {str(e)}")

def get_scheduler_status():
    """스케줄러 상태 반환 (DB 연동)"""
    db_history = get_db_last_run_times()
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        job_id = job.id.replace("_generation", "_job") if "cleanup" not in job.id else job.id
        jobs.append({
            "id": job.id,
            "name": job.name or job.id,
            "next_run": next_run.isoformat() if next_run else None,
            "last_run": db_history.get(job_id).isoformat() if db_history.get(job_id) else None
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs
    }

def start_scheduler():
    """스케줄러 시작 (KST 기준)"""
    if scheduler.running:
        return

    scheduler.remove_all_jobs()
    tz = pytz.timezone('Asia/Seoul')
    
    scheduler.add_job(
        run_weekday_generation,
        CronTrigger(hour=1, minute=0, day_of_week='0-4', timezone=tz),
        id="weekday_generation",
        name="평일 문제/데이터 생성 (월~금 01:00)",
        replace_existing=True
    )
    
    scheduler.add_job(
        cleanup_old_data,
        CronTrigger(hour=4, minute=0, timezone=tz),
        id="cleanup_job",
        name="오래된 데이터 정리 (매일 04:00)",
        replace_existing=True
    )
    
    try:
        scheduler.start()
        logger.info("[SCHEDULER] BackgroundScheduler started (KST)")
    except Exception as e:
        logger.error(f"[SCHEDULER] Start failed: {e}")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
