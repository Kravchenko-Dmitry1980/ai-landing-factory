"""WOW exhibition-grade landing export tests (Stage P.7)."""

from __future__ import annotations

import asyncio
import re

from app.schemas.export_mode import Wow3dRuntime
from app.services.export.export_theme import ExportTheme
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.services.export.wow.wow_exporter import WowExportOptions, WowHtmlExporter
from app.services.export.wow.wow_metrics import extract_wow_metrics
from tests.fixtures.export_contract_fixture import (
    make_export_fixture,
    make_university_export_fixture,
    make_wow_indlab_fixture,
)

WOW_CLASSES = ("wow-landing", "wow-cockpit", "wow-metric-panel", "wow-pipeline-map")
EXTERNAL_CDN_RE = re.compile(r'(?:src|href)\s*=\s*["\']https?://', re.I)


class _Repo:
    def __init__(self, contract, landing=None) -> None:
        self._contract = contract
        self._landing = landing

    async def get_contract(self, _pid):
        return self._contract

    async def get_landing(self, _pid):
        return self._landing


def _wow_html(contract, *, runtime=Wow3dRuntime.NONE, demo_url=None, theme=None) -> str:
    exporter = WowHtmlExporter(_Repo(contract))
    return asyncio.run(
        exporter.to_html(
            contract.project_id,
            theme=theme,
            options=WowExportOptions(runtime=runtime, demo_url=demo_url),
        )
    )


def _standard_html(contract, landing, theme=ExportTheme.UNIVERSITY_PLATFORM) -> str:
    exporter = StyledHtmlExporter(_Repo(contract, landing))
    return asyncio.run(exporter.to_html(contract.project_id, theme=theme))


# 1
def test_standard_export_has_no_wow_classes():
    _, contract, landing = make_university_export_fixture()
    html = _standard_html(contract, landing)
    for cls in WOW_CLASSES:
        assert cls not in html
    assert "<a-scene" not in html
    assert 'data-export-mode="wow"' not in html


# 2
def test_wow_export_contains_wow_landing():
    _, contract, _ = make_wow_indlab_fixture()
    html = _wow_html(contract)
    assert "wow-landing" in html
    assert 'data-export-mode="wow"' in html


# 3
def test_wow_export_contains_cockpit_hero():
    _, contract, _ = make_wow_indlab_fixture()
    html = _wow_html(contract)
    assert "wow-hero" in html
    assert "wow-cockpit" in html
    assert "wow-bg-grid" in html
    assert "wow-bg-radar" in html


# 4
def test_wow_export_contains_metric_panel():
    _, contract, _ = make_wow_indlab_fixture()
    html = _wow_html(contract)
    assert "wow-metric-panel" in html


# 5
def test_wow_export_contains_at_least_four_metric_cards():
    _, contract, _ = make_wow_indlab_fixture()
    html = _wow_html(contract)
    assert html.count("wow-metric-card") >= 4


# 6
def test_wow_export_contains_pipeline_map():
    _, contract, _ = make_wow_indlab_fixture()
    html = _wow_html(contract)
    assert "wow-pipeline-map" in html
    assert "wow-pipeline-node" in html
    assert "wow-pipeline-connector" in html


# 7
def test_wow_export_contains_demo_cta():
    _, contract, _ = make_wow_indlab_fixture()
    html = _wow_html(contract)
    assert "wow-demo-cta" in html
    assert "/showcase" in html


# 8
def test_wow_export_no_external_cdn():
    _, contract, _ = make_wow_indlab_fixture()
    html = _wow_html(contract)
    assert not EXTERNAL_CDN_RE.search(html)
    # CSS-only WOW has no scripts at all.
    assert "<script" not in html


# 9
def test_wow_export_escapes_malicious_title():
    _, contract, _ = make_wow_indlab_fixture()
    contract = contract.model_copy(update={"title": "<script>alert('xss')</script>"})
    html = _wow_html(contract)
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


# 10
def test_wow_export_rejects_javascript_demo_url():
    _, contract, _ = make_wow_indlab_fixture()
    html = _wow_html(contract, demo_url="javascript:alert(1)")
    assert "javascript:alert" not in html
    assert "Демо-ссылка не добавлена" in html


# 11
def test_wow_export_with_aframe_uses_local_vendor_runtime():
    _, contract, _ = make_wow_indlab_fixture()
    html = _wow_html(contract, runtime=Wow3dRuntime.AFRAME)
    assert "vendor/aframe/aframe.min.js" in html
    assert "<a-scene" in html
    assert "wow-aframe-hero" in html
    # Local runtime only — never a remote CDN.
    assert not EXTERNAL_CDN_RE.search(html)
    assert "https://aframe.io" not in html


# 12
def test_wow_export_without_aframe_has_no_a_scene():
    _, contract, _ = make_wow_indlab_fixture()
    html = _wow_html(contract, runtime=Wow3dRuntime.NONE)
    assert "<a-scene" not in html
    assert "aframe.min.js" not in html


# 13
def test_tech_profile_wow_has_dark_cockpit_classes():
    _, contract, _ = make_wow_indlab_fixture()  # tech profile
    html = _wow_html(contract, theme=ExportTheme.TECH)
    assert "wow--dark" in html
    assert "wow-profile-tech" in html
    assert "wow-cockpit" in html


# 14
def test_standard_university_export_materially_unchanged():
    _, contract, landing = make_university_export_fixture()
    html = _standard_html(contract, landing)
    assert "body class='theme-university_platform'" in html
    assert "id='hero'" in html
    assert "Команда проекта" in html
    assert "module-card" in html
    for cls in WOW_CLASSES:
        assert cls not in html


# 15
def test_indlab_like_contract_extracts_metrics_37000_17_800_if_present():
    _, contract, _ = make_wow_indlab_fixture()
    metrics = extract_wow_metrics(contract)
    values = " ".join(m.value for m in metrics)
    assert "37 000" in values or "37000" in values
    assert any(m.value.strip().startswith("17") for m in metrics)
    assert "800" in values
    # And they render into the export.
    html = _wow_html(contract)
    assert "800" in html


# 16
def test_generic_contract_gets_fallback_metrics():
    _, contract, _ = make_export_fixture()
    metrics = extract_wow_metrics(contract)
    assert len(metrics) >= 4
    assert any(m.source in ("derived", "fallback") for m in metrics)
    html = _wow_html(contract)
    assert html.count("wow-metric-card") >= 4


# --- API mode routing & validation ---


def _api_client_with_indlab():
    from unittest.mock import AsyncMock

    from fastapi.testclient import TestClient

    from app.main import app
    from tests.fixtures.export_contract_fixture import patch_repo_with_fixture

    project_id, contract, landing = make_wow_indlab_fixture()
    mock_repo = AsyncMock()
    patch_repo_with_fixture(mock_repo, project_id, contract, landing)
    return TestClient(app), project_id, mock_repo


def test_api_wow_mode_returns_wow_html():
    from unittest.mock import patch

    client, project_id, mock_repo = _api_client_with_indlab()
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo):
        response = client.get(
            f"/api/v1/projects/{project_id}/export/html",
            params={"mode": "wow"},
        )
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert 'data-export-mode="wow"' in html
    assert "wow-landing" in html


def test_api_standard_mode_is_default():
    from unittest.mock import patch

    client, project_id, mock_repo = _api_client_with_indlab()
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo), patch(
        "app.services.export.styled_html_exporter.ContractRepository",
        return_value=mock_repo,
    ):
        response = client.get(f"/api/v1/projects/{project_id}/export/html")
    assert response.status_code == 200, response.text
    html = response.json()["html"]
    assert "wow-landing" not in html


def test_api_invalid_mode_returns_400():
    from unittest.mock import patch

    client, project_id, mock_repo = _api_client_with_indlab()
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo):
        response = client.get(
            f"/api/v1/projects/{project_id}/export/html",
            params={"mode": "ultra"},
        )
    assert response.status_code == 400


def test_api_invalid_runtime_returns_400():
    from unittest.mock import patch

    client, project_id, mock_repo = _api_client_with_indlab()
    with patch("app.api.v1.projects.get_contract_repository", return_value=mock_repo):
        response = client.get(
            f"/api/v1/projects/{project_id}/export/html",
            params={"mode": "wow", "wow_3d_runtime": "threejs"},
        )
    assert response.status_code == 400
