from uuid import UUID



from fastapi import APIRouter, File, Form, HTTPException, UploadFile



from app.core.dependencies import (

    get_contract_builder,

    get_extraction_service,

    get_file_store,

    get_generation_service,

    get_pii_stage,

)

from app.repositories.contract_repository import ContractRepository

from app.repositories.project_repository import ProjectRepository

from app.config import settings

from app.schemas.pii import PiiSummary

from app.schemas.upload import UploadResponse

from app.services.pipeline import ContentPipeline



router = APIRouter()

_project_repo = ProjectRepository(settings)





def _pipeline() -> ContentPipeline:

    repo = ContractRepository(settings)

    return ContentPipeline(

        get_extraction_service(),

        get_contract_builder(),

        get_generation_service(),

        repo,

        get_pii_stage(),

    )





@router.post("/{project_id}/upload", response_model=UploadResponse)

async def upload_materials(

    project_id: UUID,

    files: list[UploadFile] = File(...),

    description: str | None = Form(default=None),

) -> UploadResponse:

    project = await _project_repo.get(project_id)

    if not project:

        raise HTTPException(404, "Project not found")

    if not files:

        raise HTTPException(400, "At least one file is required")



    store = get_file_store()

    saved = []

    for upload in files:

        content = await upload.read()

        meta = await store.save_upload(

            project_id,

            upload.filename or "unnamed",

            content,

            upload.content_type,

        )

        saved.append(meta)



    if description:

        await store.save_upload(

            project_id,

            "description.txt",

            description.encode("utf-8"),

            "text/plain",

        )



    pii_raw = await _pipeline().run_after_upload(project_id)

    pii_summary = PiiSummary.model_validate(pii_raw) if pii_raw else None



    return UploadResponse(

        project_id=project_id,

        files=saved,

        message="Upload complete. Draft LandingContract and landing preview are ready.",

        pii_summary=pii_summary,

    )

