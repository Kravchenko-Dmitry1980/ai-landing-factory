"""API regression tests for Stage C.6 PII Guard Hardening."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core import dependencies as deps
from app.main import app
from app.repositories.contract_repository import ContractRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.analysis.llm_contract_builder import LLMContractBuilderService
from app.services.pipeline.pii_stage import PIIStageService


PII_TEXT = (
    "Кравченко Дмитрий Александрович — тимлид\n"
    "Email: secret.person@example.com\n"
    "Тел: +7 999 123-45-67\n"
)


def _make_settings(tmp_path, privacy_mode: str = "hybrid_safe") -> Settings:
    settings = Settings(
        data_dir=tmp_path / "data",
        uploads_dir=tmp_path / "data" / "uploads",
        contracts_dir=tmp_path / "data" / "contracts",
        extractions_dir=tmp_path / "data" / "extractions",
        privacy_mode=privacy_mode,
        enable_pii_detection=True,
        llm_enabled=True,
        llm_provider="mock",
    )
    for p in (
        settings.data_dir,
        settings.uploads_dir,
        settings.contracts_dir,
        settings.extractions_dir,
        settings.pii_reports_dir,
        settings.pii_safe_payloads_dir,
    ):
        p.mkdir(parents=True, exist_ok=True)
    return settings


@pytest.fixture
def test_settings(tmp_path):
    return _make_settings(tmp_path)


@pytest.fixture
def client(test_settings, monkeypatch):
    monkeypatch.setattr(deps, "settings", test_settings)
    monkeypatch.setattr("app.config.settings", test_settings)
    monkeypatch.setattr("app.api.v1.uploads.settings", test_settings)
    monkeypatch.setattr(
        "app.api.v1.uploads._project_repo",
        ProjectRepository(test_settings),
    )
    monkeypatch.setattr(
        "app.api.v1.projects._project_repo",
        ProjectRepository(test_settings),
    )
    deps.get_settings.cache_clear()

    def _settings():
        return test_settings

    monkeypatch.setattr(deps, "get_settings", _settings)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_extraction(repo: ContractRepository, text: str = PII_TEXT) -> ExtractionResult:
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="brief.txt",
                file_type="txt",
                extracted_text=text,
            )
        ],
        extracted_at=datetime.now(timezone.utc),
    )
    asyncio.run(repo.save_extraction(extraction))
    return extraction


# --- 1–2. Route regression: /privacy must not match /{project_id} ---


def test_get_privacy_returns_200_not_422(client):
    """Regression: 'privacy' must not be parsed as UUID project_id."""
    response = client.get("/api/v1/projects/privacy")
    assert response.status_code == 200, response.text
    body = response.json()
    assert "privacy_mode" in body
    assert body["privacy_mode"] in ("hybrid_safe", "local_only", "cloud_unsafe_dev")


def test_get_privacy_cleanup_returns_200(client):
    response = client.post("/api/v1/projects/privacy/cleanup")
    assert response.status_code == 200
    assert "deleted_reports" in response.json()


# --- 3. Public PII report via API ---


def test_pii_report_api_has_no_originals(client, test_settings):
    repo = ContractRepository(test_settings)
    extraction = _seed_extraction(repo)
    asyncio.run(PIIStageService(test_settings).prescan(extraction))
    report, _ = asyncio.run(PIIStageService(test_settings).prescan(extraction))
    asyncio.run(repo.save_pii_report(report))

    response = client.get(f"/api/v1/projects/{extraction.project_id}/pii-report")
    assert response.status_code == 200
    raw = response.text
    assert "secret.person@example.com" not in raw
    assert "Кравченко" not in raw
    body = response.json()
    assert body["has_pii"] is True
    assert "original" not in raw


# --- 4. Safe cloud payload in hybrid_safe ---


def test_safe_cloud_payload_api_no_raw_pii(client, test_settings):
    repo = ContractRepository(test_settings)
    extraction = _seed_extraction(repo)
    report, _ = asyncio.run(PIIStageService(test_settings).prescan(extraction))
    asyncio.run(repo.save_pii_report(report))

    response = client.get(
        f"/api/v1/projects/{extraction.project_id}/safe-cloud-payload"
    )
    assert response.status_code == 200
    body = response.json()
    preview = body["preview_text_redacted"]
    assert "secret.person@example.com" not in preview
    assert "Кравченко" not in preview
    assert "+7 999" not in preview
    assert body["safe_for_cloud"] is True


# --- 5. Upload response includes pii_summary ---


def test_upload_response_includes_pii_summary(client, test_settings):
    create = client.post(
        "/api/v1/projects",
        json={"name": "PII test", "description": None},
    )
    assert create.status_code == 201, create.text
    project_id = create.json()["id"]

    files = {"files": ("brief.txt", BytesIO(PII_TEXT.encode("utf-8")), "text/plain")}
    response = client.post(f"/api/v1/projects/{project_id}/upload", files=files)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("pii_summary") is not None
    assert body["pii_summary"]["has_pii"] is True


# --- 6–8. Enrich privacy modes ---


def _enrich_builder(settings: Settings, repo: ContractRepository) -> LLMContractBuilderService:
    heuristic = ContractBuilderService(repo)
    return LLMContractBuilderService(
        settings,
        repo,
        heuristic,
        pii_stage=PIIStageService(settings),
    )


def test_enrich_hybrid_safe_uses_redacted_text(test_settings):
    repo = ContractRepository(test_settings)
    test_settings.privacy_mode = "hybrid_safe"
    test_settings.llm_provider = "mock"
    extraction = _seed_extraction(repo)
    asyncio.run(ContractBuilderService(repo).build_and_save(extraction))

    svc = _enrich_builder(test_settings, repo)
    captured: list[str] = []
    original = svc._build_user_prompt

    def _capture(ext, heuristic):
        prompt = original(ext, heuristic)
        captured.append(prompt)
        return prompt

    svc._build_user_prompt = _capture  # type: ignore[method-assign]
    asyncio.run(svc.enrich(extraction.project_id))

    assert captured
    prompt = captured[0]
    assert "secret.person@example.com" not in prompt
    assert "Кравченко" not in prompt


def test_enrich_local_only_blocks_openai(test_settings):
    repo = ContractRepository(test_settings)
    test_settings.privacy_mode = "local_only"
    test_settings.llm_provider = "openai"
    test_settings.llm_enabled = True
    extraction = _seed_extraction(repo)
    asyncio.run(ContractBuilderService(repo).build_and_save(extraction))

    result = asyncio.run(_enrich_builder(test_settings, repo).enrich(extraction.project_id))
    assert "LOCAL_ONLY" in result.message
    assert result.enrichment.fallback_used is True


def test_enrich_cloud_unsafe_dev_shows_warning(test_settings):
    repo = ContractRepository(test_settings)
    test_settings.privacy_mode = "cloud_unsafe_dev"
    test_settings.llm_provider = "mock"
    extraction = _seed_extraction(repo)
    asyncio.run(ContractBuilderService(repo).build_and_save(extraction))

    result = asyncio.run(_enrich_builder(test_settings, repo).enrich(extraction.project_id))
    assert result.enrichment.cloud_unsafe_warning is True
    assert "CLOUD_UNSAFE_DEV" in result.message


def test_router_registers_privacy_once():
    from app.api.router import api_router

    privacy_get_routes = [
        r
        for r in api_router.routes
        if "GET" in getattr(r, "methods", set())
        and getattr(r, "path", "").endswith("/privacy")
    ]
    assert len(privacy_get_routes) == 1
