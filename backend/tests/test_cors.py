"""CORS preflight regression tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_cors_preflight_post_projects_from_localhost_3001():
    client = TestClient(app)
    response = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in (200, 204), response.text
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3001"
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods.upper()


def test_cors_preflight_rejects_unknown_origin():
    client = TestClient(app)
    response = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400


def test_post_projects_json_with_cors_origin():
    client = TestClient(app)
    response = client.post(
        "/api/v1/projects",
        json={"name": "CORS test", "description": None},
        headers={"Origin": "http://localhost:3001"},
    )
    assert response.status_code == 201, response.text
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3001"


def test_get_privacy_still_works_with_cors():
    client = TestClient(app)
    response = client.get(
        "/api/v1/projects/privacy",
        headers={"Origin": "http://localhost:3001"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3001"
