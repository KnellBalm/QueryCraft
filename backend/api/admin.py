# backend/api/admin.py
"""관리자 API"""
from datetime import date
from backend.common.date_utils import get_today_kst
import json
import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Query

from backend.schemas.admin import (
    SystemStatus, SchedulerStatus, DatabaseTable, TodayProblemsStatus,
    GenerateProblemsRequest, GenerateProblemsResponse,
    RefreshDataRequest, RefreshDataResponse
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


@router.get("/status", response_model=SystemStatus)
async def get_system_status(admin=Depends(require_admin)):
    """시스템 상태 조회"""
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
    except:
        pass
    
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
    except:
        pass
    
    # 오늘의 문제 현황 확인
    today = get_today_kst()
    patterns = [
        f"problems/daily/{today.isoformat()}.json",
        f"problems/daily/{today.isoformat()}_set0.json",
        f"problems/daily/{today.isoformat()}_set1.json",
        f"problems/daily/stream_{today.isoformat()}.json"
    ]
    
    today_problems = None
    all_problems = []
    found_any = False
    
    try:
        for p_path in patterns:
            # 절대 경로와 상대 경로 모두 체크 (컨테이너 내 환경 고려)
            abs_path = os.path.join("/app", p_path) if not p_path.startswith("/") else p_path
            target_path = abs_path if os.path.exists(abs_path) else p_path
            
            if os.path.exists(target_path):
                found_any = True
                with open(target_path, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_problems.extend(data)
                    else:
                        all_problems.append(data)
        
        if found_any:
            difficulties = {}
            for p in all_problems:
                diff = p.get("difficulty", "unknown")
                difficulties[diff] = difficulties.get(diff, 0) + 1
            
            today_problems = TodayProblemsStatus(
                exists=True,
                count=len(all_problems),
                difficulties=difficulties,
                path=patterns[0] # 대표 경로
            )
        else:
            today_problems = TodayProblemsStatus(exists=False)
    except Exception as e:
        from backend.common.logging import get_logger
        get_logger(__name__).error(f"Error checking today problems: {e}")
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
    """문제 생성 (PA 또는 Stream)"""
    today = get_today_kst()
    
    if request.data_type == "pa":
        try:
            from problems.generator import generate as gen_problems
            
            with postgres_connection() as pg:
                path = gen_problems(today, pg)
            
            # 생성된 문제 수 확인
            import json
            with open(path, encoding="utf-8") as f:
                problems = json.load(f)
            
            return GenerateProblemsResponse(
                success=True,
                message="PA 문제 생성 완료",
                path=path,
                problem_count=len(problems)
            )
        except Exception as e:
            return GenerateProblemsResponse(
                success=False,
                message=f"PA 문제 생성 실패: {str(e)}"
            )
    
    elif request.data_type == "stream":
        try:
            from problems.generator_stream import generate_stream_problems
            
            with postgres_connection() as pg:
                path = generate_stream_problems(today, pg)
            
            import json
            with open(path, encoding="utf-8") as f:
                problems = json.load(f)
            
            return GenerateProblemsResponse(
                success=True,
                message="Stream 문제 생성 완료",
                path=path,
                problem_count=len(problems)
            )
        except Exception as e:
            return GenerateProblemsResponse(
                success=False,
                message=f"Stream 문제 생성 실패: {str(e)}"
            )
    
    else:
        return GenerateProblemsResponse(
            success=False,
            message="지원하지 않는 data_type입니다."
        )


@router.post("/refresh-data", response_model=RefreshDataResponse)
async def refresh_data(request: RefreshDataRequest, admin=Depends(require_admin)):
    """데이터 갱신"""
    try:
        from backend.generator.data_generator_advanced import generate_data
        
        if request.data_type == "pa":
            generate_data(modes=("pa",))
            return RefreshDataResponse(success=True, message="PA 데이터 갱신 완료")
        elif request.data_type == "stream":
            generate_data(modes=("stream",))
            return RefreshDataResponse(success=True, message="Stream 데이터 갱신 완료")
        else:
            return RefreshDataResponse(success=False, message="잘못된 data_type")
    except Exception as e:
        return RefreshDataResponse(success=False, message=f"데이터 갱신 실패: {str(e)}")






@router.post("/initial-setup")
async def initial_setup(admin=Depends(require_admin)):
    """초기 데이터 셋업 (PA + Stream 데이터 및 문제 생성)"""
    results = []
    errors = []
    
    try:
        # 1. PA 데이터 생성
        try:
            from backend.generator.data_generator_advanced import generate_data
            generate_data(modes=("pa",))
            results.append("✓ PA 데이터 생성 완료")
        except Exception as e:
            errors.append(f"✗ PA 데이터 생성 실패: {str(e)}")
        
        # 2. Stream 데이터 생성
        try:
            from backend.generator.data_generator_advanced import generate_data
            generate_data(modes=("stream",))
            results.append("✓ Stream 데이터 생성 완료")
        except Exception as e:
            errors.append(f"✗ Stream 데이터 생성 실패: {str(e)}")
        
        # 3. PA 문제 생성
        try:
            from problems.generator import generate as gen_problems
            with postgres_connection() as pg:
                path = gen_problems(get_today_kst(), pg)
            results.append(f"✓ PA 문제 생성 완료: {path}")
        except Exception as e:
            errors.append(f"✗ PA 문제 생성 실패: {str(e)}")
        
        # 4. Stream 문제 생성
        try:
            from problems.generator_stream import generate_stream_problems
            with postgres_connection() as pg:
                path = generate_stream_problems(get_today_kst(), pg)
            results.append(f"✓ Stream 문제 생성 완료: {path}")
        except Exception as e:
            errors.append(f"✗ Stream 문제 생성 실패: {str(e)}")
        
        db_log(
            category=LogCategory.SYSTEM,
            message=f"Initial setup completed. Success: {len(results)}, Errors: {len(errors)}",
            level=LogLevel.INFO if not errors else LogLevel.WARNING,
            source="admin"
        )
        
        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "message": f"{len(results)}개 작업 완료, {len(errors)}개 실패"
        }
    except Exception as e:
        return {
            "success": False,
            "results": results,
            "errors": errors + [f"Unexpected error: {str(e)}"],
            "message": "초기화 중 오류 발생"
        }


@router.post("/trigger-now")
async def trigger_generation_now(admin=Depends(require_admin)):
    """즉시 문제/데이터 생성 실행 (스케줄러 수동 트리거)"""
    results = []
    errors = []
    
    from datetime import date
    today = get_today_kst()
    
    try:
        # 1. 데이터 생성 (PA + Stream)
        try:
            from backend.generator.data_generator_advanced import generate_data
            generate_data(modes=("pa", "stream"))
            results.append("✓ PA/Stream 데이터 생성 완료")
        except Exception as e:
            errors.append(f"✗ 데이터 생성 실패: {str(e)}")
        
        # 2. PA 문제 생성
        try:
            from problems.generator import generate as gen_pa
            with postgres_connection() as pg:
                path = gen_pa(today, pg)
            results.append(f"✓ PA 문제 생성 완료: {path}")
        except Exception as e:
            errors.append(f"✗ PA 문제 생성 실패: {str(e)}")
        
        # 3. Stream 문제 생성
        try:
            from problems.generator_stream import generate_stream_problems
            with duckdb_connection() as duck:
                path = generate_stream_problems(target_date=today, duck=duck)
            results.append(f"✓ Stream 문제 생성 완료: {path}")
        except Exception as e:
            errors.append(f"✗ Stream 문제 생성 실패: {str(e)}")
        
        return {
            "success": len(errors) == 0,
            "date": today.isoformat(),
            "results": results,
            "errors": errors,
            "message": f"완료 ({len(results)}개 성공, {len(errors)}개 실패)"
        }
    except Exception as e:
        return {
            "success": False,
            "results": results,
            "errors": errors + [str(e)],
            "message": "예기치 않은 오류"
        }

@router.get("/dataset-versions")
async def get_dataset_versions():
    """데이터셋 버전 이력 조회"""
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("""
                SELECT 
                    version_id,
                    created_at,
                    generator_type,
                    start_date,
                    end_date,
                    n_users,
                    n_events
                FROM public.dataset_versions
                ORDER BY created_at DESC
                LIMIT 20
            """)
            versions = df.to_dict(orient="records")
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
    try:
        with postgres_connection() as pg:
            pg.execute("TRUNCATE TABLE public.submissions RESTART IDENTITY")
            pg.execute("UPDATE public.users SET xp = 0, level = 1")
        
        # DuckDB의 분석용 데이터도 삭제
        try:
            with duckdb_connection() as duck:
                duck.execute("DELETE FROM pa_submissions")
        except:
            pass
        
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
    
    # API 키 검증
    expected_key = os.environ.get("SCHEDULER_API_KEY", "")
    provided_key = request.headers.get("X-Scheduler-Key", "")
    
    if not expected_key:
        logger.warning("SCHEDULER_API_KEY not configured")
        raise HTTPException(403, "Scheduler API key not configured")
    
    if provided_key != expected_key:
        logger.warning("Invalid scheduler API key")
        raise HTTPException(403, "Invalid API key")
    
    logger.info("[TRIGGER] Daily generation triggered by Cloud Scheduler")
    db_log(LogCategory.SCHEDULER, "Cloud Scheduler 트리거 수신", LogLevel.INFO, "trigger")
    
    # KST 기준 오늘 날짜 계산 (GCP 환경 대비)
    today = get_today_kst()
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
        
        # 2. PA 문제 생성
        try:
            from problems.generator import generate as gen_pa
            gen_pa(today, pg)
            results["pa_problems"] = True
            logger.info("[TRIGGER] PA problems generated")
        except Exception as e:
            logger.warning(f"[TRIGGER] PA problem gen error: {e}")
        
        # 3. Stream 문제 생성
        try:
            from problems.generator_stream import generate_stream_problems
            generate_stream_problems(today, pg)
            results["stream_problems"] = True
            logger.info("[TRIGGER] Stream problems generated")
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
