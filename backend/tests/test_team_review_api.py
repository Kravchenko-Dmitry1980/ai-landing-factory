"""Tests for team review API and service."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.fidelity import FidelityMetadata, TeamMember
from app.schemas.landing_contract import ContractStatus, LandingBlock, LandingContract
from app.schemas.team_review import TeamPublicationMode
from app.schemas.team_verification import (
    TeamCandidateQuality,
    TeamVerificationMetrics,
    TeamVerificationReport,
    TeamVerificationStatus,
)
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.services.orchestration.agents.export_guard_agent import guard_team_for_export
from app.services.team_review.team_review_service import TeamReviewService
from app.services.team_verification.export_policy import filter_team_for_public_export
from app.services.team_verification.team_verification_service import TeamVerificationService
from app.config import settings


class _MemoryRepo(ContractRepository):
    def __init__(self) -> None:
        super().__init__(settings)
        self._contracts: dict = {}

    async def save_contract(self, contract: LandingContract) -> None:
        self._contracts[contract.project_id] = contract

    async def get_contract(self, project_id):
        return self._contracts.get(project_id)


def _ocr_report() -> TeamVerificationReport:
    verified = TeamCandidateQuality(
        raw_name="Кравченко Дмитрий",
        verification_status=TeamVerificationStatus.verified,
        verification_reason="trusted",
        name_quality_score=0.9,
    )
    review = [
        TeamCandidateQuality(
            raw_name=name,
            verification_status=TeamVerificationStatus.needs_review,
            verification_reason="ocr_only_unverified",
            source_is_ocr=True,
            source_filename="slide25.ocr",
            name_quality_score=0.6,
        )
        for name in (
            "Наденда Глазунова",
            "Денис Калюаный",
            "Александр Егорсв",
        )
    ]
    return TeamVerificationReport(
        verified_members=[verified],
        review_candidates=review,
        metrics=TeamVerificationMetrics(
            verified_count=1,
            needs_review_count=3,
            ocr_candidates=3,
        ),
    )


def _contract_with_report(project_id=None) -> LandingContract:
    pid = project_id or uuid4()
    report = _ocr_report()
    from app.services.team_verification.export_policy import draft_team_from_report

    team = draft_team_from_report(report)
    return LandingContract(
        project_id=pid,
        status=ContractStatus.DRAFT,
        updated_at=utc_now(),
        fidelity=FidelityMetadata(
            team_structured=team,
            team_verification_report=report,
            team_publication_mode=TeamPublicationMode.draft_auto,
        ),
        blocks=[
            LandingBlock(key="team", title="Команда", content="", bullets=[]),
        ],
    )


@pytest.fixture
def review_service() -> TeamReviewService:
    return TeamReviewService(_MemoryRepo())


@pytest.mark.asyncio
async def test_get_team_review_returns_summary_and_editable_text(
    review_service: TeamReviewService,
) -> None:
    contract = _contract_with_report()
    review_service._repo._contracts[contract.project_id] = contract

    response = await review_service.get_review(contract.project_id)
    assert response.summary.total_candidates == 4
    assert response.summary.verified_count == 1
    assert response.summary.needs_review_count == 3
    assert response.editable_text
    assert "Кравченко" in response.editable_text
    assert len(response.candidates) == 4


@pytest.mark.asyncio
async def test_accept_all_marks_accepted(review_service: TeamReviewService) -> None:
    contract = _contract_with_report()
    review_service._repo._contracts[contract.project_id] = contract

    result = await review_service.apply_bulk_action(
        contract.project_id, "accept_all"
    )
    assert result.publication_mode == TeamPublicationMode.user_accepted
    saved = await review_service._repo.get_contract(contract.project_id)
    assert saved.fidelity.team_publication_mode == TeamPublicationMode.user_accepted
    assert len(saved.fidelity.accepted_team_candidate_ids) >= 3
    assert len(saved.fidelity.team_structured) == 4


@pytest.mark.asyncio
async def test_keep_verified_only_excludes_unverified(
    review_service: TeamReviewService,
) -> None:
    contract = _contract_with_report()
    review_service._repo._contracts[contract.project_id] = contract

    await review_service.apply_bulk_action(contract.project_id, "keep_verified_only")
    saved = await review_service._repo.get_contract(contract.project_id)
    assert saved.fidelity.team_publication_mode == TeamPublicationMode.safe_public
    assert len(saved.fidelity.team_structured) == 1
    assert saved.fidelity.team_structured[0].name == "Кравченко Дмитрий"


@pytest.mark.asyncio
async def test_manual_text_replaces_team(review_service: TeamReviewService) -> None:
    contract = _contract_with_report()
    review_service._repo._contracts[contract.project_id] = contract

    text = (
        "Надежда Глазунова — аналитика\n"
        "- кластеризация\n"
        "Татьяна Ерюкова — помощник тимлида\n"
    )
    result = await review_service.apply_manual_text(contract.project_id, text)
    assert result.publication_mode == TeamPublicationMode.manual_edited
    saved = await review_service._repo.get_contract(contract.project_id)
    names = {m.name for m in saved.fidelity.team_structured}
    assert "Надежда Глазунова" in names
    assert "Татьяна Ерюкова" in names


@pytest.mark.asyncio
async def test_rejected_not_included_by_accept_all(
    review_service: TeamReviewService,
) -> None:
    contract = _contract_with_report()
    report = contract.fidelity.team_verification_report
    report.rejected_candidates = [
        TeamCandidateQuality(
            raw_name="Manmusit Apel",
            verification_status=TeamVerificationStatus.rejected,
            verification_reason="garbage",
        )
    ]
    review_service._repo._contracts[contract.project_id] = contract

    await review_service.apply_bulk_action(contract.project_id, "accept_all")
    saved = await review_service._repo.get_contract(contract.project_id)
    names = {m.name for m in saved.fidelity.team_structured}
    assert "Manmusit Apel" not in names


def test_export_after_manual_text() -> None:
    members = [
        TeamMember(name="Надежда Глазунова", role="аналитика"),
    ]
    filtered, _ = filter_team_for_public_export(
        members,
        None,
        TeamPublicationMode.manual_edited,
    )
    assert any(m.name == "Надежда Глазунова" for m in filtered)


def test_export_keep_verified_excludes_bad_ocr() -> None:
    report = _ocr_report()
    members = [
        TeamMember(name=c.raw_name, role=c.role or "")
        for c in report.verified_members + report.review_candidates
    ]
    filtered, _ = filter_team_for_public_export(
        members, report, TeamPublicationMode.safe_public
    )
    assert len(filtered) == 1
    assert filtered[0].name == "Кравченко Дмитрий"
    for bad in ("Наденда", "Калюаный", "Егорсв"):
        assert not any(bad in m.name for m in filtered)


@pytest.mark.asyncio
async def test_reset_to_auto_returns_draft_mode(
    review_service: TeamReviewService,
) -> None:
    contract = _contract_with_report()
    review_service._repo._contracts[contract.project_id] = contract
    await review_service.apply_bulk_action(contract.project_id, "keep_verified_only")
    await review_service.apply_bulk_action(contract.project_id, "reset_to_auto")
    saved = await review_service._repo.get_contract(contract.project_id)
    assert saved.fidelity.team_publication_mode == TeamPublicationMode.draft_auto
    assert len(saved.fidelity.team_structured) == 4


class _FakeRepo:
    def __init__(self, contract: LandingContract) -> None:
        self._contract = contract

    async def get_contract(self, _pid):
        return self._contract

    async def get_landing(self, _pid):
        return None


@pytest.mark.asyncio
async def test_export_after_accept_all_includes_names() -> None:
    report = _ocr_report()
    from app.services.team_verification.candidate_ids import make_candidate_id

    accepted = [
        make_candidate_id(c.raw_name, c.source_filename)
        for c in report.review_candidates
    ]
    contract = LandingContract(
        project_id=uuid4(),
        status=ContractStatus.DRAFT,
        updated_at=utc_now(),
        fidelity=FidelityMetadata(
            team_structured=[
                TeamMember(name=c.raw_name, role=c.role or "")
                for c in report.verified_members + report.review_candidates
            ],
            team_verification_report=report,
            team_publication_mode=TeamPublicationMode.user_accepted,
            accepted_team_candidate_ids=accepted,
        ),
        blocks=[],
    )
    members, _ = guard_team_for_export(
        contract.fidelity.team_structured,
        report,
        TeamPublicationMode.user_accepted,
        accepted,
    )
    assert any("Наденда" in m.name for m in members)


def test_docx_team_bypasses_ocr_review() -> None:
    docx_text = """
Команда проекта
Тимлид: Кравченко Дмитрий
1. Татьяна Ерюкова — помощник тимлида
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
    report = TeamVerificationService().verify(members, extraction)
    assert len(report.verified_members) == 1
    filtered, _ = filter_team_for_public_export(
        members, report, TeamPublicationMode.draft_auto
    )
    assert filtered
