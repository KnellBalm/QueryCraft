import logging
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Set ENV to production
os.environ["ENV"] = "production"

try:
    from backend.main import app
except ImportError:
    sys.path.append(os.getcwd())
    from backend.main import app

class TestCORSLogging:

    def test_cors_logging_success(self, caplog):
        """Test that CORS requests are logged and valid responses don't trigger warnings."""
        caplog.set_level(logging.INFO)
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
