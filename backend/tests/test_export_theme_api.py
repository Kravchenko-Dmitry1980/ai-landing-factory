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


def test_export_html_default_university_platform():
    client = TestClient(app)
    response = client.get(f"/api/v1/projects/{ENDO_PROJECT_ID}/export/html")
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "body class='theme-university_platform'" in html
    assert "--bg: #ffffff" in html
    assert "--accent: #7C3AED" in html
    assert "scroll-behavior: smooth" in html


def test_export_html_unknown_theme_falls_back_to_university_platform():
    client = TestClient(app)
    response = client.get(
        f"/api/v1/projects/{ENDO_PROJECT_ID}/export/html",
        params={"theme": "neon_hacker"},
    )
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "body class='theme-university_platform'" in html


def test_export_html_custom_style_config_tokens():
    import json

    client = TestClient(app)
    style_config = {
        "profile": "custom",
        "custom_style_prompt": "тёмный синий 3d",
        "theme_tokens": {
            "color_scheme": "dark",
            "accent": "blue",
            "hero_mode": "future_3d",
        },
    }
    response = client.get(
        f"/api/v1/projects/{ENDO_PROJECT_ID}/export/html",
        params={"style_config": json.dumps(style_config)},
    )
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "hero--future-3d" in html
    assert "<script>" not in html
    assert "alert(1)" not in html
