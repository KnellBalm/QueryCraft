import logging
import os
import sys
import pytest
import importlib
from unittest import mock
from fastapi.testclient import TestClient

def get_app_with_env(env_value):
    """Reload backend.main with the specified ENV variable."""
    with mock.patch.dict(os.environ, {"ENV": env_value}):
        if 'backend.main' in sys.modules:
            import backend.main
            importlib.reload(backend.main)
        else:
            if os.getcwd() not in sys.path:
                sys.path.append(os.getcwd())
            import backend.main
        return backend.main.app

class TestCORSLogging:

    def test_cors_logging_success(self, caplog):
        """Test that CORS requests are logged and valid responses don't trigger warnings."""
        caplog.set_level(logging.INFO)
        # Load app in production mode to enable strict CORS
        app = get_app_with_env("production")
        client = TestClient(app)
        origin = "https://query-craft-frontend-758178119666.us-central1.run.app"

        response = client.get(
            "/auth/me",
            headers={"Origin": origin}
        )

        # Check that we logged the request
        # Note: caplog captures logs from all loggers, including backend.middleware.cors
        found_request_log = False
        for record in caplog.records:
            if "CORS Request: Origin=" in record.message and origin in record.message:
                found_request_log = True
                break

        assert found_request_log, "Did not find CORS Request log"

        # Check that we did NOT log a warning (header missing)
        assert "CORS Response Missing Header" not in caplog.text

        # Verify header is actually present
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == origin

    def test_cors_logging_missing_header_warning(self, caplog):
        """Test that missing headers trigger a warning log."""
        caplog.set_level(logging.WARNING)
        # Load app in production mode
        app = get_app_with_env("production")
        client = TestClient(app)
        origin = "https://evil-site.com"

        # This origin is NOT allowed, so CORS middleware will NOT add the header.
        # But our logging middleware sees an Origin header in request, and NO header in response.
        # So it SHOULD log a warning.

        response = client.get(
            "/auth/me",
            headers={"Origin": origin}
        )

        assert "CORS Response Missing Header" in caplog.text
        assert f"Origin={origin}" in caplog.text

        # Verify header is indeed missing
        assert "access-control-allow-origin" not in response.headers
