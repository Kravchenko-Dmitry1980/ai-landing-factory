"""Public export policy for verified team members."""



from __future__ import annotations



from app.schemas.fidelity import TeamMember

from app.schemas.team_review import TeamPublicationMode

from app.schemas.team_verification import (

    TeamCandidateQuality,

    TeamVerificationReport,

    TeamVerificationStatus,

)

from app.services.contract_fidelity.team_candidate_validator import filter_team_members

from app.services.team_verification.candidate_ids import make_candidate_id



MIN_NAME_QUALITY_FOR_PUBLIC = 0.5

OCR_REVIEW_WARNING = (

    "OCR found possible team members, but they require verification before public export."

)





def is_public_export_eligible(candidate: TeamCandidateQuality) -> bool:

    """Whether a candidate may appear in public HTML export."""

    if candidate.verification_status != TeamVerificationStatus.verified:

        return False

    if candidate.name_quality_score < MIN_NAME_QUALITY_FOR_PUBLIC:

        return False

    display_name = candidate.corrected_name or candidate.raw_name

    if not display_name.strip():

        return False

    return True





def candidate_to_team_member(candidate: TeamCandidateQuality) -> TeamMember:

    """Convert verified candidate to TeamMember for export."""

    name = candidate.corrected_name or candidate.raw_name

    return TeamMember(

        name=name,

        role=candidate.role or "",

        project_area="",

        contributions=list(candidate.contributions),

    )





def draft_team_from_report(report: TeamVerificationReport) -> list[TeamMember]:

    """Build editor draft team: verified + probable + needs_review (not rejected)."""

    members: list[TeamMember] = []

    for bucket in (

        report.verified_members,

        report.review_candidates,

        report.probable_candidates,

    ):

        for cand in bucket:

            members.append(candidate_to_team_member(cand))

    return _dedupe_team(members)





def _accepted_members_from_report(

    report: TeamVerificationReport,

    accepted_ids: list[str],

) -> list[TeamMember]:

    """Collect verified + user-accepted candidates for export."""

    accepted_set = set(accepted_ids)

    members: list[TeamMember] = []



    for cand in report.verified_members:

        members.append(candidate_to_team_member(cand))



    for bucket in (report.review_candidates, report.probable_candidates):

        for cand in bucket:

            cid = make_candidate_id(cand.raw_name, cand.source_filename)

            if cid in accepted_set:

                members.append(candidate_to_team_member(cand))



    return _dedupe_team(members)





def filter_team_for_public_export(

    members: list[TeamMember],

    report: TeamVerificationReport | None = None,

    publication_mode: str = TeamPublicationMode.safe_public,

    accepted_ids: list[str] | None = None,

) -> tuple[list[TeamMember], list[str]]:

    """Filter team members for public export using publication mode."""

    warnings: list[str] = []

    mode = publication_mode or TeamPublicationMode.safe_public

    accepted_ids = accepted_ids or []



    if mode == TeamPublicationMode.manual_edited:

        return filter_team_members(members), warnings



    if report is None:

        return filter_team_members(members), warnings



    if mode == TeamPublicationMode.user_accepted:

        exported = _accepted_members_from_report(report, accepted_ids)

        if exported:

            return filter_team_members(exported), warnings

        warnings.append(OCR_REVIEW_WARNING)

        return [], warnings



    # safe_public and draft_auto → verified only for public export

    verified = [

        candidate_to_team_member(c)

        for c in report.verified_members

        if is_public_export_eligible(c)

    ]

    if verified:

        return filter_team_members(verified), warnings



    if report.review_candidates or report.probable_candidates:

        warnings.append(OCR_REVIEW_WARNING)



    if report.metrics.ocr_candidates == 0 and members:

        return filter_team_members(members), warnings



    return [], warnings





def team_publication_warning(

    report: TeamVerificationReport | None,

    publication_mode: str = TeamPublicationMode.draft_auto,

) -> str | None:

    """Return warning message if OCR review candidates exist."""

    if publication_mode in (

        TeamPublicationMode.manual_edited,

        TeamPublicationMode.user_accepted,

    ):

        return None

    if not report:

        return None

    if report.review_candidates or report.probable_candidates:

        return OCR_REVIEW_WARNING

    if report.metrics.verified_count == 0 and report.metrics.ocr_candidates > 0:

        return OCR_REVIEW_WARNING

    return None





def _dedupe_team(members: list[TeamMember]) -> list[TeamMember]:

    seen: set[str] = set()

    result: list[TeamMember] = []

    for member in filter_team_members(members):

        key = member.name.lower()

        if key in seen:

            continue

        seen.add(key)

        result.append(member)

    return result

