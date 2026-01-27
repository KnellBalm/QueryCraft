from fastapi.testclient import TestClient
from backend.main import app

def test_cors_specific_origin():
    client = TestClient(app)
    origin = "https://query-craft-frontend-758178119666.us-central1.run.app"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization",
    }

    # Test Preflight (OPTIONS)
    response = client.options("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"

def test_cors_regex_origin():
    client = TestClient(app)
    # A random hypothetical cloud run url that matches regex
    origin = "https://query-craft-frontend-123456.us-west1.run.app"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
    }

    response = client.options("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"
