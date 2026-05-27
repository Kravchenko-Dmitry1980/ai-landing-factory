"""Team review service — bulk actions and manual text editing."""

from __future__ import annotations

import logging
from uuid import UUID

from app.repositories.contract_repository import ContractRepository
from app.schemas.fidelity import FidelityMetadata, TeamMember
from app.schemas.landing_contract import LandingContract
from app.schemas.team_review import (
    TeamPublicationMode,
    TeamReviewActionResponse,
    TeamReviewCandidate,
    TeamReviewResponse,
    TeamReviewSummary,
)
from app.schemas.team_verification import TeamCandidateQuality, TeamVerificationReport
from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
from app.services.contract_fidelity.team_candidate_validator import filter_team_members
from app.services.contract_fidelity.team_parser import team_to_bullets
from app.services.team_verification.candidate_ids import make_candidate_id
from app.services.team_review.team_text_formatter import (
    apply_team_to_contract_blocks,
    format_team_as_text,
    parse_manual_team_text,
    team_members_to_editable_text,
)
from app.services.team_verification.export_policy import (
    OCR_REVIEW_WARNING,
    candidate_to_team_member,
    draft_team_from_report,
    filter_team_for_public_export,
)

logger = logging.getLogger(__name__)

OCR_TEAM_WARNING = (
    "Команда извлечена из изображения через OCR. Возможны ошибки в ФИО."
)


class TeamReviewService:
    """Minimal team review UX — auto-fill first, bulk actions, text edit."""

    def __init__(self, repository: ContractRepository) -> None:
        self._repo = repository
        self._completeness_gate = ContractCompletenessGate()

    async def get_review(self, project_id: UUID) -> TeamReviewResponse:
        contract = await self._repo.get_contract(project_id)
        if not contract:
            raise ValueError("LandingContract not found")
        return self.build_response(contract)

    def build_response(self, contract: LandingContract) -> TeamReviewResponse:
        fidelity = contract.fidelity
        report = fidelity.team_verification_report if fidelity else None
        mode = _publication_mode(fidelity)
        candidates = self._build_candidates(report, fidelity)
        summary = self._build_summary(report, fidelity, candidates)

        editable = (
            fidelity.manual_team_text
            if fidelity and fidelity.manual_team_text
            else format_team_as_text(candidates)
            if candidates
            else team_members_to_editable_text(
                fidelity.team_structured if fidelity else []
            )
        )

        return TeamReviewResponse(
            project_id=contract.project_id,
            summary=summary,
            candidates=candidates,
            editable_text=editable,
            publication_mode=mode,
        )

    async def apply_bulk_action(
        self,
        project_id: UUID,
        action: str,
    ) -> TeamReviewActionResponse:
        contract = await self._repo.get_contract(project_id)
        if not contract:
            raise ValueError("LandingContract not found")

        fidelity = contract.fidelity or FidelityMetadata()
        contract.fidelity = fidelity
        report = fidelity.team_verification_report

        if action == "accept_all":
            self._apply_accept_all(fidelity, report)
        elif action == "keep_verified_only":
            self._apply_keep_verified(fidelity, report)
        elif action == "reset_to_auto":
            self._apply_reset_auto(fidelity, report)
        else:
            raise ValueError(f"Unknown action: {action}")

        self._sync_team_blocks(contract)
        fidelity.completeness = self._completeness_gate.evaluate(contract)
        await self._repo.save_contract(contract)

        response = self.build_response(contract)
        logger.info(
            "Team bulk action %s for %s: mode=%s team=%d",
            action,
            project_id,
            fidelity.team_publication_mode,
            len(fidelity.team_structured),
        )
        return TeamReviewActionResponse(
            project_id=project_id,
            publication_mode=fidelity.team_publication_mode,
            summary=response.summary,
            team_count=len(fidelity.team_structured),
        )

    async def apply_manual_text(
        self,
        project_id: UUID,
        text: str,
    ) -> TeamReviewActionResponse:
        contract = await self._repo.get_contract(project_id)
        if not contract:
            raise ValueError("LandingContract not found")

        members = parse_manual_team_text(text)
        if not members:
            raise ValueError("Не удалось распознать участников команды в тексте")

        fidelity = contract.fidelity or FidelityMetadata()
        contract.fidelity = fidelity
        fidelity.team_structured = members
        fidelity.team_publication_mode = TeamPublicationMode.manual_edited
        fidelity.manual_team_override = True
        fidelity.manual_team_text = text.strip()
        fidelity.accepted_team_candidate_ids = []
        fidelity.team_review_warning = None

        self._sync_team_blocks(contract)
        fidelity.completeness = self._completeness_gate.evaluate(contract)
        await self._repo.save_contract(contract)

        response = self.build_response(contract)
        return TeamReviewActionResponse(
            project_id=project_id,
            publication_mode=TeamPublicationMode.manual_edited,
            summary=response.summary,
            team_count=len(members),
        )

    def _apply_accept_all(
        self,
        fidelity: FidelityMetadata,
        report: TeamVerificationReport | None,
    ) -> None:
        if not report:
            return
        accepted_ids: list[str] = []
        members: list[TeamMember] = []

        for bucket in (
            report.verified_members,
            report.review_candidates,
            report.probable_candidates,
        ):
            for cand in bucket:
                cid = make_candidate_id(cand.raw_name, cand.source_filename)
                accepted_ids.append(cid)
                members.append(candidate_to_team_member(cand))

        fidelity.accepted_team_candidate_ids = list(dict.fromkeys(accepted_ids))
        fidelity.team_publication_mode = TeamPublicationMode.user_accepted
        fidelity.manual_team_override = False
        fidelity.manual_team_text = None
        fidelity.team_structured = _dedupe_members(members)
        fidelity.team_review_warning = OCR_TEAM_WARNING if report.metrics.ocr_candidates else None

    def _apply_keep_verified(
        self,
        fidelity: FidelityMetadata,
        report: TeamVerificationReport | None,
    ) -> None:
        fidelity.team_publication_mode = TeamPublicationMode.safe_public
        fidelity.accepted_team_candidate_ids = []
        fidelity.manual_team_override = False
        fidelity.manual_team_text = None

        if report:
            verified = [
                candidate_to_team_member(c) for c in report.verified_members
            ]
            fidelity.team_structured = _dedupe_members(verified)
        else:
            filtered, _ = filter_team_for_public_export(
                fidelity.team_structured,
                report,
                TeamPublicationMode.safe_public,
            )
            fidelity.team_structured = filtered

        fidelity.team_review_warning = OCR_REVIEW_WARNING if report and (
            report.review_candidates or report.probable_candidates
        ) else None

    def _apply_reset_auto(
        self,
        fidelity: FidelityMetadata,
        report: TeamVerificationReport | None,
    ) -> None:
        fidelity.team_publication_mode = TeamPublicationMode.draft_auto
        fidelity.accepted_team_candidate_ids = []
        fidelity.manual_team_override = False
        fidelity.manual_team_text = None

        if report:
            fidelity.team_structured = draft_team_from_report(report)
            fidelity.team_review_warning = (
                OCR_TEAM_WARNING
                if report.review_candidates or report.probable_candidates
                else None
            )
        fidelity.team_review_warning = fidelity.team_review_warning or None

    def _build_candidates(
        self,
        report: TeamVerificationReport | None,
        fidelity: FidelityMetadata | None,
    ) -> list[TeamReviewCandidate]:
        if not report:
            if fidelity and fidelity.team_structured:
                return [
                    TeamReviewCandidate(
                        id=make_candidate_id(m.name),
                        raw_name=m.name,
                        display_name=m.name,
                        role=m.role or None,
                        contributions=list(m.contributions),
                        status="manual" if fidelity.manual_team_override else "verified",
                        source="manual" if fidelity.manual_team_override else "docx",
                    )
                    for m in fidelity.team_structured
                ]
            return []

        accepted = set(fidelity.accepted_team_candidate_ids if fidelity else [])
        mode = _publication_mode(fidelity)
        result: list[TeamReviewCandidate] = []

        for bucket, default_status in (
            (report.verified_members, "verified"),
            (report.probable_candidates, "probable"),
            (report.review_candidates, "needs_review"),
            (report.rejected_candidates, "rejected"),
        ):
            for cand in bucket:
                cid = make_candidate_id(cand.raw_name, cand.source_filename)
                status = default_status
                if mode == TeamPublicationMode.manual_edited:
                    status = "manual"
                elif cid in accepted and default_status != "verified":
                    status = "accepted_by_user"

                warning = None
                if cand.source_is_ocr and status in (
                    "needs_review",
                    "probable",
                    "accepted_by_user",
                ):
                    warning = OCR_TEAM_WARNING
                if cand.matched_trusted_name and cand.raw_name != cand.matched_trusted_name:
                    warning = (
                        f"Возможное совпадение: {cand.matched_trusted_name}"
                    )

                result.append(
                    _candidate_view(cand, cid, status, warning)
                )
        return result

    def _build_summary(
        self,
        report: TeamVerificationReport | None,
        fidelity: FidelityMetadata | None,
        candidates: list[TeamReviewCandidate],
    ) -> TeamReviewSummary:
        mode = _publication_mode(fidelity)
        if not report:
            count = len(fidelity.team_structured) if fidelity else 0
            return TeamReviewSummary(
                total_candidates=count,
                verified_count=count,
                publication_mode=mode,
                can_publish_team=count > 0,
            )

        metrics = report.metrics
        can_publish = mode in (
            TeamPublicationMode.manual_edited,
            TeamPublicationMode.user_accepted,
        ) or metrics.verified_count > 0

        warning = fidelity.team_review_warning if fidelity else None
        if not warning and metrics.ocr_candidates > 0 and mode == TeamPublicationMode.draft_auto:
            warning = OCR_TEAM_WARNING

        return TeamReviewSummary(
            total_candidates=(
                metrics.verified_count
                + metrics.probable_count
                + metrics.needs_review_count
                + metrics.rejected_count
            ),
            verified_count=metrics.verified_count,
            probable_count=metrics.probable_count,
            needs_review_count=metrics.needs_review_count,
            rejected_count=metrics.rejected_count,
            publication_mode=mode,
            can_publish_team=can_publish,
            warning=warning,
        )

    @staticmethod
    def _sync_team_blocks(contract: LandingContract) -> None:
        fidelity = contract.fidelity
        if not fidelity:
            return
        apply_team_to_contract_blocks(fidelity.team_structured, contract.blocks)


def _publication_mode(fidelity: FidelityMetadata | None) -> str:
    if not fidelity:
        return TeamPublicationMode.draft_auto
    return fidelity.team_publication_mode or TeamPublicationMode.draft_auto


def _candidate_view(
    cand: TeamCandidateQuality,
    cid: str,
    status: str,
    warning: str | None,
) -> TeamReviewCandidate:
    display = cand.corrected_name or cand.raw_name
    source = cand.source_filename or cand.source_type or "unknown"
    if cand.source_is_ocr and cand.ocr_engine:
        source = f"{source} / {cand.ocr_engine}"

    return TeamReviewCandidate(
        id=cid,
        raw_name=cand.raw_name,
        display_name=display,
        role=cand.role,
        contributions=list(cand.contributions),
        status=status,
        source=source,
        source_is_ocr=cand.source_is_ocr,
        confidence=cand.ocr_confidence,
        warning=warning,
    )


def _dedupe_members(members: list[TeamMember]) -> list[TeamMember]:
    seen: set[str] = set()
    result: list[TeamMember] = []
    for member in filter_team_members(members):
        key = member.name.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(member)
    return result
