# backend/api/auth.py
"""OAuth 인증 API (Google, Kakao)"""
import os
from typing import Optional
from datetime import datetime, timedelta
import secrets
import hashlib

from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx

from backend.services.database import postgres_connection
from common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# 환경변수
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID", "")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:15173")

# 세션 저장소 (간단한 인메모리, 프로덕션에서는 Redis 사용)
sessions: dict[str, dict] = {}


class LoginResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    message: str = ""


def create_session(user_data: dict) -> str:
    """세션 생성"""
    session_id = secrets.token_hex(32)
    sessions[session_id] = {
        "user": user_data,
        "created_at": datetime.now().isoformat()
    }
    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """세션 조회"""
    return sessions.get(session_id)


def ensure_users_table():
    """users 테이블 생성"""
    try:
        with postgres_connection() as pg:
            pg.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    provider TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
    except Exception as e:
        logger.error(f"Failed to create users table: {e}")


# 시작 시 테이블 생성
ensure_users_table()


# =============================================
# Google OAuth
# =============================================
@router.get("/google/login")
async def google_login():
    """Google 로그인 시작"""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(400, "Google OAuth not configured")
    
    redirect_uri = f"{FRONTEND_URL.replace('15173', '15174')}/auth/google/callback"
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=email%20profile"
    )
    return RedirectResponse(google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str, response: Response):
    """Google OAuth 콜백"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(400, "Google OAuth not configured")
    
    redirect_uri = f"{FRONTEND_URL.replace('15173', '15174')}/auth/google/callback"
    
    # 토큰 교환
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
        )
        
        if token_res.status_code != 200:
            raise HTTPException(400, "Failed to get access token")
        
        tokens = token_res.json()
        access_token = tokens.get("access_token")
        
        # 사용자 정보 조회
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_res.status_code != 200:
            raise HTTPException(400, "Failed to get user info")
        
        user_info = user_res.json()
    
    # 사용자 저장/업데이트
    user_id = f"google_{user_info['id']}"
    save_user(user_id, user_info.get("email"), user_info.get("name"), "google")
    
    # 세션 생성
    session_id = create_session({
        "id": user_id,
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "provider": "google"
    })
    
    # 쿠키 설정 및 프론트엔드로 리다이렉트
    redirect = RedirectResponse(f"{FRONTEND_URL}?login=success")
    redirect.set_cookie("session_id", session_id, max_age=86400*7, httponly=True)
    return redirect


# =============================================
# Kakao OAuth
# =============================================
@router.get("/kakao/login")
async def kakao_login():
    """Kakao 로그인 시작"""
    if not KAKAO_CLIENT_ID:
        raise HTTPException(400, "Kakao OAuth not configured")
    
    redirect_uri = f"{FRONTEND_URL.replace('15173', '15174')}/auth/kakao/callback"
    kakao_auth_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
    )
    return RedirectResponse(kakao_auth_url)


@router.get("/kakao/callback")
async def kakao_callback(code: str, response: Response):
    """Kakao OAuth 콜백"""
    if not KAKAO_CLIENT_ID:
        raise HTTPException(400, "Kakao OAuth not configured")
    
    redirect_uri = f"{FRONTEND_URL.replace('15173', '15174')}/auth/kakao/callback"
    
    # 토큰 교환
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": KAKAO_CLIENT_ID,
                "client_secret": KAKAO_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "code": code
            }
        )
        
        if token_res.status_code != 200:
            raise HTTPException(400, "Failed to get access token")
        
        tokens = token_res.json()
        access_token = tokens.get("access_token")
        
        # 사용자 정보 조회
        user_res = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_res.status_code != 200:
            raise HTTPException(400, "Failed to get user info")
        
        user_info = user_res.json()
    
    # 사용자 저장/업데이트
    kakao_account = user_info.get("kakao_account", {})
    profile = kakao_account.get("profile", {})
    
    user_id = f"kakao_{user_info['id']}"
    email = kakao_account.get("email", f"{user_info['id']}@kakao.user")
    name = profile.get("nickname", "Kakao User")
    
    save_user(user_id, email, name, "kakao")
    
    # 세션 생성
    session_id = create_session({
        "id": user_id,
        "email": email,
        "name": name,
        "provider": "kakao"
    })
    
    # 쿠키 설정 및 프론트엔드로 리다이렉트
    redirect = RedirectResponse(f"{FRONTEND_URL}?login=success")
    redirect.set_cookie("session_id", session_id, max_age=86400*7, httponly=True)
    return redirect


# =============================================
# 공통 API
# =============================================
@router.get("/me")
async def get_me(request: Request):
    """현재 로그인 사용자 정보"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"logged_in": False}
    
    session = get_session(session_id)
    if not session:
        return {"logged_in": False}
    
    return {"logged_in": True, "user": session["user"]}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """로그아웃"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    response.delete_cookie("session_id")
    return {"success": True}


@router.get("/status")
async def auth_status():
    """OAuth 설정 상태"""
    return {
        "google_configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        "kakao_configured": bool(KAKAO_CLIENT_ID)
    }


def save_user(user_id: str, email: str, name: str, provider: str):
    """사용자 저장/업데이트"""
    try:
        with postgres_connection() as pg:
            pg.execute("""
                INSERT INTO users (id, email, name, provider)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
            """, (user_id, email, name, provider))
    except Exception as e:
        logger.error(f"Failed to save user: {e}")
