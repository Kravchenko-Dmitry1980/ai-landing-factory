from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.core.dependencies import get_contract_repository
from app.repositories.project_repository import ProjectRepository
from app.schemas.generation import GeneratedLanding
from app.schemas.landing_contract import LandingContract
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectSummary
from app.services.diagnostics.last_project_tracker import write_last_project
from app.schemas.style_config import StyleConfigPatch, StyleConfigResponse
from app.core.dependencies import get_contract_builder
from app.services.export.export_theme import resolve_export_style
from app.services.export.styled_html_exporter import StyledHtmlExporter

router = APIRouter()
_project_repo = ProjectRepository(settings)
_RUNTIME_ROOT = settings.base_dir.parent


def _record_last_project(project_id: UUID, project_name: str, source: str) -> None:
    write_last_project(
        _RUNTIME_ROOT,
        project_id=project_id,
        project_name=project_name,
        source=source,
    )


@router.get("", response_model=list[ProjectSummary])
async def list_projects(
    limit: int = Query(default=50, ge=1, le=200),
    sort: str = Query(default="updated_desc"),
) -> list[ProjectSummary]:
    if sort not in ("updated_desc", "updated_asc", "created_desc", "created_asc"):
        raise HTTPException(400, "Invalid sort. Use updated_desc, updated_asc, created_desc, created_asc.")
    records = await _project_repo.list_projects(limit=limit, sort=sort)
    contract_repo = get_contract_repository()
    summaries: list[ProjectSummary] = []
    for rec in records:
        version = 1
        contract = await contract_repo.get_contract(rec.id)
        if contract:
            version = contract.version
        summaries.append(
            ProjectSummary(
                id=rec.id,
                name=rec.name,
                created_at=rec.created_at,
                updated_at=rec.updated_at,
                version=version,
            )
        )
    return summaries


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate) -> ProjectResponse:
    record = await _project_repo.create(body.name, body.description)
    _record_last_project(record.id, record.name, "api")
    return ProjectResponse(
        id=record.id,
        name=record.name,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID) -> ProjectResponse:
    record = await _project_repo.get(project_id)
    if not record:
        raise HTTPException(404, "Project not found")
    return ProjectResponse(
        id=record.id,
        name=record.name,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/{project_id}/contract", response_model=LandingContract)
async def get_contract(project_id: UUID) -> LandingContract:
    contract = await get_contract_repository().get_contract(project_id)
    if not contract:
        raise HTTPException(404, "LandingContract not found. Upload materials first.")
    return contract


@router.get("/{project_id}/landing", response_model=GeneratedLanding)
async def get_landing(project_id: UUID) -> GeneratedLanding:
    landing = await get_contract_repository().get_landing(project_id)
    if not landing:
        raise HTTPException(404, "Landing not generated yet.")
    return landing


@router.patch("/{project_id}/style-config", response_model=StyleConfigResponse)
async def patch_style_config(
    project_id: UUID,
    body: StyleConfigPatch,
) -> StyleConfigResponse:
    repo = get_contract_repository()
    contract = await repo.get_contract(project_id)
    if not contract:
        raise HTTPException(404, "LandingContract not found. Upload materials first.")
    from app.schemas.style_config import LandingStyleConfigModel

    cfg = LandingStyleConfigModel(
        profile=body.profile,
        custom_style_prompt=body.custom_style_prompt,
        theme_tokens=body.theme_tokens,
    )
    presentation = body.profile.value
    if body.profile.value == "custom":
        presentation = "university_platform"
    updated = await get_contract_builder().update_contract(
        project_id,
        blocks=None,
        style_config=cfg,
        presentation_style=presentation,
    )
    if not updated:
        raise HTTPException(404, "LandingContract not found")
    return StyleConfigResponse(
        project_id=str(project_id),
        style_config=updated.style_config or cfg,
    )


@router.get("/{project_id}/export/html")
async def export_html(
    project_id: UUID,
    theme: str | None = None,
    style_config: str | None = None,
    mode: str | None = None,
    export_mode: str | None = None,
    wow_3d_runtime: str | None = None,
    demo_url: str | None = None,
) -> dict[str, str]:
    from app.schemas.export_mode import (
        LandingExportMode,
        parse_export_mode,
        parse_wow_runtime,
    )
    from app.schemas.style_config import parse_style_config_query

    # ``mode`` is the primary contract; ``export_mode`` is an accepted alias.
    try:
        resolved_mode = parse_export_mode(mode or export_mode)
        resolved_runtime = parse_wow_runtime(wow_3d_runtime)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    repo = get_contract_repository()
    contract = await repo.get_contract(project_id)
    parsed_style = parse_style_config_query(style_config)
    resolved_theme, _, _ = resolve_export_style(
        contract,
        theme_query=theme,
        style_config_query=parsed_style,
    )

    if resolved_mode == LandingExportMode.WOW:
        from app.services.export.wow.wow_exporter import (
            WowExportOptions,
            WowHtmlExporter,
        )

        html = await WowHtmlExporter(repo).to_html(
            project_id,
            theme=resolved_theme,
            style_config=parsed_style,
            options=WowExportOptions(runtime=resolved_runtime, demo_url=demo_url),
        )
        return {"html": html}

    html = await StyledHtmlExporter(repo).to_html(
        project_id,
        theme=resolved_theme,
        style_config=parsed_style,
    )
    return {"html": html}
