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
    # DB 초기화 (테이블 생성) - 실패해도 앱은 시작
    try:
        from backend.services.db_init import init_database
        init_database()
    except Exception as e:
        print(f"[WARNING] Database initialization failed: {e}")
        print("[WARNING] App will start anyway, but some features may not work")
    
    # 스케줄러 시작 (환경변수로 활성화)
    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        try:
            from backend.scheduler import start_scheduler, stop_scheduler
            start_scheduler()
            yield
            stop_scheduler()
        except Exception as e:
            print(f"[WARNING] Scheduler failed: {e}")
            yield
    else:
        yield


app = FastAPI(
    title="QueryCraft API",
    description="AI 기반 SQL 학습 플랫폼 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:15173")
origins = [
    FRONTEND_URL,
    "http://localhost:15173",
    "http://127.0.0.1:15173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if os.getenv("ENV") == "production" else ["*"],
    allow_origin_regex=r"https://query-craft-.*\.a\.run\.app" if os.getenv("ENV") == "production" else None,
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
