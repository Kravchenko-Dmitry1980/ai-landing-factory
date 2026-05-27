"""Style config persistence and export safety."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
import pytest

from app.schemas.style_config import (
    LandingStyleConfigModel,
    LandingStyleProfile,
    ThemeTokensModel,
    default_style_config,
)
from app.services.export.styled_html_exporter import StyledHtmlExporter
from tests.fixtures.export_contract_fixture import make_export_fixture, patch_repo_with_fixture


def test_default_style_config_is_university():
    cfg = default_style_config()
    assert cfg.profile == LandingStyleProfile.UNIVERSITY_PLATFORM


def test_new_contract_fixture_has_university_default():
    _, contract, _ = make_export_fixture(style_config=default_style_config())
    assert contract.style_config is not None
    assert contract.style_config.profile == LandingStyleProfile.UNIVERSITY_PLATFORM


def test_patch_style_config_persists_tech():
    project_id, contract, landing = make_export_fixture()
    mock_repo = AsyncMock()
    mock_repo.get_contract = AsyncMock(return_value=contract)
    mock_repo.save_contract = AsyncMock(side_effect=lambda c: setattr(contract, "style_config", c.style_config))

    saved: list[LandingStyleConfigModel] = []

    async def update_contract(pid, blocks=None, **fields):
        if fields.get("style_config"):
            contract.style_config = fields["style_config"]
            saved.append(fields["style_config"])
        contract.version += 1
        return contract

    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo), patch(
        "app.api.v1.projects.get_contract_builder"
    ) as mock_builder:
        builder = MagicMock()
        builder.update_contract = AsyncMock(side_effect=update_contract)
        mock_builder.return_value = builder
        client = TestClient(app)
        response = client.patch(
            f"/api/v1/projects/{project_id}/style-config",
            json={"profile": "tech"},
        )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["style_config"]["profile"] == "tech"
    assert saved[-1].profile == LandingStyleProfile.TECH


@pytest.mark.asyncio
async def test_export_uses_persisted_tech():
    cfg = LandingStyleConfigModel(profile=LandingStyleProfile.TECH)
    project_id, contract, landing = make_export_fixture(style_config=cfg)
    mock_repo = AsyncMock()
    patch_repo_with_fixture(mock_repo, project_id, contract, landing)
    exporter = StyledHtmlExporter(mock_repo)
    html = await exporter.to_html(project_id)
    assert "theme-tech" in html
    assert "тёмный" not in html


@pytest.mark.asyncio
async def test_custom_prompt_not_in_html():
    cfg = LandingStyleConfigModel(
        profile=LandingStyleProfile.CUSTOM,
        custom_style_prompt='тёмный <script>alert(1)</script>',
        theme_tokens=ThemeTokensModel(
            color_scheme="dark",
            accent="blue",
            hero_mode="future_3d",
        ),
    )
    project_id, contract, landing = make_export_fixture(style_config=cfg)
    mock_repo = AsyncMock()
    patch_repo_with_fixture(mock_repo, project_id, contract, landing)
    exporter = StyledHtmlExporter(mock_repo)
    html = await exporter.to_html(project_id)
    assert "<script>" not in html
    assert "alert(1)" not in html
    assert "theme-custom" in html


def test_query_style_config_override():
    project_id, contract, landing = make_export_fixture(
        style_config=LandingStyleConfigModel(profile=LandingStyleProfile.MINIMAL)
    )
    mock_repo = AsyncMock()
    patch_repo_with_fixture(mock_repo, project_id, contract, landing)
    override = {"profile": "bold", "theme_tokens": {"motion": "expressive"}}
    client = TestClient(app)
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo), patch(
        "app.services.export.styled_html_exporter.ContractRepository",
        return_value=mock_repo,
    ):
        response = client.get(
            f"/api/v1/projects/{project_id}/export/html",
            params={"style_config": json.dumps(override)},
        )
    html = response.json()["html"]
    assert "theme-bold" in html
    assert contract.style_config.profile == LandingStyleProfile.MINIMAL
