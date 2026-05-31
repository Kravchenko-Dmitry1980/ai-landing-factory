"""Build landing candidate entries for the showcase builder (Stage P.6.2).

Pure helpers: construct preview/export URLs from project ids and map registry
records + contracts into ``LandingCandidate`` payloads. No frontend or network
required.
"""

from __future__ import annotations

from app.models.domain import ProjectRecord
from app.schemas.landing_contract import LandingContract
from app.services.showcase.showcase_schema import LandingCandidate

_EXPORT_HTML_PREFIX = "/api/v1/projects"
_PREVIEW_PREFIX = "/preview"


def preview_url_for_project(project_id: str) -> str:
    """Relative frontend preview route for a landing project."""

    return f"{_PREVIEW_PREFIX}/{project_id}"


def export_html_url_for_project(project_id: str) -> str:
    """Backend HTML export endpoint for a landing project."""

    return f"{_EXPORT_HTML_PREFIX}/{project_id}/export/html"


def is_valid_project_id(project_id: str | None) -> bool:
    """Reject empty or path-smuggling project ids."""

    if not project_id:
        return False
    cleaned = str(project_id).strip()
    if not cleaned:
        return False
    if ".." in cleaned or "/" in cleaned or "\\" in cleaned:
        return False
    return True


def build_landing_candidate(
    record: ProjectRecord,
    *,
    contract: LandingContract | None = None,
    has_landing: bool = False,
) -> LandingCandidate | None:
    """Map a project registry row (+ optional contract) to a showcase candidate."""

    project_id = str(record.id)
    if not is_valid_project_id(project_id):
        return None

    title = (contract.title if contract and contract.title else record.name) or record.name
    client = contract.client if contract else None
    description: str | None = None
    if contract:
        description = contract.lead or contract.quote or None
    elif record.description:
        description = record.description

    preview_url = preview_url_for_project(project_id)
    export_html_url = export_html_url_for_project(project_id)

    return LandingCandidate(
        project_id=project_id,
        title=title,
        client=client,
        description=description,
        preview_url=preview_url,
        export_html_url=export_html_url,
        landing_url=preview_url,
        export_available=bool(contract or has_landing),
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
    )


def candidate_title_from_contract(
    record: ProjectRecord,
    contract: LandingContract | None,
) -> str:
    """Extract display title preferring contract over registry name."""

    if contract and contract.title:
        return contract.title
    return record.name
