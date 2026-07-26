"""Algofusion structured text → LandingContract mapping tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.repositories.contract_repository import ContractRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.export.wow.wow_metrics import extract_wow_metrics
from app.services.export.wow.wow_pipeline import build_pipeline

FIXTURE = Path(__file__).parent / "fixtures" / "algofusion_landing.txt"


def _build_contract():
    text = FIXTURE.read_text(encoding="utf-8")
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="Лендинг_АлгоФьюжн_CV.docx",
                file_type="docx",
                extracted_text=text,
            )
        ],
        extracted_at=datetime.now(timezone.utc),
    )
    # Repository is unused by build(); pass a real instance for constructor.
    from app.config import settings

    builder = ContractBuilderService(ContractRepository(settings))
    return builder.build(extraction)


def test_algofusion_contract_uses_structured_parser() -> None:
    contract = _build_contract()
    assert contract.fidelity is not None
    assert contract.fidelity.parser_mode == "structured"
    assert contract.title and "Computer Vision" in contract.title
    assert contract.client and "АлгоФьюжн" in contract.client
    assert contract.timeline and "2026" in contract.timeline
    assert contract.lead and "Кус" in contract.lead
    assert contract.quote and "цифровой паспорт" in contract.quote.lower()


def test_algofusion_contract_has_team_and_stack() -> None:
    contract = _build_contract()
    assert contract.fidelity is not None
    assert len(contract.fidelity.team_structured) >= 10
    stack_count = sum(len(v) for v in contract.fidelity.tech_stack_grouped.values())
    assert stack_count >= 10
    blocks = {b.key: b for b in contract.blocks}
    assert len(blocks["tasks"].bullets) >= 5
    assert len(blocks["results"].bullets) >= 8
    assert len(blocks["outlook"].bullets) >= 5
    assert len(blocks["tech_stack"].bullets) >= 4
    assert len(blocks["team"].bullets) >= 10


def test_algofusion_metrics_not_zero_and_pipeline_domain() -> None:
    contract = _build_contract()
    metrics = extract_wow_metrics(contract)
    assert len(metrics) >= 8
    values = " ".join(f"{m.label}={m.value}" for m in metrics)
    assert "0 технологий" not in values.lower()
    assert "0 команда" not in values.lower()
    assert not any(m.label == "Команда" and m.value == "0" for m in metrics)
    assert not any(m.label == "Технологий" and m.value == "0" for m in metrics)
    assert any("mAP50" in m.label or m.label == "mAP50" for m in metrics)

    pipeline = build_pipeline(contract)
    titles = " | ".join(n.title for n in pipeline)
    assert "YOLO" in titles
    assert "ByteTrack" in titles or "Compliance" in titles
    assert "CASHIER WATCH" in titles or "UI" in titles
