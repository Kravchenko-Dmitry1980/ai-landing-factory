import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.config import Settings
from app.repositories.contract_repository import ContractRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.landing_contract import ContractStatus
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.analysis.llm_contract_builder import LLMContractBuilderService
from app.services.analysis.normalization import normalize_llm_output, repair_json_text


def _sample_extraction() -> ExtractionResult:
    pid = uuid4()
    return ExtractionResult(
        project_id=pid,
        payload=ExtractionPayload(
            essence="Суть: AI Landing Factory",
            tasks=["Задача 1"],
            raw_notes=["note"],
        ),
        files=[
            FileExtraction(
                filename="brief.docx",
                file_type="docx",
                extracted_text="Суть проекта: AI Landing Factory\n- Задача первая\nКлиент: ACME",
            )
        ],
        extracted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def builder(tmp_path):
    settings = Settings(
        data_dir=tmp_path / "data",
        uploads_dir=tmp_path / "data" / "uploads",
        contracts_dir=tmp_path / "data" / "contracts",
        extractions_dir=tmp_path / "data" / "extractions",
        llm_enabled=True,
        llm_provider="mock",
    )
    for p in (
        settings.data_dir,
        settings.uploads_dir,
        settings.contracts_dir,
        settings.extractions_dir,
    ):
        p.mkdir(parents=True, exist_ok=True)
    repo = ContractRepository(settings)
    heuristic = ContractBuilderService(repo)
    return LLMContractBuilderService(settings, repo, heuristic), repo


def test_mock_returns_valid_contract(builder):
    svc, repo = builder
    extraction = _sample_extraction()
    asyncio.run(repo.save_extraction(extraction))
    asyncio.run(svc._heuristic.build_and_save(extraction))

    result = asyncio.run(svc.enrich(extraction.project_id))
    assert result.contract.status == ContractStatus.ENRICHED
    assert result.contract.blocks
    assert result.enrichment.fallback_used is False
    assert "essence" in [b.key for b in result.contract.blocks]


def test_missing_fields_preserved(builder):
    svc, repo = builder
    extraction = _sample_extraction()
    extraction.files = []
    extraction.payload.raw_notes = []
    asyncio.run(repo.save_extraction(extraction))
    asyncio.run(svc._heuristic.build_and_save(extraction))

    result = asyncio.run(svc.enrich(extraction.project_id))
    assert result.enrichment.missing_fields


def test_llm_disabled_fallback(builder):
    svc, repo = builder
    svc._settings.llm_enabled = False
    extraction = _sample_extraction()
    asyncio.run(repo.save_extraction(extraction))

    result = asyncio.run(svc.enrich(extraction.project_id))
    assert result.contract.status == ContractStatus.DRAFT_FALLBACK
    assert result.enrichment.fallback_used is True
    assert "disabled" in result.message.lower()


def test_invalid_json_fallback(builder):
    svc, repo = builder
    extraction = _sample_extraction()
    asyncio.run(repo.save_extraction(extraction))
    asyncio.run(svc._heuristic.build_and_save(extraction))

    class BadClient:
        async def generate_json(self, *args, **kwargs):
            return "not-json-at-all"

    svc._resolve_client = lambda _e: BadClient()  # type: ignore[method-assign]

    result = asyncio.run(svc.enrich(extraction.project_id))
    assert result.contract.status == ContractStatus.DRAFT_FALLBACK
    assert result.enrichment.fallback_used is True


def test_source_trace_from_output():
    data = {
        "essence": "Test essence",
        "tasks": [],
        "inputs": [],
        "outputs": [],
        "results": [],
        "stack": [],
        "team": [],
        "confidence": {},
        "missing_fields": [],
        "assumptions": [],
        "source_trace": [
            {"field": "results", "filename": "a.pdf", "evidence": "result line"}
        ],
    }
    out = normalize_llm_output(data)
    assert out.source_trace[0].field == "results"
    assert out.source_trace[0].filename == "a.pdf"


def test_repair_json_strips_markdown():
    raw = '```json\n{"title": "X", "tasks": [], "inputs": [], "outputs": [], "results": [], "stack": [], "team": [], "confidence": {}, "missing_fields": [], "assumptions": [], "source_trace": []}\n```'
    repaired = repair_json_text(raw)
    out = normalize_llm_output(repaired)
    assert out.title == "X"
