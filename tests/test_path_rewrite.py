from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_rewrite_auth_me():
    # This should be rewritten to /api/auth/me
    # Since we don't have a valid session, it should return {"logged_in": False}
    # But crucially, it should NOT return 404
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json() == {"logged_in": False}

def test_direct_api_auth_me():
    # This should work as is
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {"logged_in": False}

def test_rewrite_other_routes():
    # Test verify health route is NOT rewritten (it's not in the list)
    # /health is a valid route
    response = client.get("/health")
    assert response.status_code == 200
    # The status might be unhealthy if DB is not connected, but that's fine for this test
    # We just want to ensure it didn't return 404 (which would happen if rewritten to /api/health)

def test_unknown_route():
    # Test that unknown route returns 404
    response = client.get("/unknown")
    assert response.status_code == 404
