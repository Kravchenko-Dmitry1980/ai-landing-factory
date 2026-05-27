"""API tests: export theme profiles with synthetic fixture (no ENDO project)."""

import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.style_config import LandingStyleConfigModel, LandingStyleProfile, ThemeTokensModel
from tests.fixtures.export_contract_fixture import make_export_fixture, patch_repo_with_fixture


def _client_with_fixture(style_config=None, presentation_style="university_platform"):
    project_id, contract, landing = make_export_fixture(
        style_config=style_config,
        presentation_style=presentation_style,
    )
    mock_repo = AsyncMock()
    patch_repo_with_fixture(mock_repo, project_id, contract, landing)
    return TestClient(app), project_id, mock_repo


def test_export_html_university_theme_query():
    client, project_id, mock_repo = _client_with_fixture()
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo), patch(
        "app.services.export.styled_html_exporter.ContractRepository",
        return_value=mock_repo,
    ):
        response = client.get(
            f"/api/v1/projects/{project_id}/export/html",
            params={"theme": "university_platform"},
        )
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "body class='theme-university_platform'" in html
    assert "--alf-accent:" in html or "--accent:" in html.lower()


def test_export_html_default_university_platform():
    client, project_id, mock_repo = _client_with_fixture()
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo), patch(
        "app.services.export.styled_html_exporter.ContractRepository",
        return_value=mock_repo,
    ):
        response = client.get(f"/api/v1/projects/{project_id}/export/html")
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "body class='theme-university_platform'" in html
    assert "scroll-behavior: smooth" in html


def test_export_html_tech_theme_query():
    client, project_id, mock_repo = _client_with_fixture()
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo), patch(
        "app.services.export.styled_html_exporter.ContractRepository",
        return_value=mock_repo,
    ):
        response = client.get(
            f"/api/v1/projects/{project_id}/export/html",
            params={"theme": "tech"},
        )
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "body class='theme-tech'" in html
    assert "--alf-bg:" in html


def test_export_html_bold_theme_query():
    client, project_id, mock_repo = _client_with_fixture()
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo), patch(
        "app.services.export.styled_html_exporter.ContractRepository",
        return_value=mock_repo,
    ):
        response = client.get(
            f"/api/v1/projects/{project_id}/export/html",
            params={"theme": "bold"},
        )
    html = response.json()["html"]
    assert "body class='theme-bold'" in html


def test_export_html_custom_style_config_tokens():
    client, project_id, mock_repo = _client_with_fixture()
    style_config = {
        "profile": "custom",
        "custom_style_prompt": "dark blue 3d",
        "theme_tokens": {
            "color_scheme": "dark",
            "accent": "blue",
            "hero_mode": "future_3d",
        },
    }
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo), patch(
        "app.services.export.styled_html_exporter.ContractRepository",
        return_value=mock_repo,
    ):
        response = client.get(
            f"/api/v1/projects/{project_id}/export/html",
            params={"style_config": json.dumps(style_config)},
        )
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "body class='theme-custom'" in html
    assert "hero--future-3d" in html
    assert "<script>" not in html
    assert "dark blue 3d" not in html


def test_export_persisted_tech_style_config():
    cfg = LandingStyleConfigModel(profile=LandingStyleProfile.TECH)
    client, project_id, mock_repo = _client_with_fixture(style_config=cfg, presentation_style="tech")
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo), patch(
        "app.services.export.styled_html_exporter.ContractRepository",
        return_value=mock_repo,
    ):
        response = client.get(f"/api/v1/projects/{project_id}/export/html")
    html = response.json()["html"]
    assert "body class='theme-tech'" in html
