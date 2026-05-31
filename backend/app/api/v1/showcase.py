"""VR/AR Showcase export API (Stage P.5 MVP).

Separate, additive endpoint. Does not touch the normal landing export flow.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter
from app.services.showcase.showcase_schema import ShowcaseConfig, ShowcaseExportResult

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
