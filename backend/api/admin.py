# backend/api/admin.py
"""관리자 API"""
from datetime import date
from backend.common.date_utils import get_today_kst
import json
import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Query, BackgroundTasks

from backend.schemas.admin import (
    SystemStatus, SchedulerStatus, DatabaseTable, TodayProblemsStatus,
    GenerateProblemsRequest, GenerateProblemsResponse,
    RefreshDataRequest, RefreshDataResponse, ScheduleRunResponse,
    TriggerRCARequest
)
from backend.services.database import postgres_connection, duckdb_connection
from backend.api.auth import get_session
from backend.services.db_logger import get_logs, db_log, LogCategory, LogLevel


async def require_admin(request: Request):
    """관리자 권한 체크 (상세 로깅 포함)"""
    from backend.common.logging import get_logger
    logger = get_logger(__name__)
    
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.warning("Admin access denied: No session cookie")
        raise HTTPException(403, "로그인이 필요합니다 (세션 없음)")
    
    session = get_session(session_id)
    if not session:
        logger.warning(f"Admin access denied: Session not found (id={session_id[:8]}...)")
        raise HTTPException(403, "세션이 만료되었습니다. 다시 로그인해주세요")
    
    user_email = session.get("user", {}).get("email", "")
    if not user_email:
        logger.warning("Admin access denied: No email in session")
        raise HTTPException(403, "세션 정보가 올바르지 않습니다")
    
    # DB에서 is_admin 확인
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("SELECT is_admin FROM public.users WHERE email = %s", [user_email])
            if len(df) == 0:
                logger.warning(f"Admin access denied: User not found ({user_email})")
                raise HTTPException(403, "사용자 정보를 찾을 수 없습니다")
            if not df.iloc[0].get('is_admin', False):
                logger.warning(f"Admin access denied: Not admin ({user_email})")
                raise HTTPException(403, "관리자 권한이 없습니다")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin check DB error: {e}")
        raise HTTPException(500, f"권한 확인 중 오류 발생: {str(e)}")
    
    logger.info(f"Admin access granted: {user_email}")
    return session


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health-check")
async def health_check_with_auto_recovery(request: Request):
    """Health check with auto-recovery for missing problems.
    
    Cloud Scheduler should call this endpoint periodically (e.g., every hour).
    If today's problems are missing, it will trigger generation automatically.
    
    This ensures data availability even if the main daily scheduler fails.
    """
    from backend.common.logging import get_logger
    import time
    logger = get_logger(__name__)
    
    # API 키 검증 (Cloud Scheduler 또는 내부 호출)
    expected_key = os.environ.get("SCHEDULER_API_KEY", "")
    provided_key = request.headers.get("X-Scheduler-Key", "")
    
    # 키가 설정되어 있으면 검증, 아니면 건너뜀 (dev 환경 호환)
    if expected_key and provided_key != expected_key:
        logger.warning("[HEALTH] Invalid API key for health check")
        raise HTTPException(403, "Invalid API key")
    
    today = get_today_kst()
    result = {
        "status": "healthy",
        "date": str(today),
        "problems_exist": False,
        "auto_generated": False,
        "details": {}
    }
    
    try:
        with postgres_connection() as pg:
            # 오늘 날짜 문제 확인
            df = pg.fetch_df("""
                SELECT data_type, COUNT(*) as cnt 
                FROM public.problems 
                WHERE problem_date = %s 
                GROUP BY data_type
            """, [today])
            
            pa_count = 0
            for _, row in df.iterrows():
                if row.get("data_type") == "pa":
                    pa_count = int(row.get("cnt", 0))
                result["details"][row.get("data_type", "unknown")] = int(row.get("cnt", 0))
            
            if pa_count > 0:
                result["problems_exist"] = True
                logger.info(f"[HEALTH] Problems exist for {today}: {result['details']}")
                return result
            
            # 문제가 없으면 자동 생성 시도
            logger.warning(f"[HEALTH] No problems found for {today}, triggering auto-generation")
            db_log(LogCategory.SCHEDULER, f"Health check 자동 복구: {today} 문제 없음, 생성 시작", LogLevel.WARNING, "health_check")
            
            start_time = time.time()
            
            # 1. 데이터 생성
            try:
                from backend.generator.data_generator_advanced import generate_data
                generate_data(modes=("pa",))
                result["details"]["data_generated"] = True
            except Exception as e:
                logger.error(f"[HEALTH] Data generation failed: {e}")
                result["details"]["data_error"] = str(e)
            
            # 2. PA 문제 생성
            try:
                from problems.generator import generate as gen_pa
                gen_pa(today, pg)
                
                # 생성된 문제 수 확인
                new_df = pg.fetch_df("""
                    SELECT COUNT(*) as cnt FROM public.problems 
                    WHERE problem_date = %s AND data_type = 'pa'
                """, [today])
                new_count = int(new_df.iloc[0]["cnt"]) if len(new_df) > 0 else 0
                result["details"]["pa_generated"] = new_count
                result["auto_generated"] = new_count > 0
            except Exception as e:
                logger.error(f"[HEALTH] PA generation failed: {e}")
                result["details"]["pa_error"] = str(e)
            
            duration = time.time() - start_time
            result["details"]["duration_sec"] = round(duration, 2)
            
            if result["auto_generated"]:
                result["status"] = "recovered"
                db_log(LogCategory.SCHEDULER, f"Health check 자동 복구 성공: {result['details']}", LogLevel.INFO, "health_check")
            else:
                result["status"] = "degraded"
                db_log(LogCategory.SCHEDULER, f"Health check 자동 복구 실패: {result['details']}", LogLevel.ERROR, "health_check")
            
            return result
            
    except Exception as e:
        logger.error(f"[HEALTH] Health check failed: {e}")
        return {
            "status": "error",
            "date": str(today),
            "error": str(e)
        }


@router.get("/status", response_model=SystemStatus)
async def get_system_status(admin=Depends(require_admin)):
    """시스템 상태 조회"""
    from backend.common.logging import get_logger
    logger = get_logger(__name__)

    # PostgreSQL 연결 확인
    postgres_connected = False
    tables = []
    
    try:
        with postgres_connection() as pg:
            postgres_connected = True
            
            table_df = pg.fetch_df("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' ORDER BY table_name
            """)
            
            for _, row in table_df.iterrows():
                tbl = row["table_name"]
                try:
                    cnt = pg.fetch_df(f"SELECT COUNT(*) as cnt FROM public.{tbl}")
                    row_count = int(cnt.iloc[0]["cnt"])
                except:
                    row_count = 0
                
                col_cnt = pg.fetch_df(f"""
                    SELECT COUNT(*) as cnt FROM information_schema.columns
                    WHERE table_name = '{tbl}'
                """)
                
                tables.append(DatabaseTable(
                    table_name=tbl,
                    row_count=row_count,
                    column_count=int(col_cnt.iloc[0]["cnt"])
                ))
    except Exception as e:
        logger.error(f"Failed to fetch PostgreSQL table metadata: {e}")
    
    # DuckDB 연결 확인
    duckdb_connected = False
    scheduler_sessions = []
    
    try:
        with duckdb_connection() as duck:
            duckdb_connected = True
            
            rows = duck.fetchall("""
                SELECT session_date, status, generated_at, problem_set_path
                FROM daily_sessions
                ORDER BY session_date DESC
                LIMIT 7
            """)
            
            scheduler_sessions = [
                SchedulerStatus(
                    session_date=r["session_date"],
                    status=r.get("status", "N/A"),
                    generated_at=r.get("generated_at"),
                    problem_set_path=r.get("problem_set_path")
                )
                for r in rows
            ]
    except Exception as e:
        logger.error(f"Failed to fetch DuckDB scheduler sessions: {e}")
    
    # 오늘의 문제 현황 확인 (DB 기반 - Cloud Run 파일 시스템 휘발성 대응)
    today = get_today_kst()
    today_problems = None
    
    try:
        with postgres_connection() as pg:
            # problems 테이블에서 오늘 날짜 문제 조회
            df = pg.fetch_df("""
                SELECT problem_id, difficulty, data_type
                FROM public.problems
                WHERE session_date = %s
            """, [today])
            
            if len(df) > 0:
                difficulties = {}
                for _, row in df.iterrows():
                    diff = row.get("difficulty", "unknown")
                    difficulties[diff] = difficulties.get(diff, 0) + 1
                
                today_problems = TodayProblemsStatus(
                    exists=True,
                    count=len(df),
                    difficulties=difficulties,
                    path=f"DB: {today.isoformat()} ({len(df)} problems)"
                )
            else:
                today_problems = TodayProblemsStatus(exists=False)
    except Exception as e:
        from backend.common.logging import get_logger
        get_logger(__name__).error(f"Error checking today problems from DB: {e}")
        today_problems = TodayProblemsStatus(exists=False)
    
    return SystemStatus(
        postgres_connected=postgres_connected,
        duckdb_connected=duckdb_connected,
        tables=tables,
        scheduler_sessions=scheduler_sessions,
        today_problems=today_problems
    )



@router.post("/generate-problems", response_model=GenerateProblemsResponse)
async def generate_problems(request: GenerateProblemsRequest, admin=Depends(require_admin)):
    """문제 생성 (PA, Stream, RCA 통합 지원)"""
    today = get_today_kst()
    mode = request.data_type
    
    try:
        from problems.generator import generate as gen_problems
        
        with postgres_connection() as pg:
            # Rca는 추가 파라미터(product_type)가 필요할 수 있음
            if mode == "rca":
                # request에 product_type이 있으면 사용, 없으면 Commerce 기본
                p_type = getattr(request, 'product_type', 'commerce')
                path = gen_problems(today, pg, mode=mode, product_type=p_type)
            else:
                path = gen_problems(today, pg, mode=mode)
        
        if not path:
            return GenerateProblemsResponse(
                success=False,
                message=f"{mode.upper()} 문제 생성 실패 (AI 응답 없음)",
                path="",
                problem_count=0
            )

        # 생성된 문제 수 확인
        p_count = 0
        try:
            import json
            daily_filename = f"{mode}_{today}.json" if mode != "pa" else f"{today}.json"
            daily_path = os.path.join("problems/daily", daily_filename)
            if os.path.exists(daily_path):
                with open(daily_path, encoding="utf-8") as f:
                    data = json.load(f)
                    p_count = len(data)
        except:
            pass

        return GenerateProblemsResponse(
            success=True,
            message=f"{mode.upper()} 문제 생성 완료",
            path=path,
            problem_count=p_count
        )
    except Exception as e:
        return GenerateProblemsResponse(
            success=False,
            message=f"{mode.upper()} 문제 생성 오류: {str(e)}"
        )


def run_full_generation_task(today: date):
    """백그라운드에서 전체 생성을 수행하는 데몬 함수"""
    from backend.common.logging import get_logger
    import time
    logger = get_logger("backend.admin.generation")
    
    version_id = None
    start_time = time.time()
    
    try:
        logger.info(f"Start background full generation for {today}")
        
        # 0. 초기 상태 기록
        with postgres_connection() as pg:
            res = pg.fetch_df(f"""
                INSERT INTO public.dataset_versions 
                (generation_date, generation_type, status, created_at)
                VALUES ('{today}', 'full_unified', 'running', now())
                RETURNING version_id
            """)
            if not res.empty:
                version_id = int(res.iloc[0]['version_id'])
        
        results = []
        errors = []
        
        # 1. 통합 데이터 생성
        try:
            from backend.generator.data_generator_advanced import generate_data
            generate_data(modes=("pa", "stream"))
            results.append("✓ 통합 데이터 생성 완료 (PA + Stream)")
        except Exception as e:
            errors.append(f"✗ 데이터 생성 실패: {str(e)}")
        
        # 2. 통합 문제 생성 (PA + Stream)
        from problems.generator import generate as gen_problems
        p_count = 0
        with postgres_connection() as pg:
            for mode in ["pa", "stream"]:
                try:
                    path = gen_problems(today, pg, mode=mode)
                    if path:
                        results.append(f"✓ {mode.upper()} 문제 생성 완료: {path}")
                        # 문제 수 합산 (간이 방식)
                        try:
                            import json
                            with open(path, 'r') as f:
                                data = json.load(f)
                                p_count += len(data.get('problems', []))
                        except:
                            pass
                    else:
                        errors.append(f"✗ {mode.upper()} 문제 생성 실패 (결과 없음)")
                except Exception as e:
                    errors.append(f"✗ {mode.upper()} 문제 생성 오류: {str(e)}")
        
        # 3. 최종 상태 업데이트
        duration = int((time.time() - start_time) * 1000)
        status = 'completed' if not errors else 'failed'
        error_msg = "\n".join(errors) if errors else None
        
        if version_id:
            with postgres_connection() as pg:
                pg.execute(f"""
                    UPDATE public.dataset_versions
                    SET 
                        status = '{status}',
                        error_message = {f"'{error_msg}'" if error_msg else 'NULL'},
                        duration_ms = {duration},
                        problem_count = {p_count}
                    WHERE version_id = {version_id}
                """)
        
        if not errors:
            logger.info(f"Full generation finished successfully for {today}")
        else:
            logger.warning(f"Full generation finished with {len(errors)} errors: {errors}")
            
    except Exception as e:
        logger.critical(f"Unhandled error in generation task: {e}")
        if version_id:
            try:
                with postgres_connection() as pg:
                    pg.execute(f"UPDATE public.dataset_versions SET status = 'failed', error_message = '{str(e)}' WHERE version_id = {version_id}")
            except:
                pass


@router.post("/trigger-now")
async def trigger_generation_now(
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin)
):
    """즉시 통합 생성 실행 (데이터 + PA + Stream 문제) - 백그라운드 작업"""
    today = get_today_kst()
    
    # 작업 시작 (비동기)
    background_tasks.add_task(run_full_generation_task, today)
    
    return {
        "success": True,
        "date": today.isoformat(),
        "message": "통합 생성 작업이 백그라운드에서 시작되었습니다. 잠시 후 '콘텐츠 생성' 탭에서 결과를 확인해주세요."
    }

@router.get("/dataset-versions")
async def get_dataset_versions():
    """데이터셋/문제 생성 이력 조회"""
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT 
                    version_id,
                    created_at,
                    generation_date,
                    generation_type,
                    data_type,
                    problem_count,
                    n_users,
                    n_events,
                    status,
                    error_message,
                    duration_ms
                FROM public.dataset_versions
                ORDER BY created_at DESC
                LIMIT 30
            """)
            versions = []
            for _, row in df.iterrows():
                versions.append({
                    "version_id": row.get("version_id"),
                    "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                    "generation_date": row.get("generation_date").isoformat() if row.get("generation_date") else None,
                    "generation_type": row.get("generation_type"),
                    "data_type": row.get("data_type"),
                    "problem_count": row.get("problem_count"),
                    "n_users": row.get("n_users"),
                    "n_events": row.get("n_events"),
                    "status": row.get("status"),
                    "error_message": row.get("error_message"),
                    "duration_ms": row.get("duration_ms")
                })
            return {"success": True, "versions": versions}
    except Exception as e:
        return {"success": False, "message": str(e), "versions": []}


@router.get("/problem-files")
async def get_problem_files(admin=Depends(require_admin)):
    """문제 파일 목록 조회"""
    import os
    from pathlib import Path
    from datetime import datetime
    import json
    
    problem_dir = Path("/app/problems/daily")
    if not problem_dir.exists():
        problem_dir = Path("problems/daily")
    
    files = []
    
    try:
        for f in sorted(problem_dir.glob("*.json"), reverse=True):
            stat = f.stat()
            
            # 문제 개수 확인
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                    problem_count = len(data) if isinstance(data, list) else 1
            except:
                problem_count = 0
            
            # 파일 타입 구분
            file_type = "stream" if f.name.startswith("stream_") else "pa"
            
            files.append({
                "filename": f.name,
                "type": file_type,
                "size_kb": round(stat.st_size / 1024, 1),
                "problem_count": problem_count,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        # 최근 30개만 반환
        return {"success": True, "files": files[:30]}
    except Exception as e:
        return {"success": False, "message": str(e), "files": []}


@router.get("/scheduler-logs")
async def get_scheduler_logs(lines: int = 50):
    """스케줄러 로그 조회 (docker logs)"""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "compose", "logs", "scheduler", "--tail", str(lines)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/app"  # docker compose가 실행되는 위치
        )
        logs = result.stdout or result.stderr
        
        # 로그를 줄 단위로 파싱
        log_lines = []
        for line in logs.split('\n'):
            if 'scheduler-1' in line:
                # "scheduler-1  | " 제거
                clean_line = line.split('|', 1)[-1].strip() if '|' in line else line
                log_lines.append(clean_line)
        
        return {
            "success": True, 
            "logs": log_lines[-lines:],  # 최근 N줄
            "total_lines": len(log_lines)
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "로그 조회 타임아웃", "logs": []}
    except Exception as e:
        return {"success": False, "message": str(e), "logs": []}


@router.get("/scheduler-status")
async def get_scheduler_status_admin(admin=Depends(require_admin)):
    """스케줄러 상태 조회 (내부 스케줄러)"""
    try:
        from backend.scheduler import get_scheduler_status, scheduler
        status = get_scheduler_status()
        
        # 추가 정보
        jobs_info = []
        for job in scheduler.get_jobs():
            next_run = job.next_run_time
            jobs_info.append({
                "id": job.id,
                "name": job.name or job.id,
                "next_run": next_run.strftime("%Y-%m-%d %H:%M:%S KST") if next_run else "미정",
                "trigger": str(job.trigger)
            })
        
        return {
            "success": True,
            "running": status["running"],
            "jobs": jobs_info,
            "last_run_times": status["last_run_times"]
        }
    except Exception as e:
        return {"success": False, "message": str(e), "running": False, "jobs": []}


@router.post("/run-scheduler-job")
async def run_scheduler_job(job_type: str, admin=Depends(require_admin)):
    """스케줄러 작업 수동 실행"""
    try:
        if job_type == "weekday":
            from backend.scheduler import run_weekday_generation
            run_weekday_generation()
            return {"success": True, "message": "평일 문제/데이터 생성 작업 실행됨"}
        elif job_type == "sunday":
            from backend.scheduler import run_sunday_generation
            run_sunday_generation()
            return {"success": True, "message": "일요일 Stream 데이터 생성 작업 실행됨"}
        elif job_type == "cleanup":
            from backend.scheduler import cleanup_old_data
            cleanup_old_data()
            return {"success": True, "message": "데이터 정리 작업 실행됨"}
        else:
            return {"success": False, "message": f"알 수 없는 작업 타입: {job_type}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/reset-submissions")
async def reset_submissions(admin=Depends(require_admin)):
    """제출 기록 초기화 및 XP 리셋"""
    from backend.common.logging import get_logger
    logger = get_logger(__name__)

    try:
        with postgres_connection() as pg:
            pg.execute("TRUNCATE TABLE public.submissions RESTART IDENTITY")
            pg.execute("UPDATE public.users SET xp = 0, level = 1")
        
        # DuckDB의 분석용 데이터도 삭제
        try:
            with duckdb_connection() as duck:
                duck.execute("DELETE FROM pa_submissions")
        except Exception as e:
            logger.warning(f"Failed to delete DuckDB submissions during reset: {e}")
        
        return {
            "success": True,
            "message": "모든 제출 기록이 초기화되었습니다."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"초기화 실패: {str(e)}"
        }

@router.get("/logs")
async def get_system_logs(
    admin=Depends(require_admin),
    category: Optional[str] = Query(None, description="로그 카테고리"),
    level: Optional[str] = Query(None, description="로그 레벨"),
    limit: int = Query(100, description="조회 개수")
):
    """시스템 로그 조회"""
    logs = get_logs(category=category, level=level, limit=limit)
    return {
        "success": True,
        "logs": logs,
        "count": len(logs)
    }


@router.get("/log-categories")
async def get_log_categories(admin=Depends(require_admin)):
    """로그 카테고리 목록"""
    return {
        "categories": [
            {"id": "problem_generation", "name": "문제 생성", "icon": "🤖"},
            {"id": "user_action", "name": "사용자 액션", "icon": "👤"},
            {"id": "scheduler", "name": "스케줄러", "icon": "⏰"},
            {"id": "system", "name": "시스템", "icon": "🖥️"},
            {"id": "api", "name": "API", "icon": "🔌"}
        ]
    }


@router.get("/users")
async def get_all_users(admin=Depends(require_admin)):
    """전체 사용자 목록 조회"""
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT id, email, name, nickname, xp, level, is_admin, created_at
                FROM public.users
                ORDER BY created_at DESC
            """)
            users = []
            for _, row in df.iterrows():
                users.append({
                    "id": row["id"],
                    "email": row["email"],
                    "name": row["name"],
                    "nickname": row["nickname"],
                    "xp": int(row.get("xp", 0)),
                    "level": int(row.get("level", 1)),
                    "is_admin": bool(row.get("is_admin", False)),
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                })
            return {"success": True, "users": users, "count": len(users)}
    except Exception as e:
        return {"success": False, "message": str(e), "users": []}


@router.patch("/users/{user_id}/admin")
async def toggle_user_admin(user_id: str, admin=Depends(require_admin)):
    """사용자 관리자 권한 토글"""
    try:
        with postgres_connection() as pg:
            # 현재 상태 조회
            df = pg.fetch_df("SELECT is_admin FROM public.users WHERE id = %s", [user_id])
            if len(df) == 0:
                return {"success": False, "message": "사용자를 찾을 수 없습니다"}
            
            current_admin = bool(df.iloc[0].get("is_admin", False))
            new_admin = not current_admin
            
            pg.execute("UPDATE public.users SET is_admin = %s WHERE id = %s", [new_admin, user_id])
            
            db_log(
                category=LogCategory.SYSTEM,
                message=f"사용자 관리자 권한 변경: {user_id} -> {'관리자' if new_admin else '일반'}",
                level=LogLevel.INFO,
                source="admin_api"
            )
            
            return {"success": True, "is_admin": new_admin}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin=Depends(require_admin)):
    """사용자 삭제"""
    try:
        with postgres_connection() as pg:
            pg.execute("DELETE FROM public.submissions WHERE user_id = %s", [user_id])
            pg.execute("DELETE FROM public.user_problem_sets WHERE user_id = %s", [user_id])
            pg.execute("DELETE FROM public.users WHERE id = %s", [user_id])
            
            db_log(
                category=LogCategory.SYSTEM,
                message=f"사용자 삭제: {user_id}",
                level=LogLevel.WARNING,
                source="admin_api"
            )
            
            return {"success": True, "message": "사용자가 삭제되었습니다"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/api-usage")
async def get_api_usage(
    admin=Depends(require_admin),
    limit: int = Query(100, description="조회할 로그 수"),
    days: int = Query(7, description="최근 N일")
):
    """Gemini API 사용량 조회"""
    try:
        with postgres_connection() as pg:
            # 테이블 존재 확인
            pg.execute("""
                CREATE TABLE IF NOT EXISTS public.api_usage_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    purpose VARCHAR(100),
                    model VARCHAR(50),
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    user_id VARCHAR(100)
                )
            """)
            
            # 일별 사용량
            daily_df = pg.fetch_df("""
                SELECT 
                    DATE(timestamp) as date,
                    purpose,
                    COUNT(*) as call_count,
                    SUM(total_tokens) as total_tokens
                FROM public.api_usage_logs
                WHERE timestamp >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(timestamp), purpose
                ORDER BY date DESC, purpose
            """, [days])
            
            # 최근 로그
            logs_df = pg.fetch_df("""
                SELECT 
                    timestamp, purpose, model, input_tokens, output_tokens, total_tokens, user_id
                FROM public.api_usage_logs
                ORDER BY timestamp DESC
                LIMIT %s
            """, [limit])
            
            # 총계
            total_df = pg.fetch_df("""
                SELECT 
                    COUNT(*) as total_calls,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(SUM(input_tokens), 0) as input_tokens,
                    COALESCE(SUM(output_tokens), 0) as output_tokens
                FROM public.api_usage_logs
                WHERE timestamp >= CURRENT_DATE - INTERVAL '%s days'
            """, [days])
            
            # Gemini 가격 계산 (대략적 - 1.5 Pro 기준 $0.00025/1K input, $0.0005/1K output)
            total_input = int(total_df.iloc[0]['input_tokens']) if len(total_df) > 0 else 0
            total_output = int(total_df.iloc[0]['output_tokens']) if len(total_df) > 0 else 0
            estimated_cost_usd = (total_input / 1000 * 0.00025) + (total_output / 1000 * 0.0005)
            
            return {
                "summary": {
                    "total_calls": int(total_df.iloc[0]['total_calls']) if len(total_df) > 0 else 0,
                    "total_tokens": int(total_df.iloc[0]['total_tokens']) if len(total_df) > 0 else 0,
                    "input_tokens": total_input,
                    "output_tokens": total_output,
                    "estimated_cost_usd": round(estimated_cost_usd, 4),
                    "period_days": days
                },
                "daily": daily_df.to_dict('records') if len(daily_df) > 0 else [],
                "logs": logs_df.to_dict('records') if len(logs_df) > 0 else []
            }
    except Exception as e:
        return {"error": str(e), "summary": {}, "daily": [], "logs": []}


# ============================================
# Cloud Scheduler 트리거 엔드포인트
# ============================================

@router.post("/trigger/daily-generation")
async def trigger_daily_generation(request: Request):
    """Cloud Scheduler용 일일 데이터/문제 생성 트리거
    
    헤더에 X-Scheduler-Key가 SCHEDULER_API_KEY 환경변수와 일치해야 함
    """
    from backend.common.logging import get_logger
    logger = get_logger(__name__)
    
    # 요청 정보 로깅 (디버깅용)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")
    logger.info(f"[TRIGGER] Request received from IP={client_ip}, UA={user_agent[:50]}")
    
    # API 키 검증
    expected_key = os.environ.get("SCHEDULER_API_KEY", "")
    provided_key = request.headers.get("X-Scheduler-Key", "")
    
    if not expected_key:
        logger.warning("[TRIGGER] SCHEDULER_API_KEY not configured in environment")
        raise HTTPException(403, "Scheduler API key not configured")
    
    if provided_key != expected_key:
        logger.warning(f"[TRIGGER] Invalid API key provided (length={len(provided_key)})")
        raise HTTPException(403, "Invalid API key")
    
    logger.info("[TRIGGER] API key validated, starting daily generation")
    db_log(LogCategory.SCHEDULER, "Cloud Scheduler 트리거 수신 (인증 성공)", LogLevel.INFO, "trigger")

    # KST 기준 오늘 날짜 계산 (GCP 환경 대비)
    today = get_today_kst()
    logger.info(f"[TRIGGER] Target date: {today}")

    # 중복 실행 방지: 오늘 날짜로 이미 생성되었는지 확인
    try:
        from backend.services.database import postgres_connection
        with postgres_connection() as pg:
            # PA와 Stream 문제 모두 확인
            existing = pg.fetch_df("""
                SELECT data_type, COUNT(*) as cnt 
                FROM public.problems 
                WHERE session_date = %s 
                GROUP BY data_type
            """, [today])
            
            pa_count = 0
            stream_count = 0
            for _, row in existing.iterrows():
                if row.get("data_type") == "pa":
                    pa_count = int(row.get("cnt", 0))
                elif row.get("data_type") == "stream":
                    stream_count = int(row.get("cnt", 0))
            
            if pa_count > 0 and stream_count > 0:
                logger.info(f"[TRIGGER] Problems already exist for {today}: PA={pa_count}, Stream={stream_count}")
                db_log(LogCategory.SCHEDULER, f"{today} 중복 생성 방지 (PA={pa_count}, Stream={stream_count})", LogLevel.INFO, "trigger")
                return {
                    "status": "already_generated",
                    "date": str(today),
                    "pa_count": pa_count,
                    "stream_count": stream_count,
                    "message": f"{today} 날짜의 문제가 이미 생성되어 있습니다."
                }
            elif pa_count > 0 or stream_count > 0:
                logger.info(f"[TRIGGER] Partial generation detected for {today}: PA={pa_count}, Stream={stream_count}")
    except Exception as e:
        logger.warning(f"[TRIGGER] Duplicate check failed (continuing anyway): {e}")

    results = {"date": str(today), "pa_data": False, "stream_data": False, "pa_problems": False, "stream_problems": False}
    
    try:
        from backend.engine.postgres_engine import PostgresEngine
        from backend.config.db import PostgresEnv
        pg = PostgresEngine(PostgresEnv().dsn())
        
        # 1. 데이터 생성
        try:
            from backend.generator.data_generator_advanced import generate_data
            generate_data(modes=("pa", "stream"))
            results["pa_data"] = True
            results["stream_data"] = True
            logger.info("[TRIGGER] Data generation done")
        except Exception as e:
            logger.warning(f"[TRIGGER] Data gen error: {e}")
        
        # 2. PA 문제 생성 (통합 generator 사용)
        try:
            from problems.generator import generate
            generate(today, pg, mode="pa")  # 2세트 = 12문제
            results["pa_problems"] = True
            logger.info("[TRIGGER] PA problems generated (unified generator)")
        except Exception as e:
            logger.warning(f"[TRIGGER] PA problem gen error: {e}")

        # 3. Stream 문제 생성 (통합 generator 사용)
        try:
            from problems.generator import generate
            generate(today, pg, mode="stream")  # 1세트 = 6문제
            results["stream_problems"] = True
            logger.info("[TRIGGER] Stream problems generated (unified generator)")
        except Exception as e:
            logger.warning(f"[TRIGGER] Stream problem gen error: {e}")
        
        # 4. 오늘의 팁 생성
        try:
            from backend.services.tip_service import generate_tip_of_the_day
            generate_tip_of_the_day(today)
            results["daily_tip"] = True
            logger.info("[TRIGGER] Daily tip generated")
        except Exception as e:
            logger.warning(f"[TRIGGER] Tip gen error: {e}")
        
        db_log(LogCategory.SCHEDULER, f"일일 생성 완료: {results}", LogLevel.INFO, "trigger")
        
    except Exception as e:
        logger.error(f"[TRIGGER] Fatal error: {e}")
        results["error"] = str(e)
        
        # [AI Doctor] 치명적 에러 발생 시 자동 진단 및 복구 시도
        try:
            from backend.services.ai_doctor import AIDoctor, send_doctor_report
            doctor = AIDoctor()
            diagnosis_report = doctor.diagnose_and_heal(e, results)
            send_doctor_report(diagnosis_report, str(today))
            logger.info("[AI Doctor] Diagnosis and report sent.")
            results["ai_diagnosis"] = diagnosis_report
        except Exception as doctor_err:
            logger.error(f"[AI Doctor] Failed to diagnose: {doctor_err}")
    
    # 5. 결과 이메일 알림 발송 (정상 또는 일부 실패 시)
    if not results.get("ai_diagnosis"): # AI Doctor가 처리하지 않은 경우만 일반 이메일 발송
        try:
            from backend.services.notification_service import send_email
            status_str = "성공" if results.get("pa_problems") and results.get("stream_problems") else "일부 실패"
            if "error" in results:
                status_str = "치명적 실패"
                
            subject = f"일일 데이터 생성 결과: {status_str} ({results['date']})"
            body = f"일일 데이터 및 문제 생성 결과 보고입니다.\n\n"
            body += f"- 날짜: {results['date']}\n"
            body += f"- PA 데이터: {'✅' if results.get('pa_data') else '❌'}\n"
            body += f"- Stream 데이터: {'✅' if results.get('stream_data') else '❌'}\n"
            body += f"- PA 문제: {'✅' if results.get('pa_problems') else '❌'}\n"
            body += f"- Stream 문제: {'✅' if results.get('stream_problems') else '❌'}\n"
            body += f"- 오늘의 팁: {'✅' if results.get('daily_tip') else '❌'}\n"
            
            if "error" in results:
                body += f"\n[에러 발생]\n{results['error']}\n"
                
            send_email(subject, body)
        except Exception as email_err:
            logger.error(f"Failed to send result email: {email_err}")
    
    return results


@router.post("/trigger/daily-tip")
async def trigger_daily_tip(request: Request):
    """오늘의 팁 생성 트리거 (독립 호출용)"""
    expected_key = os.environ.get("SCHEDULER_API_KEY", "")
    provided_key = request.headers.get("X-Scheduler-Key", "")

    if not expected_key or provided_key != expected_key:
        raise HTTPException(403, "Invalid API key")

    from backend.services.tip_service import generate_tip_of_the_day
    today = get_today_kst()
    return generate_tip_of_the_day(today)


@router.post("/schedule/run", response_model=ScheduleRunResponse)
async def run_scheduled_generation(request: Request):
    """Cloud Scheduler용 엔드포인트 - Worker Job 트리거

    Cloud Run Job을 비동기로 실행하고 즉시 반환합니다.
    실제 데이터/문제 생성은 Worker Job에서 수행됩니다.
    """
    import time
    import subprocess
    from backend.common.logging import get_logger
    logger = get_logger(__name__)

    start_time = time.time()

    # API 키 검증
    expected_key = os.environ.get("SCHEDULER_API_KEY", "")
    provided_key = request.headers.get("X-Scheduler-Key", "")

    if not expected_key:
        logger.warning("[SCHEDULE/RUN] SCHEDULER_API_KEY not configured")
        raise HTTPException(403, "Scheduler API key not configured")

    if provided_key != expected_key:
        logger.warning(f"[SCHEDULE/RUN] Invalid API key (length={len(provided_key)})")
        raise HTTPException(403, "Invalid API key")

    logger.info("[SCHEDULE/RUN] API key validated, triggering Worker Job")

    today = get_today_kst()
    
    # 중복 실행 방지 확인
    try:
        with postgres_connection() as pg:
            existing = pg.fetch_df("""
                SELECT data_type, COUNT(*) as cnt
                FROM public.problems
                WHERE problem_date = %s
                GROUP BY data_type
            """, [today])

            pa_count = 0
            for _, row in existing.iterrows():
                if row.get("data_type") == "pa":
                    pa_count = int(row.get("cnt", 0))

            if pa_count > 0:
                duration = time.time() - start_time
                logger.info(f"[SCHEDULE/RUN] Already generated for {today}")
                return ScheduleRunResponse(
                    status="already_generated",
                    data_generated=True,
                    problems_generated=pa_count,
                    duration_sec=round(duration, 2),
                    date=str(today),
                    details={"pa_count": pa_count, "message": "Problems already exist for today"}
                )
    except Exception as e:
        logger.warning(f"[SCHEDULE/RUN] Duplicate check failed: {e}")

    # Cloud Run Job 트리거 (비동기)
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "querycraft-483512")
    region = os.environ.get("CLOUD_RUN_REGION", "us-central1")
    job_name = "querycraft-worker"
    
    job_triggered = False
    job_execution_id = None
    
    try:
        # gcloud로 Job 실행 (비동기)
        cmd = [
            "gcloud", "run", "jobs", "execute", job_name,
            f"--region={region}",
            f"--project={project_id}",
            "--async",  # 비동기 실행
            "--format=json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            job_triggered = True
            # Job execution ID 추출 시도
            try:
                import json
                output = json.loads(result.stdout)
                job_execution_id = output.get("metadata", {}).get("name", "").split("/")[-1]
            except:
                job_execution_id = "triggered"
            logger.info(f"[SCHEDULE/RUN] Worker Job triggered: {job_execution_id}")
        else:
            logger.error(f"[SCHEDULE/RUN] Job trigger failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("[SCHEDULE/RUN] Job trigger timeout")
    except FileNotFoundError:
        logger.warning("[SCHEDULE/RUN] gcloud not found, falling back to inline execution")
        # gcloud 없으면 기존 방식으로 폴백
        return await _run_generation_inline(today, start_time)
    except Exception as e:
        logger.error(f"[SCHEDULE/RUN] Job trigger error: {e}")

    duration = time.time() - start_time
    
    if job_triggered:
        db_log(
            LogCategory.SCHEDULER,
            f"Worker Job triggered for {today} (execution_id={job_execution_id})",
            LogLevel.INFO,
            "schedule_run"
        )
        
        return ScheduleRunResponse(
            status="job_triggered",
            data_generated=False,  # Job이 처리할 예정
            problems_generated=0,
            duration_sec=round(duration, 2),
            date=str(today),
            details={
                "job_name": job_name,
                "execution_id": job_execution_id,
                "message": "Worker Job triggered asynchronously. Check job logs for progress."
            }
        )
    else:
        return ScheduleRunResponse(
            status="trigger_failed",
            data_generated=False,
            problems_generated=0,
            duration_sec=round(duration, 2),
            date=str(today),
            details={"error": "Failed to trigger Worker Job"}
        )


async def _run_generation_inline(today, start_time):
    """폴백: 인라인 생성 (Worker Job 없을 때)"""
    import time
    from backend.common.logging import get_logger
    logger = get_logger(__name__)
    
    data_generated = False
    problems_generated = 0
    details = {"date": str(today), "fallback": True}
    
    # 1. 데이터 생성 (PA만)
    try:
        from backend.generator.data_generator_advanced import generate_data
        generate_data(modes=("pa",))
        data_generated = True
        logger.info("[SCHEDULE/RUN] Fallback: PA data generation completed")
    except Exception as e:
        logger.error(f"[SCHEDULE/RUN] Fallback: Data generation failed: {e}")
        details["data_error"] = str(e)

    # 2. PA 문제 생성
    try:
        from problems.generator import generate as gen_pa
        with postgres_connection() as pg:
            gen_pa(today, pg)
            
            pa_df = pg.fetch_df("""
                SELECT COUNT(*) as cnt FROM public.problems
                WHERE problem_date = %s AND data_type = 'pa'
            """, [today])
            pa_count = int(pa_df.iloc[0]["cnt"]) if len(pa_df) > 0 else 0
            details["pa_problems"] = pa_count
            problems_generated += pa_count
            
        logger.info(f"[SCHEDULE/RUN] Fallback: PA problems generated: {pa_count}")
    except Exception as e:
        logger.error(f"[SCHEDULE/RUN] Fallback: PA problem generation failed: {e}")
        details["pa_error"] = str(e)

    duration = time.time() - start_time
    status = "success" if problems_generated > 0 else "error"

    db_log(
        LogCategory.SCHEDULER,
        f"Fallback generation completed: {status} (problems={problems_generated})",
        LogLevel.INFO if status == "success" else LogLevel.WARNING,
        "schedule_run"
    )

    return ScheduleRunResponse(
        status=status,
        data_generated=data_generated,
        problems_generated=problems_generated,
        duration_sec=round(duration, 2),
        date=str(today),
        details=details
    )

