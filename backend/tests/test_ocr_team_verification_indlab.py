"""Indlab OCR team verification integration tests."""

from __future__ import annotations

from uuid import uuid4

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.fidelity import TeamMember
from app.schemas.team_verification import TeamVerificationStatus
from app.services.team_verification.team_verification_service import TeamVerificationService

INDLAB_BAD_OCR = [
    "Наденда Глазунова",
    "Денис Калюаный",
    "Александр Егорсв",
    "Татьяна Залоротец",
]

INDLAB_TRUSTED = [
    "Татьяна Ерюкова",
    "Надежда Глазунова",
    "Егор Быков",
    "Кравченко Дмитрий",
]


def _indlab_ocr_extraction() -> ExtractionResult:
    ocr_text = "Команда проекта\n" + "\n".join(INDLAB_BAD_OCR)
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="01_presentation.pptx#slide25.ocr",
                file_type="ocr",
                extracted_text=ocr_text,
                metadata={
                    "is_ocr_derivative": True,
                    "ocr_engine": "easyocr",
                    "ocr_confidence": 0.75,
                    "page_or_slide": 25,
                },
            )
        ],
        extracted_at=utc_now(),
    )


def test_indlab_bad_ocr_without_roster_needs_review() -> None:
    service = TeamVerificationService()
    members = [TeamMember(name=n, role="") for n in INDLAB_BAD_OCR]
    report = service.verify(members, _indlab_ocr_extraction())
    assert not report.verified_members
    assert len(report.review_candidates) + len(report.rejected_candidates) == len(INDLAB_BAD_OCR)


def test_indlab_nadezhda_corrected_with_trusted_roster() -> None:
    service = TeamVerificationService()
    members = [TeamMember(name="Наденда Глазунова", role="Участник")]
    report = service.verify(
        members,
        _indlab_ocr_extraction(),
        known_names=INDLAB_TRUSTED,
    )
    all_cands = report.verified_members + report.review_candidates
    nadezhda = next(c for c in all_cands if "Глазунова" in c.raw_name)
    assert nadezhda.matched_trusted_name == "Надежда Глазунова"
    assert nadezhda.match_score is not None and nadezhda.match_score >= 0.75


def test_indlab_zalorotets_not_verified_against_eryukova() -> None:
    service = TeamVerificationService()
    members = [TeamMember(name="Татьяна Залоротец", role="")]
    report = service.verify(
        members,
        _indlab_ocr_extraction(),
        known_names=["Татьяна Ерюкова"],
    )
    assert not report.verified_members
    cand = (report.review_candidates + report.rejected_candidates)[0]
    assert cand.verification_status != TeamVerificationStatus.verified
