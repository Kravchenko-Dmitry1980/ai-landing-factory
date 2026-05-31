"""VR/AR Showcase export API (Stage P.5 MVP + P.5.2 ZIP bundle).

Separate, additive endpoints. Does not touch the normal landing export flow.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter
from app.services.showcase.showcase_schema import ShowcaseConfig, ShowcaseExportResult
from app.services.showcase.showcase_vendor import ZIP_DOWNLOAD_FILENAME
from app.services.showcase.showcase_zip_exporter import build_showcase_zip

router = APIRouter()


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
