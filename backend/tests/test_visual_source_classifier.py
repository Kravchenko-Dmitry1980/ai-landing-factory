"""Visual source classifier unit tests (H.9.1)."""

from __future__ import annotations

import pytest

from app.config import settings
from app.schemas.visual_evidence import (
    VisualContentType,
    VisualRouteAction,
    VisualSourceItem,
)
from app.services.visual.visual_source_classifier import VisualSourceClassifier


@pytest.fixture
def classifier() -> VisualSourceClassifier:
    return VisualSourceClassifier()


def _item(**kwargs) -> VisualSourceItem:
    defaults = {
        "source_id": "test#1",
        "filename": "test.pptx",
        "source_type": "pptx",
        "page_or_slide": 1,
    }
    defaults.update(kwargs)
    return VisualSourceItem(**defaults)


def test_team_image_only_slide(classifier: VisualSourceClassifier) -> None:
    item = _item(
        page_or_slide=25,
        text_chars=0,
        image_count=1,
        has_text_layer=False,
        has_images=True,
        title_hint="Команда проекта",
    )
    cls = classifier.classify_item(item)
    assert cls.content_type == VisualContentType.team_slide
    assert cls.route_action == VisualRouteAction.run_ocr_and_mark_vlm_candidate
    assert cls.vlm_candidate is True
    assert "команда проекта" in cls.markers


def test_architecture_slide(classifier: VisualSourceClassifier) -> None:
    item = _item(
        text_chars=120,
        image_count=1,
        has_text_layer=True,
        has_images=True,
        title_hint="Архитектура пайплайна",
        raw_text_preview="Архитектура пайплайна Qdrant BERTopic Neo4j компоненты backend frontend",
    )
    cls = classifier.classify_item(item)
    assert cls.content_type in (
        VisualContentType.architecture_diagram,
        VisualContentType.tech_stack_slide,
    )
    assert cls.vlm_candidate is True


def test_tech_stack_slide(classifier: VisualSourceClassifier) -> None:
    item = _item(
        text_chars=200,
        has_text_layer=True,
        title_hint="Технологический стек",
        raw_text_preview="FastAPI React PostgreSQL Docker Qdrant Neo4j",
    )
    cls = classifier.classify_item(item)
    assert cls.content_type == VisualContentType.tech_stack_slide
    assert cls.route_action == VisualRouteAction.use_text_layer


def test_goals_slide(classifier: VisualSourceClassifier) -> None:
    item = _item(
        title_hint="Цели проекта",
        raw_text_preview="Цели проекта: автоматизация процесса",
        text_chars=80,
        has_text_layer=True,
    )
    cls = classifier.classify_item(item)
    assert cls.content_type == VisualContentType.goals_slide
    assert cls.route_action == VisualRouteAction.use_text_layer


def test_metrics_slide(classifier: VisualSourceClassifier) -> None:
    item = _item(
        title_hint="Метрики и результаты",
        raw_text_preview="Метрики: accuracy 92%, latency <10ms, uptime 99%",
        text_chars=90,
        has_text_layer=True,
        image_count=1,
        has_images=True,
    )
    cls = classifier.classify_item(item)
    assert cls.content_type == VisualContentType.metrics_slide
    assert cls.route_action in (
        VisualRouteAction.use_text_layer,
        VisualRouteAction.mark_vlm_candidate_only,
    )


def test_empty_decorative_image(classifier: VisualSourceClassifier) -> None:
    item = _item(
        text_chars=0,
        image_count=1,
        has_text_layer=False,
        has_images=True,
        extracted_image_bytes=2048,
        title_hint=None,
        raw_text_preview=None,
    )
    cls = classifier.classify_item(item)
    assert cls.content_type in (VisualContentType.generic_image, VisualContentType.unknown)
    assert cls.confidence <= 0.5


def test_route_does_not_execute_vlm(classifier: VisualSourceClassifier) -> None:
    """Routing only marks candidates — no VLM engine is invoked."""
    item = _item(
        page_or_slide=8,
        text_chars=0,
        image_count=1,
        has_images=True,
        title_hint="Архитектура системы",
    )
    cls = classifier.classify_item(item)
    assert cls.vlm_candidate is True
    assert cls.route_action in (
        VisualRouteAction.mark_vlm_candidate_only,
        VisualRouteAction.run_ocr_and_mark_vlm_candidate,
    )


def test_team_with_names_uses_text_layer(classifier: VisualSourceClassifier) -> None:
    item = _item(
        title_hint="Команда проекта",
        raw_text_preview=(
            "Команда проекта\n"
            "Тимлид: Иванов Иван Петрович\n"
            "Помощник тимлида: Петрова Анна Сергеевна\n"
            "Разработчик: Сидоров Петр"
        ),
        text_chars=120,
        has_text_layer=True,
        image_count=0,
        has_images=False,
    )
    cls = classifier.classify_item(item)
    assert cls.content_type == VisualContentType.team_slide
    assert cls.route_action == VisualRouteAction.use_text_layer


def test_unknown_image_only_routes_ocr_when_enabled(
    classifier: VisualSourceClassifier,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ocr_enabled", True)
    item = _item(
        text_chars=0,
        image_count=1,
        has_images=True,
        has_text_layer=False,
    )
    cls = classifier.classify_item(item)
    assert cls.route_action in (
        VisualRouteAction.run_ocr,
        VisualRouteAction.run_ocr_and_mark_vlm_candidate,
        VisualRouteAction.mark_vlm_candidate_only,
    )


def test_visual_evidence_builder_summary() -> None:
    from app.schemas.visual_evidence import VisualClassification, VisualEvidenceReport
    from app.services.visual.visual_evidence_builder import VisualEvidenceBuilder

    item = VisualSourceItem(
        source_id="deck#25",
        filename="deck.pptx",
        source_type="pptx",
        page_or_slide=25,
        text_chars=0,
        image_count=1,
        has_images=True,
        title_hint="Команда проекта",
    )
    cls = VisualClassification(
        item=item,
        content_type=VisualContentType.team_slide,
        confidence=0.91,
        route_action=VisualRouteAction.run_ocr_and_mark_vlm_candidate,
        reason="team markers/image-only",
        markers=["команда проекта"],
        vlm_candidate=True,
    )
    report = VisualEvidenceReport(
        source_count=1,
        visual_items_count=1,
        classifications=[cls],
        vlm_candidates_count=1,
        ocr_candidates_count=1,
    )
    lines = VisualEvidenceBuilder.summarize_report(report)
    assert len(lines) == 1
    assert lines[0].page_or_slide == 25
    assert "team_slide" in VisualEvidenceBuilder.format_summary_line(lines[0])


def test_classify_extraction_skips_ocr_derivatives(
    classifier: VisualSourceClassifier,
) -> None:
    from uuid import uuid4

    from app.models.domain import utc_now
    from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction

    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="ocr_slide_25.txt",
                file_type="ocr",
                extracted_text="Slide 25:\nTeam OCR",
                metadata={"is_ocr_derivative": True},
            ),
            FileExtraction(
                filename="deck.pptx",
                file_type="pptx",
                extracted_text="Slide 1:\nЦели проекта\nАвтоматизация",
                metadata={"slides_count": 1},
            ),
        ],
        extracted_at=utc_now(),
    )
    report = classifier.classify_extraction(extraction)
    assert report.source_count == 1
    assert report.visual_items_count >= 1
