"""Showcase Registry CRUD + export API (Stage P.6).

Additive registry layer on top of the Stage P.5 exporters. Stores showcases as
JSON files, exposes project CRUD, and re-exports a *saved* showcase to HTML/ZIP
using the existing exporters. Does not touch the normal landing export flow.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter
from app.services.showcase.showcase_registry import (
    ShowcaseNotFoundError,
    ShowcaseProjectNotFoundError,
    get_showcase_registry,
)
from app.services.showcase.showcase_schema import (
    ShowcaseConfig,
    ShowcaseCreateRequest,
    ShowcaseExportResult,
    ShowcaseProjectCreateRequest,
    ShowcaseProjectUpdateRequest,
    ShowcaseReorderRequest,
    ShowcaseSummary,
    ShowcaseUpdateRequest,
)
from app.services.showcase.showcase_vendor import ZIP_DOWNLOAD_FILENAME
from app.services.showcase.showcase_zip_exporter import build_showcase_zip

router = APIRouter()


def _registry():
    return get_showcase_registry()


def _get_or_404(showcase_id: str) -> ShowcaseConfig:
    try:
        return _registry().get_showcase(showcase_id)
    except ShowcaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Showcase not found") from exc


# --------------------------------------------------------------- showcase CRUD


@router.get("", response_model=list[ShowcaseSummary])
async def list_showcases() -> list[ShowcaseSummary]:
    return _registry().list_summaries()


@router.post("", response_model=ShowcaseConfig, status_code=201)
async def create_showcase(body: ShowcaseCreateRequest) -> ShowcaseConfig:
    return _registry().create_showcase(body)


@router.get("/{showcase_id}", response_model=ShowcaseConfig)
async def get_showcase(showcase_id: str) -> ShowcaseConfig:
    return _get_or_404(showcase_id)


@router.patch("/{showcase_id}", response_model=ShowcaseConfig)
async def update_showcase(
    showcase_id: str, body: ShowcaseUpdateRequest
) -> ShowcaseConfig:
    try:
        return _registry().update_showcase(showcase_id, body)
    except ShowcaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Showcase not found") from exc


@router.delete("/{showcase_id}")
async def delete_showcase(showcase_id: str) -> dict[str, bool]:
    deleted = _registry().delete_showcase(showcase_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Showcase not found")
    return {"deleted": True}


# ---------------------------------------------------------------- project CRUD


@router.post("/{showcase_id}/projects", response_model=ShowcaseConfig)
async def add_project(
    showcase_id: str, body: ShowcaseProjectCreateRequest
) -> ShowcaseConfig:
    try:
        return _registry().add_project(showcase_id, body)
    except ShowcaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Showcase not found") from exc


@router.patch("/{showcase_id}/projects/{project_id}", response_model=ShowcaseConfig)
async def update_project(
    showcase_id: str,
    project_id: str,
    body: ShowcaseProjectUpdateRequest,
) -> ShowcaseConfig:
    try:
        return _registry().update_project(showcase_id, project_id, body)
    except ShowcaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Showcase not found") from exc
    except ShowcaseProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.delete("/{showcase_id}/projects/{project_id}", response_model=ShowcaseConfig)
async def delete_project(showcase_id: str, project_id: str) -> ShowcaseConfig:
    try:
        return _registry().delete_project(showcase_id, project_id)
    except ShowcaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Showcase not found") from exc
    except ShowcaseProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.post("/{showcase_id}/projects/reorder", response_model=ShowcaseConfig)
async def reorder_projects(
    showcase_id: str, body: ShowcaseReorderRequest
) -> ShowcaseConfig:
    try:
        return _registry().reorder_projects(showcase_id, body.ordered_ids)
    except ShowcaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Showcase not found") from exc


# -------------------------------------------------------------------- exports


@router.post("/{showcase_id}/export-html", response_model=ShowcaseExportResult)
async def export_showcase_html(
    showcase_id: str,
    aframe_src: str | None = Query(default=None),
) -> ShowcaseExportResult:
    config = _get_or_404(showcase_id)
    exporter = (
        ShowcaseHtmlExporter(aframe_src=aframe_src)
        if aframe_src
        else ShowcaseHtmlExporter()
    )
    return exporter.export(config)


@router.post("/{showcase_id}/export-zip")
async def export_showcase_zip(showcase_id: str) -> Response:
    config = _get_or_404(showcase_id)
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
