# backend/main.py
"""
QueryCraft - FastAPI Backend
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.problems import router as problems_router
from backend.api.sql import router as sql_router
from backend.api.stats import router as stats_router
from backend.api.admin import router as admin_router
from backend.api.auth import router as auth_router
from backend.api.practice import router as practice_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 수명 주기 관리 - DB 초기화 및 스케줄러 시작/중지"""
    import threading
    
    # DB 초기화 (백그라운드에서 실행 - 서버 시작 블로킹 방지)
    def init_background():
        try:
            from backend.services.db_init import init_database
            init_database()
            print("[INFO] Database initialized successfully")
        except Exception as e:
            print(f"[WARNING] Database initialization failed: {e}")
    
    threading.Thread(target=init_background, daemon=True).start()
    
    # 스케줄러 시작 (프로덕션에서 자동 활성화)
    scheduler_started = False
    if os.getenv("ENV") == "production":
        try:
            from backend.scheduler import start_scheduler, stop_scheduler
            
            def start_scheduler_background():
                import time
                time.sleep(5)  # DB 초기화 대기
                try:
                    start_scheduler()
                    print("[INFO] Scheduler started in background")
                except Exception as e:
                    print(f"[WARNING] Scheduler start failed: {e}")
            
            threading.Thread(target=start_scheduler_background, daemon=True).start()
            scheduler_started = True
        except Exception as e:
            print(f"[WARNING] Scheduler import failed: {e}")
    
    yield
    
    if scheduler_started:
        try:
            from backend.scheduler import stop_scheduler
            stop_scheduler()
        except:
            pass


app = FastAPI(
    title="QueryCraft API",
    description="AI 기반 SQL 학습 플랫폼 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 - 환경별 분리
if os.getenv("ENV") == "production":
    # 프로덕션: 특정 도메인만 허용
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://query-craft-frontend-53ngedkhia-uc.a.run.app",
        ],
        allow_origin_regex=r"https://.*\.run\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # 개발: localhost 및 개발서버 IP 허용
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:15173", 
            "http://127.0.0.1:15173", 
            "http://localhost:3000",
            "http://192.168.101.224:15173",  # 개발서버 IP
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 라우터 등록
app.include_router(problems_router)
app.include_router(sql_router)
app.include_router(stats_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(practice_router)


@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "status": "ok",
        "service": "QueryCraft API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy"}
