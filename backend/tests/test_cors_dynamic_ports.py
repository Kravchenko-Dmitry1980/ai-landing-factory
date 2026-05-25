"""CORS tests for dynamic dev frontend ports (start_dev.ps1 range)."""

from fastapi.testclient import TestClient

from app.main import app


def test_cors_preflight_localhost_3004():
    client = TestClient(app)
    response = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "http://localhost:3004",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in (200, 204), response.text
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3004"
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods.upper()


def test_cors_preflight_127_0_0_1_3004():
    client = TestClient(app)
    response = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "http://127.0.0.1:3004",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in (200, 204), response.text
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:3004"


def test_cors_preflight_rejects_evil_origin():
    client = TestClient(app)
    response = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400


def test_post_projects_from_localhost_3004():
    client = TestClient(app)
    response = client.post(
        "/api/v1/projects",
        json={"name": "CORS dynamic port test", "description": None},
        headers={"Origin": "http://localhost:3004"},
    )
    assert response.status_code == 201, response.text
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3004"
