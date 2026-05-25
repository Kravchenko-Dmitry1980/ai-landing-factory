"""Field assembler unit tests."""

from pathlib import Path
from uuid import uuid4

import pytest

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.evidence.evidence_extractor import EvidenceExtractor
from app.services.evidence.field_assembler import FieldAssembler
from app.services.evidence.field_candidates import is_generic_title
from app.services.evidence.field_evidence_builder import FieldEvidenceBuilder
from app.services.evidence.source_inventory import SourceInventoryBuilder

TELEGRAM_FIXTURE = Path(__file__).parent / "fixtures" / "telegram_analytics_presentation.txt"


def _field_map(text: str, filename: str = "deck.pptx", file_type: str = "pptx"):
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename=filename,
                file_type=file_type,
                extracted_text=text,
                metadata={},
            )
        ],
        extracted_at=utc_now(),
    )
    inventory = SourceInventoryBuilder().build(extraction)
    items = EvidenceExtractor().extract(extraction, inventory)
    return FieldEvidenceBuilder().build(items, inventory)


def test_title_from_project_line() -> None:
    text = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    fe = _field_map(text)
    assembler = FieldAssembler()
    title, _ = assembler.assemble_title(fe.get("title"))
    assert title
    assert not is_generic_title(title)
    assert "Интеллектуальный агрегатор" in title


def test_timeline_extracted() -> None:
    text = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    fe = _field_map(text)
    timeline, _ = FieldAssembler().assemble_timeline(fe.get("timeline"))
    assert timeline
    assert "01.09" in timeline


def test_essence_not_only_slide_one() -> None:
    text = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    fe = _field_map(text)
    assembler = FieldAssembler()
    title, _ = assembler.assemble_title(fe.get("title"))
    essence, _ = assembler.assemble_essence(
        fe.get("essence"),
        title=title,
        tech_evidence=fe.get("tech_stack"),
        modules_evidence=fe.get("modules"),
        purpose_evidence=fe.get("purpose"),
    )
    assert len(essence) >= 300
    assert not essence.strip().lower().startswith("slide 1")


def test_technologies_grouped() -> None:
    text = TELEGRAM_FIXTURE.read_text(encoding="utf-8")
    fe = _field_map(text)
    stack, _ = FieldAssembler().assemble_tech_stack(fe.get("tech_stack"))
    flat = [t for vals in stack.values() for t in vals]
    assert "Qdrant" in flat
    assert "BERTopic" in flat
    assert "Neo4j" in flat


def test_multi_file_merge() -> None:
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="presentation.pptx",
                file_type="pptx",
                extracted_text=(
                    "Slide 1:\nПроект:\nСистема мониторинга Alpha\n\n"
                    "Slide 2:\nЦели проекта\nАвтоматизировать сбор метрик."
                ),
                metadata={},
            ),
            FileExtraction(
                filename="tech_spec.docx",
                file_type="docx",
                extracted_text=(
                    "Техническое задание\nВходные данные\n• Логи сервисов\n• Метрики Prometheus\n"
                    "Выходные данные\n• Дашборд Grafana\n• REST API\n"
                    "Используемый стек: Python, FastAPI, PostgreSQL"
                ),
                metadata={},
            ),
            FileExtraction(
                filename="team.txt",
                file_type="txt",
                extracted_text="Команда проекта\nТимлид: Иванов Иван Иванович\n",
                metadata={},
            ),
            FileExtraction(
                filename="report.pdf",
                file_type="pdf",
                extracted_text=(
                    "Отчёт по проекту\nРезультаты\n• Внедрён прототип\n• Сокращено время анализа\n"
                    "Рекомендации\n• Масштабировать на все сервисы\n• Добавить алерты"
                ),
                metadata={},
            ),
        ],
        extracted_at=utc_now(),
    )
    inventory = SourceInventoryBuilder().build(extraction)
    items = EvidenceExtractor().extract(extraction, inventory)
    fe = FieldEvidenceBuilder().build(items, inventory)
    assembled, _ = FieldAssembler().assemble_all(fe, inventory)

    assert "Alpha" in str(assembled.get("title"))
    assert assembled.get("inputs")
    assert len(assembled["inputs"]) >= 2
    assert assembled.get("outputs")
    assert assembled.get("team")
    assert assembled.get("results")
