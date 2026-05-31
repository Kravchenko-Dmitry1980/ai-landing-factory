"""VR/AR Showcase export API (Stage P.5 MVP + P.5.2 ZIP bundle).

Separate, additive endpoints. Does not touch the normal landing export flow.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.config import settings
from app.core.dependencies import get_contract_repository
from app.repositories.project_repository import ProjectRepository
from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter
from app.services.showcase.showcase_schema import (
    LandingCandidate,
    ShowcaseConfig,
    ShowcaseExportResult,
)
from app.services.showcase.showcase_vendor import ZIP_DOWNLOAD_FILENAME
from app.services.showcase.showcase_zip_exporter import build_showcase_zip

router = APIRouter()
_project_repo = ProjectRepository(settings)


@router.post("/export-html", response_model=ShowcaseExportResult)
async def export_showcase_html(
    config: ShowcaseConfig,
    aframe_src: str | None = Query(
        default=None,
        description="Override A-Frame runtime URL (e.g. a vendored relative path).",
    ),
) -> ShowcaseExportResult:
    """Render a showcase config into self-contained A-Frame + 2D fallback HTML."""

    exporter = (
        ShowcaseHtmlExporter(aframe_src=aframe_src)
        if aframe_src
        else ShowcaseHtmlExporter()
    )
    return exporter.export(config)


@router.post("/export-zip")
async def export_showcase_zip(config: ShowcaseConfig) -> Response:
    """Render a portable offline ZIP bundle (HTML + vendored A-Frame + license)."""

    try:
        data = build_showcase_zip(config)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return Response(
        content=data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{ZIP_DOWNLOAD_FILENAME}"',
        },
    )


@router.get("/landing-candidates", response_model=list[LandingCandidate])
async def list_landing_candidates(
    limit: int = Query(default=50, ge=1, le=200),
) -> list[LandingCandidate]:
    """List existing landing projects that can be attached to a showcase.

    MVP behavior: read from the existing project registry and enrich each
    entry with contract title/client/lead when available. ``landing_url`` is
    left blank (no permanent public URL in MVP); the builder lets the user
    paste a demo/landing link manually.
    """

    records = await _project_repo.list_projects(limit=limit, sort="updated_desc")
    contract_repo = get_contract_repository()
    candidates: list[LandingCandidate] = []
    for record in records:
        contract = await contract_repo.get_contract(record.id)
        title = (contract.title if contract and contract.title else record.name) or record.name
        client = contract.client if contract else None
        description = None
        if contract:
            description = contract.lead or contract.quote or None
        landing = await contract_repo.get_landing(record.id)
        candidates.append(
            LandingCandidate(
                project_id=str(record.id),
                title=title,
                client=client,
                description=description,
                landing_url=None,
                export_available=bool(contract or landing),
                updated_at=record.updated_at.isoformat() if record.updated_at else None,
            )
        )
    return candidates
