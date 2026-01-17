# tests/test_auth.py
"""Auth API 테스트"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from backend.api.auth import hash_password, verify_password


class TestPasswordHashing:
    """비밀번호 해싱 테스트 (bcrypt)"""

    def test_hash_password_returns_bcrypt_hash(self):
        """bcrypt 해시 형식 확인"""
        result = hash_password("testpassword")
        # bcrypt 해시는 $2b$ 또는 $2a$로 시작
        assert result.startswith("$2b$") or result.startswith("$2a$")
        # bcrypt 해시 길이는 60자
        assert len(result) == 60

    def test_hash_password_different_salts(self):
        """같은 비밀번호도 다른 해시 생성"""
        hash1 = hash_password("testpassword")
        hash2 = hash_password("testpassword")
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """올바른 비밀번호 검증"""
        password = "mySecurePassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """잘못된 비밀번호 검증"""
        hashed = hash_password("correctPassword")
        assert verify_password("wrongPassword", hashed) is False

    def test_verify_password_invalid_hash_format(self):
        """잘못된 해시 형식"""
        assert verify_password("password", "invalid_hash") is False
        assert verify_password("password", "") is False
        assert verify_password("password", "no_colon_here") is False

    def test_verify_password_empty_inputs(self):
        """빈 입력값 처리"""
        hashed = hash_password("password")
        assert verify_password("", hashed) is False

    def test_hash_password_unicode(self):
        """유니코드 비밀번호 처리"""
        password = "비밀번호123!@#"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_hash_password_special_chars(self):
        """특수문자 비밀번호"""
        password = "p@$$w0rd!#$%^&*()"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_bcrypt_computational_cost(self):
        """bcrypt는 계산 비용이 있어야 함 (SHA256보다 느림)"""
        import time
        password = "testpassword123"

        # bcrypt 해싱 시간 측정
        start = time.time()
        hash_password(password)
        elapsed = time.time() - start

        # bcrypt는 최소 10ms 이상 걸려야 함 (rounds=12)
        # 너무 빠르면 보안에 취약
        assert elapsed > 0.01, "bcrypt 해싱이 너무 빠름 (보안 취약)"

    def test_bcrypt_rounds_in_hash(self):
        """bcrypt 해시에 rounds 정보 포함"""
        result = hash_password("password")
        # $2b$12$... 형식 (12 rounds)
        parts = result.split("$")
        assert len(parts) >= 4
        assert parts[2] == "12", "bcrypt rounds should be 12"


class TestAuthEndpoints:
    """Auth API 엔드포인트 테스트 (모킹 사용)"""

    @pytest.fixture
    def mock_pg(self):
        """PostgreSQL 연결 모킹"""
        with patch('backend.api.auth.postgres_connection') as mock:
            pg_instance = MagicMock()
            mock.return_value.__enter__ = MagicMock(return_value=pg_instance)
            mock.return_value.__exit__ = MagicMock(return_value=False)
            yield pg_instance

    def test_register_validation_empty_email(self):
        """회원가입 - 빈 이메일 검증"""
        from fastapi.testclient import TestClient
        from backend.main import app

        with patch('backend.api.auth.postgres_connection'):
            client = TestClient(app)
            response = client.post("/api/auth/register", json={
                "email": "",
                "password": "password123!",
                "name": "Test User"
            })
            assert response.status_code == 400

    def test_register_validation_short_password(self):
        """회원가입 - 짧은 비밀번호 검증"""
        from fastapi.testclient import TestClient
        from backend.main import app

        with patch('backend.api.auth.postgres_connection'):
            client = TestClient(app)
            response = client.post("/api/auth/register", json={
                "email": "test@example.com",
                "password": "Short1!",  # 8자 미만
                "name": "Test User"
            })
            assert response.status_code == 400
            assert "8자 이상" in response.json().get("detail", "")

    def test_register_validation_complexity_no_upper(self):
        """회원가입 - 대문자 누락"""
        from fastapi.testclient import TestClient
        from backend.main import app
        client = TestClient(app)
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "lowercase123!",
            "name": "Test User"
        })
        assert response.status_code == 400
        assert "대문자" in response.json().get("detail", "")

    def test_register_validation_complexity_no_number(self):
        """회원가입 - 숫자 누락"""
        from fastapi.testclient import TestClient
        from backend.main import app
        client = TestClient(app)
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "NoNumberHere!",
            "name": "Test User"
        })
        assert response.status_code == 400
        assert "숫자" in response.json().get("detail", "")

    def test_register_validation_complexity_no_special(self):
        """회원가입 - 특수문자 누락"""
        from fastapi.testclient import TestClient
        from backend.main import app
        client = TestClient(app)
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "NoSpecialChar123",
            "name": "Test User"
        })
        assert response.status_code == 400
        assert "특수문자" in response.json().get("detail", "")

    def test_login_validation_empty_credentials(self):
        """로그인 - 빈 입력값 검증"""
        from fastapi.testclient import TestClient
        from backend.main import app

        with patch('backend.api.auth.postgres_connection'):
            client = TestClient(app)
            response = client.post("/api/auth/login", json={
                "email": "",
                "password": ""
            })
            assert response.status_code == 400

    def test_auth_status(self):
        """OAuth 설정 상태 확인"""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "google_configured" in data
        assert "kakao_configured" in data

    def test_get_me_not_logged_in(self):
        """비로그인 상태에서 /me 호출"""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["logged_in"] is False

    def test_logout_without_session(self):
        """세션 없이 로그아웃"""
        from fastapi.testclient import TestClient
        from backend.main import app

        with patch('backend.api.auth.delete_session'):
            client = TestClient(app)
            response = client.post("/api/auth/logout")
            assert response.status_code == 200
            assert response.json()["success"] is True


class TestSessionManagement:
    """세션 관리 테스트"""

    def test_create_session_generates_token(self):
        """세션 생성 시 토큰 생성"""
        with patch('backend.api.auth.postgres_connection') as mock_pg:
            mock_instance = MagicMock()
            mock_pg.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_pg.return_value.__exit__ = MagicMock(return_value=False)

            from backend.api.auth import create_session
            session_id = create_session({"id": "user_123", "email": "test@example.com"})

            assert session_id is not None
            assert len(session_id) == 64  # token_hex(32) = 64 chars

    def test_get_session_returns_none_for_empty(self):
        """빈 세션 ID는 None 반환"""
        from backend.api.auth import get_session
        assert get_session("") is None
        assert get_session(None) is None

    def test_delete_session_handles_empty(self):
        """빈 세션 ID 삭제 시 에러 없음"""
        from backend.api.auth import delete_session
        # 에러 없이 실행되어야 함
        delete_session("")
        delete_session(None)
