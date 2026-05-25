"""API tests: theme query propagation for HTML export."""

from fastapi.testclient import TestClient

from app.main import app

ENDO_PROJECT_ID = "55a98f90-73fc-4d26-a477-3c974a0cbeed"


def test_export_html_university_theme_query():
    client = TestClient(app)
    response = client.get(
        f"/api/v1/projects/{ENDO_PROJECT_ID}/export/html",
        params={"theme": "university_platform"},
    )
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "body class='theme-university_platform'" in html
    assert "--bg: #ffffff" in html
    assert "--accent: #7C3AED" in html
    assert "--bg: #0f1419" not in html


def test_export_html_default_enterprise_dark():
    client = TestClient(app)
    response = client.get(f"/api/v1/projects/{ENDO_PROJECT_ID}/export/html")
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "body class='theme-enterprise_dark'" in html
    assert "--bg: #0f1419" in html
    assert "--accent: #3b82f6" in html


def test_export_html_unknown_theme_falls_back_to_enterprise_dark():
    client = TestClient(app)
    response = client.get(
        f"/api/v1/projects/{ENDO_PROJECT_ID}/export/html",
        params={"theme": "neon_hacker"},
    )
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "body class='theme-enterprise_dark'" in html
