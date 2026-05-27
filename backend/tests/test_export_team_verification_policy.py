"""Tests for public export team verification policy."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.fidelity import FidelityMetadata, TeamMember
from app.schemas.landing_contract import ContractStatus, LandingBlock, LandingContract
from app.schemas.team_verification import (
    TeamCandidateQuality,
    TeamVerificationMetrics,
    TeamVerificationReport,
    TeamVerificationStatus,
)
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.services.orchestration.agents.export_guard_agent import guard_team_for_export
from app.services.team_verification.export_policy import filter_team_for_public_export


BAD_OCR_NAMES = [
    "Наденда Глазунова",
    "Денис Калюаный",
    "Александр Егорсв",
    "Татьяна Залоротец",
]


def _make_report(
    verified: list[str],
    review: list[str],
    ocr_count: int = 0,
) -> TeamVerificationReport:
    return TeamVerificationReport(
        verified_members=[
            TeamCandidateQuality(
                raw_name=n,
                verification_status=TeamVerificationStatus.verified,
                verification_reason="test",
                name_quality_score=0.9,
            )
            for n in verified
        ],
        review_candidates=[
            TeamCandidateQuality(
                raw_name=n,
                verification_status=TeamVerificationStatus.needs_review,
                verification_reason="ocr_only_unverified",
                source_is_ocr=True,
                name_quality_score=0.6,
            )
            for n in review
        ],
        metrics=TeamVerificationMetrics(
            ocr_candidates=ocr_count,
            verified_count=len(verified),
            needs_review_count=len(review),
        ),
    )


def test_verified_ocr_member_appears_in_export() -> None:
    members = [TeamMember(name="Надежда Глазунова", role="Участник")]
    report = _make_report(["Надежда Глазунова"], [], ocr_count=1)
    filtered, _ = filter_team_for_public_export(members, report)
    assert any(m.name == "Надежда Глазунова" for m in filtered)


def test_needs_review_ocr_member_excluded() -> None:
    members = [TeamMember(name="Наденда Глазунова", role="")]
    report = _make_report([], ["Наденда Глазунова"], ocr_count=1)
    filtered, warnings = filter_team_for_public_export(members, report)
    assert not any(m.name == "Наденда Глазунова" for m in filtered)
    assert warnings


def test_rejected_ocr_member_excluded() -> None:
    members = [TeamMember(name="Manmusit Apel Аизтольевич", role="")]
    report = TeamVerificationReport(
        rejected_candidates=[
            TeamCandidateQuality(
                raw_name="Manmusit Apel Аизтольевич",
                verification_status=TeamVerificationStatus.rejected,
                verification_reason="garbage",
            )
        ],
        metrics=TeamVerificationMetrics(ocr_candidates=1, rejected_count=1),
    )
    filtered, _ = filter_team_for_public_export(members, report)
    assert not filtered


def test_docx_team_appears_without_report() -> None:
    members = [
        TeamMember(name="Татьяна Ерюкова", role="Помощник тимлида"),
        TeamMember(name="Кравченко Дмитрий", role="Тимлид"),
    ]
    filtered, _ = filter_team_for_public_export(members, None)
    assert len(filtered) == 2


def test_bad_easyocr_names_not_in_public_export() -> None:
    members = [TeamMember(name=n, role="") for n in BAD_OCR_NAMES]
    report = _make_report([], BAD_OCR_NAMES, ocr_count=len(BAD_OCR_NAMES))
    filtered, _ = filter_team_for_public_export(members, report)
    for bad in BAD_OCR_NAMES:
        assert not any(m.name == bad for m in filtered)


def test_guard_team_respects_verification_report() -> None:
    members = [TeamMember(name="Наденда Глазунова", role="")]
    report = _make_report([], ["Наденда Глазунова"], ocr_count=1)
    cleaned, warnings = guard_team_for_export(members, report)
    assert not cleaned
    assert warnings


class _FakeRepo:
    def __init__(self, contract: LandingContract) -> None:
        self._contract = contract

    async def get_contract(self, _pid):
        return self._contract

    async def get_landing(self, _pid):
        return None


@pytest.mark.asyncio
async def test_html_export_excludes_unverified_ocr_names() -> None:
    report = _make_report(
        ["Кравченко Дмитрий"],
        ["Наденда Глазунова", "Денис Калюаный"],
        ocr_count=2,
    )
    contract = LandingContract(
        project_id=uuid4(),
        status=ContractStatus.DRAFT,
        updated_at=utc_now(),
        fidelity=FidelityMetadata(
            team_structured=[
                TeamMember(name="Кравченко Дмитрий", role="Тимлид"),
            ],
            team_verification_report=report,
        ),
        blocks=[
            LandingBlock(
                key="team",
                title="Команда проекта",
                content="",
                bullets=["Кравченко Дмитрий — Тимлид"],
            )
        ],
    )
    exporter = StyledHtmlExporter(_FakeRepo(contract))
    html = await exporter.to_html(contract.project_id)
    assert "Кравченко" in html
    for bad in ("Наденда", "Калюаный"):
        assert bad not in html
