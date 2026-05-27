"""Tests for TeamVerificationService."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.fidelity import TeamMember
from app.schemas.team_verification import TeamVerificationStatus
from app.services.team_verification.team_verification_service import TeamVerificationService


@pytest.fixture
def service() -> TeamVerificationService:
    return TeamVerificationService()


def test_exact_trusted_match_verified(service: TeamVerificationService) -> None:
    members = [TeamMember(name="Татьяна Ерюкова", role="Помощник тимлида")]
    report = service.verify(members, known_names=["Татьяна Ерюкова"])
    assert len(report.verified_members) == 1
    assert report.verified_members[0].verification_status == TeamVerificationStatus.verified
    assert report.verified_members[0].raw_name == "Татьяна Ерюкова"


def test_fuzzy_trusted_match_nadezhda(service: TeamVerificationService) -> None:
    members = [
        TeamMember(
            name="Наденда Глазунова",
            role="",
            contributions=[],
        )
    ]
    report = service.verify(
        members,
        known_names=["Надежда Глазунова"],
        extraction=_ocr_extraction_with_name("Наденда Глазунова"),
    )
    cand = report.review_candidates + report.verified_members
    assert cand, "Expected at least one classified candidate"
    best = cand[0]
    assert best.matched_trusted_name == "Надежда Глазунова"
    assert best.match_score is not None and best.match_score >= 0.75
    if best.verification_status == TeamVerificationStatus.verified:
        assert best.corrected_name == "Надежда Глазунова"


def test_no_trusted_source_needs_review(service: TeamVerificationService) -> None:
    members = [TeamMember(name="Наденда Глазунова", role="")]
    report = service.verify(
        members,
        extraction=_ocr_extraction_with_name("Наденда Глазунова"),
    )
    assert not report.verified_members
    assert len(report.review_candidates) == 1
    assert report.review_candidates[0].verification_status == TeamVerificationStatus.needs_review


def test_ocr_garbage_rejected(service: TeamVerificationService) -> None:
    members = [TeamMember(name="Manmusit Apel Аизтольевич", role="")]
    report = service.verify(
        members,
        extraction=_ocr_extraction_with_name("Manmusit Apel Аизтольевич"),
    )
    assert not report.verified_members
    rejected = report.rejected_candidates + report.review_candidates
    assert rejected
    assert rejected[0].verification_status in (
        TeamVerificationStatus.rejected,
        TeamVerificationStatus.needs_review,
    )


def test_mixed_latin_cyrillic_rejected(service: TeamVerificationService) -> None:
    members = [TeamMember(name="John Иванов", role="")]
    report = service.verify(
        members,
        extraction=_ocr_extraction_with_name("John Иванов"),
    )
    assert not report.verified_members


def test_empty_role_ocr_only_needs_review(service: TeamVerificationService) -> None:
    members = [TeamMember(name="Денис Калюаный", role="", contributions=[])]
    report = service.verify(
        members,
        extraction=_ocr_extraction_with_name("Денис Калюаный"),
    )
    assert not report.verified_members
    assert report.review_candidates or report.rejected_candidates


def test_non_ocr_docx_team_verified(service: TeamVerificationService) -> None:
    docx_text = """
Команда проекта
Тимлид: Кравченко Дмитрий
1. Татьяна Ерюкова — помощник тимлида
Архитектура, кластеризация
"""
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="landing.docx",
                file_type="docx",
                extracted_text=docx_text,
            )
        ],
        extracted_at=utc_now(),
    )
    members = [TeamMember(name="Татьяна Ерюкова", role="Помощник тимлида")]
    report = service.verify(members, extraction)
    assert len(report.verified_members) == 1
    assert report.verified_members[0].verification_reason == "trusted_non_ocr_source"


def _ocr_extraction_with_name(name: str) -> ExtractionResult:
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="01_presentation.pptx#slide25.ocr",
                file_type="ocr",
                extracted_text=f"Команда проекта\n{name}\nРоль участника",
                metadata={
                    "is_ocr_derivative": True,
                    "ocr_engine": "easyocr",
                    "ocr_confidence": 0.72,
                    "page_or_slide": 25,
                },
            )
        ],
        extracted_at=utc_now(),
    )
