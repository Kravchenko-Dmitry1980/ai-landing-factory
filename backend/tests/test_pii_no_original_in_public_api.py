"""API must never expose original PII values in public pii-report."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core import dependencies as deps
from app.main import app
from app.repositories.contract_repository import ContractRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction

SENSITIVE = (
    "Кравченко Дмитрий Александрович — тимлид\n"
    "Email: alex.dreval@secret.org\n"
    "Тел: +7 999 123-45-67\n"
)


def _settings(tmp_path) -> Settings:
    s = Settings(
        data_dir=tmp_path / "data",
        uploads_dir=tmp_path / "data" / "uploads",
        contracts_dir=tmp_path / "data" / "contracts",
        extractions_dir=tmp_path / "data" / "extractions",
        privacy_mode="hybrid_safe",
        enable_pii_detection=True,
    )
    for p in (
        s.data_dir,
        s.uploads_dir,
        s.contracts_dir,
        s.extractions_dir,
        s.pii_reports_dir,
        s.pii_safe_payloads_dir,
    ):
        p.mkdir(parents=True, exist_ok=True)
    return s


@pytest.fixture
def client(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    monkeypatch.setattr(deps, "settings", settings)
    monkeypatch.setattr("app.config.settings", settings)
    monkeypatch.setattr("app.api.v1.uploads.settings", settings)
    monkeypatch.setattr(
        "app.api.v1.uploads._project_repo",
        ProjectRepository(settings),
    )
    monkeypatch.setattr(
        "app.api.v1.projects._project_repo",
        ProjectRepository(settings),
    )
    deps.get_settings.cache_clear()
    monkeypatch.setattr(deps, "get_settings", lambda: settings)
    with TestClient(app) as c:
        yield c, settings


def _seed_extraction(settings: Settings, text: str):
    async def _run():
        project = await ProjectRepository(settings).create("PII test", None)
        repo = ContractRepository(settings)
        extraction = ExtractionResult(
            project_id=project.id,
            payload=ExtractionPayload(),
            files=[
                FileExtraction(
                    filename="brief.docx",
                    file_type="docx",
                    extracted_text=text,
                )
            ],
            extracted_at=datetime.now(timezone.utc),
        )
        await repo.save_extraction(extraction)
        return project.id

    return asyncio.run(_run())


def test_pii_report_api_no_original_values(client):
    c, settings = client
    project_id = _seed_extraction(settings, SENSITIVE)

    prescan = c.post(f"/api/v1/projects/{project_id}/pii-prescan")
    assert prescan.status_code == 200

    response = c.get(f"/api/v1/projects/{project_id}/pii-report")
    assert response.status_code == 200
    body = response.json()
    raw = response.text.lower()

    forbidden = [
        "alex.dreval@secret.org",
        "999 123-45-67",
        '"original"',
        "original_hash",
    ]
    for token in forbidden:
        assert token not in raw
    assert "alex.dreval@" not in raw

    for ent in body.get("entities", []):
        assert "original" not in ent
        assert ent.get("placeholder", "").startswith("[")


def test_safe_cloud_payload_api_no_raw_values(client):
    c, settings = client
    project_id = _seed_extraction(settings, SENSITIVE)
    c.post(f"/api/v1/projects/{project_id}/pii-prescan")

    response = c.get(f"/api/v1/projects/{project_id}/safe-cloud-payload")
    assert response.status_code == 200
    data = response.json()
    preview = data.get("preview_text_redacted", "").lower()
    assert "alex.dreval" not in preview
    assert "999 123" not in preview or "[phone" in preview
    assert data.get("safe_for_cloud") is True
