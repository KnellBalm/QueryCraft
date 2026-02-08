
import os
import sys
import pytest
from unittest import mock
import importlib
from fastapi.testclient import TestClient

@pytest.fixture
def production_app():
    """Fixture that forces ENV='production' and reloads backend.main app."""
    # Use mock.patch.dict to temporarily change os.environ
    with mock.patch.dict(os.environ, {"ENV": "production", "POSTGRES_DSN": "postgresql://mock_user:mock_pass@localhost:5432/mock_db"}):
        # We need to reload backend.main because the app is created at module level based on ENV
        if 'backend.main' in sys.modules:
            import backend.main
            importlib.reload(backend.main)
        else:
            import backend.main

        yield backend.main.app

    # Cleanup: reload backend.main with original environment (if needed by other tests)
    # Note: Since pytest runs tests in a single process, reloading here is good practice
    # to restore the state for subsequent tests.
    if 'backend.main' in sys.modules:
        import backend.main
        importlib.reload(backend.main)

class TestCORSConfig:
    """Test CORS configuration for the backend."""

    def test_cors_specific_origin_allowed(self, production_app):
        """
        Verify that the specific frontend origin reported in the issue is allowed.
        Origin: https://query-craft-frontend-758178119666.us-central1.run.app
        """
        origin = "https://query-craft-frontend-758178119666.us-central1.run.app"
        client = TestClient(production_app)

        # 1. Test Preflight (OPTIONS)
        response = client.options(
            "/auth/me",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin
        assert response.headers.get("access-control-allow-credentials") == "true"

        # 2. Test GET request
        # /auth/me might return 200 (logged_in=False) or 401 depending on logic, but headers must be present
        response = client.get(
            "/auth/me",
            headers={"Origin": origin}
        )
        assert response.headers.get("access-control-allow-origin") == origin
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_cors_cloud_run_domain_regex(self, production_app):
        """Verify that other Cloud Run domains matching the regex are also allowed."""
        origin = "https://query-craft-frontend-random-hash.a.run.app"
        client = TestClient(production_app)

        response = client.options(
            "/auth/me",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin

    def test_cors_disallowed_origin(self, production_app):
        """Verify that a random origin is NOT allowed."""
        origin = "https://evil-site.com"
        client = TestClient(production_app)

        response = client.options(
            "/auth/me",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            }
        )
        # Standard behavior for disallowed origin in FastAPI CORSMiddleware is
        # usually 200 OK but WITHOUT Access-Control-Allow-Origin header,
        # or sometimes 400.
        # Starlette CORSMiddleware just ignores it and processes request as normal non-CORS,
        # or returns response without CORS headers.

        assert "access-control-allow-origin" not in response.headers

    def test_path_rewrite_does_not_break_cors(self, production_app):
        """
        Verify that PathRewriteMiddleware (which rewrites /auth/me to /api/auth/me)
        does not interfere with CORS headers.
        """
        origin = "https://query-craft-frontend-758178119666.us-central1.run.app"
        client = TestClient(production_app)

        # Send request to /auth/me (rewritten to /api/auth/me)
        response = client.get(
            "/auth/me",
            headers={"Origin": origin}
        )
        assert response.headers.get("access-control-allow-origin") == origin

        # Send request directly to /api/auth/me (no rewrite needed)
        response = client.get(
            "/api/auth/me",
            headers={"Origin": origin}
        )
        assert response.headers.get("access-control-allow-origin") == origin
