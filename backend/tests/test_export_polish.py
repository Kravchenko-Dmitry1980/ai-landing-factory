"""Tests for HTML export polish: tagline, truncation, team cards."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

import pytest

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.export.export_tagline import resolve_tagline
from app.services.export.export_theme import ExportTheme
from app.services.export.html_bullet_utils import (
    format_more_count,
    limit_bullets,
    truncate_sentence_safe,
)
from app.services.export.styled_html_exporter import StyledHtmlExporter
from tests.test_styled_html_exporter import FIXTURE, _FakeRepo

BROKEN_ENDING_RE = re.compile(
    r"\b(?:с|для|по|и|в|на|к|из|от|до|при|через|между|над|под)\s*</li>",
    re.I,
)


@pytest.fixture
def endocrinology_contract():
    text = FIXTURE.read_text(encoding="utf-8")
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="Ленд проекта Эндокринология.docx",
                file_type="docx",
                extracted_text=text,
            )
        ],
        extracted_at=utc_now(),
    )
    builder = ContractBuilderService.__new__(ContractBuilderService)
    from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
    from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector
    from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser

    builder._detector = LandingDocumentDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._completeness_gate = ContractCompletenessGate()
    return builder.build(extraction)


def test_resolve_tagline_replaces_duplicate_title() -> None:
    result = resolve_tagline("Эндокринология+", "Эндокринология+", None, "medical_ai")
    assert result != "Эндокринология+"
    assert "AI-экосистема" in result


def test_resolve_tagline_keeps_unique_tagline() -> None:
    custom = "Платформа поддержки клинических решений"
    assert resolve_tagline("Эндокринология+", custom, None, None) == custom


def test_truncate_sentence_safe_avoids_preposition_endings() -> None:
    long_text = (
        "Разработка удобной навигации и взаимодействия с пользователем "
        "системы для врачей и медицинского персонала в клинике"
    )
    result = truncate_sentence_safe(long_text, max_chars=45)
    assert not result.endswith(" с")
    assert not result.endswith(" для")
    assert "…" in result or len(result) <= 45

    assert truncate_sentence_safe("Короткий пункт.", 240) == "Короткий пункт."


def test_truncate_sentence_safe_does_not_cut_mid_word() -> None:
    text = "Аналитика данных и построение отчётов для клиники"
    result = truncate_sentence_safe(text, max_chars=30)
    assert " " in result or len(text) <= 30
    assert not result.endswith(" отч")


def test_format_more_count_grammar() -> None:
    assert format_more_count(1) == "+ ещё 1 пункт"
    assert format_more_count(2) == "+ ещё 2 пункта"
    assert format_more_count(3) == "+ ещё 3 пункта"
    assert format_more_count(4) == "+ ещё 4 пункта"
    assert format_more_count(5) == "+ ещё 5 пунктов"
    assert format_more_count(11) == "+ ещё 11 пунктов"
    assert format_more_count(21) == "+ ещё 21 пункт"


def test_limit_bullets() -> None:
    shown, remaining = limit_bullets(["a", "b", "c", "d", "e", "f"], max_visible=4)
    assert shown == ["a", "b", "c", "d"]
    assert remaining == 2


@pytest.mark.asyncio
async def test_university_export_preserves_names_and_polish(endocrinology_contract) -> None:
    exporter = StyledHtmlExporter(_FakeRepo(endocrinology_contract))
    html = await exporter.to_html(
        endocrinology_contract.project_id,
        theme=ExportTheme.UNIVERSITY_PLATFORM,
    )

    assert "Кравченко Дмитрий" in html
    assert "Малицкий Андрей" in html
    assert "theme-university_platform" in html
    assert "--bg: #ffffff" in html
    assert "--bg: #0f1419" not in html
    assert "● ●" not in html
    assert "+ ещё 1 пунктов" not in html
    assert "+ ещё 2 пунктов" not in html
    assert not BROKEN_ENDING_RE.search(html)
    assert "<p class='tagline'>Эндокринология+</p>" not in html
    assert "AI-экосистема для клинической аналитики" in html
    assert "team-intro" in html
