import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.config import Settings
from app.repositories.contract_repository import ContractRepository
from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.models.domain import utc_now
from app.services.semantic.domain_classifier import classify_domain
from app.services.semantic.fallback_generator import generate_fallback_semantic
from app.services.semantic.generator import SemanticGenerationEngine
from app.services.semantic.hallucination_guard import guard_hallucinations
from app.services.semantic.semantic_validator import validate_semantic_llm_output


def _contract() -> LandingContract:
    pid = uuid4()
    return LandingContract(
        project_id=pid,
        style=LandingStylePreset.MINIMAL,
        title="AI Landing Factory",
        client="ACME Corp",
        blocks=[
            LandingBlock(key="essence", title="Essence", content="Platform for enterprise AI landings", bullets=[]),
            LandingBlock(key="tasks", title="Tasks", content="", bullets=["Build pipeline", "Validate PII"]),
            LandingBlock(key="results", title="Results", content="", bullets=["MVP delivered"]),
            LandingBlock(key="team", title="Team", content="", bullets=["Product Owner", "Tech Lead"]),
        ],
        updated_at=utc_now(),
    )


def test_domain_classifier_medical_signals():
    c = _contract()
    c.blocks[0].content = "Clinical patient monitoring system for hospital workflow"
    result = classify_domain(c)
    assert result.domain.value == "medical"
    assert result.confidence > 0.4


def test_fallback_generates_sections():
    semantic = generate_fallback_semantic(_contract())
    assert len(semantic.sections) >= 3
    assert semantic.metadata.fallback_used is True
    assert semantic.narrative.problem or semantic.narrative.system


def test_no_fabricated_metrics_removed():
    contract = _contract()
    semantic = generate_fallback_semantic(contract)
    semantic.sections[0].metrics = ["99.9% uptime", "500 users"]
    report = guard_hallucinations(semantic, contract)
    assert any("Unverified metric" in w for w in report.warnings)
    assert not any("99.9%" in m for s in report.adjusted_sections for m in s.metrics)


def test_no_fabricated_team_removed():
    contract = _contract()
    semantic = generate_fallback_semantic(contract)
    for s in semantic.sections:
        if str(s.section_type) == "team" or getattr(s.section_type, "value", "") == "team":
            s.bullets = ["Totally Unknown Person XYZ"]
    report = guard_hallucinations(semantic, contract)
    assert any("team" in w.lower() or "Unknown" in w for w in report.warnings)


def test_missing_data_propagation():
    contract = _contract()
    contract.blocks = []
    semantic = generate_fallback_semantic(contract)
    assert semantic.metadata.missing_fields


def test_semantic_structure_validation():
    contract = _contract()
    raw = {
        "project_id": str(contract.project_id),
        "domain": "enterprise",
        "layout_preset": "architecture_first",
        "style_profile": "enterprise",
        "narrative": {"problem": "x", "system": "y"},
        "sections": [
            {
                "section_type": "architecture",
                "title": "Arch",
                "narrative": "From contract",
                "bullets": [],
                "metrics": [],
                "confidence": {"overall": 0.8},
                "source_keys": ["inputs"],
            }
        ],
        "metadata": {"missing_fields": ["team"], "assumptions": []},
    }
    parsed = validate_semantic_llm_output(raw, project_id=contract.project_id)
    assert parsed.sections[0].title == "Arch"
    assert "team" in parsed.metadata.missing_fields


@pytest.fixture
def engine(tmp_path):
    settings = Settings(
        data_dir=tmp_path / "data",
        uploads_dir=tmp_path / "data" / "uploads",
        contracts_dir=tmp_path / "data" / "contracts",
        extractions_dir=tmp_path / "data" / "extractions",
        semantic_generation_enabled=True,
        semantic_use_llm=False,
        llm_enabled=False,
    )
    for p in (settings.data_dir, settings.contracts_dir, settings.extractions_dir):
        p.mkdir(parents=True, exist_ok=True)
    repo = ContractRepository(settings)
    return SemanticGenerationEngine(settings, repo), repo


def test_engine_fallback_pipeline(engine):
    svc, repo = engine
    contract = _contract()
    asyncio.run(repo.save_contract(contract))
    result = asyncio.run(svc.generate(contract.project_id))
    assert result.semantic.sections
    assert result.landing.blocks
    assert "fallback" in result.message.lower() or result.semantic.metadata.fallback_used
