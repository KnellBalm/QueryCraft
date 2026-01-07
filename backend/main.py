# backend/main.py
"""
QueryCraft - FastAPI Backend
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.api.problems import router as problems_router
from backend.api.sql import router as sql_router
from backend.api.stats import router as stats_router
from backend.api.admin import router as admin_router
from backend.api.auth import router as auth_router
from backend.api.practice import router as practice_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 수명 주기 관리 - DB 초기화"""
    import threading
    
    def init_background():
        """백그라운드에서 DB 초기화 (서버 시작 블로킹 방지)"""
        try:
            from backend.services.db_init import init_database
            init_database()
            print("[INFO] Database initialized in background")
        except Exception as e:
            print(f"[WARNING] Background DB init failed: {e}")
    
    print(f"[INFO] ENV: {os.getenv('ENV', 'not set')}")
    print(f"[INFO] Starting server immediately, DB init in background...")
    
    # DB 초기화를 백그라운드 스레드에서 실행 (서버 시작 블로킹 없음)
    threading.Thread(target=init_background, daemon=True).start()
    
    # NOTE: MSA 아키텍처에서는 Cloud Functions가 문제/팁 생성 담당
    yield


app = FastAPI(
    title="QueryCraft API",
    description="AI 기반 SQL 학습 플랫폼 API",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 파싱 에러(422/400) 발생 시 상세 내용을 로그에 기록"""
    from backend.common.logging import get_logger
    logger = get_logger("validation")
    
    error_details = exc.errors()
    logger.error(f"Validation Error at {request.url.path}: {error_details}")
    logger.error(f"Request body structure: {exc.body}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details, "body": str(exc.body)},
    )

# CORS 설정
FRONTEND_URL = os.getenv("FRONTEND_URL", "").strip()
origins = [
    "http://localhost:15173",
    "http://127.0.0.1:15173",
]
if FRONTEND_URL:
    origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    # Production에서는 origins가 비어있어도 allow_origin_regex가 커버함
    allow_origins=origins if os.getenv("ENV") == "production" else ["*"],
    allow_origin_regex=r"https://.*.run.app" if os.getenv("ENV") == "production" else None,
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
