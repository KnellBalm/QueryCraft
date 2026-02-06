
import os
import sys
import pytest
from unittest.mock import patch
import importlib
from fastapi.testclient import TestClient

@pytest.fixture(scope="class")
def production_app():
    """
    Sets up the application in production mode for CORS testing.
    Reloads backend.main to apply the configuration.
    Restores the original state afterwards.
    """
    # Use patch.dict to safely modify os.environ for the duration of the fixture
    # We provide a dummy POSTGRES_DSN because config.db might check for it in production
    with patch.dict(os.environ, {
        "ENV": "production",
        "POSTGRES_DSN": "postgresql://dummy:dummy@localhost:5432/dummy"
    }):
        # Import and reload backend.main to apply production CORS settings
        import backend.main
        importlib.reload(backend.main)

        yield backend.main.app

    # Teardown: Reload backend.main to restore it to the state matching the
    # original environment (which is restored by patch.dict automatically)
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
