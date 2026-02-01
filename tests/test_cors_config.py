
import os
import sys
import pytest
from unittest import mock
from fastapi.testclient import TestClient

class TestCORSConfig:
    """Test CORS configuration for the backend."""

    @pytest.fixture(autouse=True)
    def setup_cors_env(self):
        """
        Setup environment variables for CORS testing and reload the app.
        We need to ensure ENV is production to test the production CORS logic.
        Using mock.patch.dict ensures this is isolated to this test class.
        """
        with mock.patch.dict(os.environ, {"ENV": "production"}):
            # We need to reload the app or at least ensuring the logic reads the new env
            # consistently. Since backend.main executes at import time, we might need
            # to reload it or structure the test to import inside the mock context.

            # Unload backend.main if it's already imported to force re-execution of lifespan/middleware logic
            if "backend.main" in sys.modules:
                del sys.modules["backend.main"]

            from backend.main import app
            self.app = app
            yield

    def test_cors_specific_origin_allowed(self):
        """
        Verify that the specific frontend origin reported in the issue is allowed.
        Origin: https://query-craft-frontend-758178119666.us-central1.run.app
        """
        origin = "https://query-craft-frontend-758178119666.us-central1.run.app"
        client = TestClient(self.app)

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
        response = client.get(
            "/auth/me",
            headers={"Origin": origin}
        )
        assert response.headers.get("access-control-allow-origin") == origin
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_cors_cloud_run_domain_regex(self):
        """Verify that other Cloud Run domains matching the regex are also allowed."""
        origin = "https://query-craft-frontend-random-hash.a.run.app"
        client = TestClient(self.app)

        response = client.options(
            "/auth/me",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin

    def test_cors_origin_with_trailing_slash(self):
        """Verify that an origin with a trailing slash is allowed (via regex)."""
        origin = "https://query-craft-frontend-758178119666.us-central1.run.app/"
        client = TestClient(self.app)

        response = client.options(
            "/auth/me",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin

    def test_cors_disallowed_origin(self):
        """Verify that a random origin is NOT allowed."""
        origin = "https://evil-site.com"
        client = TestClient(self.app)

        response = client.options(
            "/auth/me",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            }
        )
        assert "access-control-allow-origin" not in response.headers

    def test_path_rewrite_does_not_break_cors(self):
        """
        Verify that PathRewriteMiddleware (which rewrites /auth/me to /api/auth/me)
        does not interfere with CORS headers.
        """
        origin = "https://query-craft-frontend-758178119666.us-central1.run.app"
        client = TestClient(self.app)

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
