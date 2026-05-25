from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.dependencies import get_contract_repository
from app.repositories.project_repository import ProjectRepository
from app.schemas.generation import GeneratedLanding
from app.schemas.landing_contract import LandingContract
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.export.export_theme import ExportTheme
from app.services.export.styled_html_exporter import StyledHtmlExporter

router = APIRouter()
_project_repo = ProjectRepository(settings)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate) -> ProjectResponse:
    record = await _project_repo.create(body.name, body.description)
    return ProjectResponse(
        id=record.id,
        name=record.name,
        description=record.description,
        created_at=record.created_at,
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


@router.get("/{project_id}/export/html")
async def export_html(
    project_id: UUID,
    theme: str | None = None,
) -> dict[str, str]:
    export_theme = ExportTheme.from_query(theme)
    html = await StyledHtmlExporter(get_contract_repository()).to_html(
        project_id,
        theme=export_theme,
    )
    return {"html": html}
