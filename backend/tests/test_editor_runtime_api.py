from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services.export import wow_bundle_exporter
from app.services.export.wow_bundle_data import build_wow_bundle_data
from tests.fixtures.export_contract_fixture import (
    make_wow_indlab_fixture,
    patch_repo_with_fixture,
)


def test_get_project_returns_404_for_missing_project() -> None:
    client = TestClient(app)
    response = client.get(f"/api/v1/projects/{uuid4()}")
    assert response.status_code == 404
    assert "Project not found" in response.text


def test_export_wow_bundle_returns_503_when_dist_wow_missing(tmp_path: Path) -> None:
    project_id, contract, landing = make_wow_indlab_fixture()

    class _Repo:
        pass

    repo = _Repo()
    patch_repo_with_fixture(repo, project_id, contract, landing)
    missing_assets = tmp_path / "missing-dist-wow" / "assets"

    with patch("app.api.v1.projects.get_contract_repository", return_value=repo), patch.object(
        wow_bundle_exporter,
        "DEFAULT_ASSETS_DIR",
        missing_assets,
    ):
        client = TestClient(app)
        response = client.get(f"/api/v1/projects/{project_id}/export/wow-bundle")

    assert response.status_code == 503
    assert "npm run build:wow-bundle" in response.text


def test_wow_bundle_data_accepts_legacy_contract_without_p7_fields() -> None:
    _, contract, _ = make_wow_indlab_fixture()
    legacy_contract = contract.model_copy(
        update={
            "style_config": None,
            "presentation_style": None,
            "visual_assets": [],
        }
    )

    payload = build_wow_bundle_data(legacy_contract)
    assert payload["project"]["title"]
    assert isinstance(payload["metrics"], list)
