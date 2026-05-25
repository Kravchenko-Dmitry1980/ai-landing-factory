from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.core.dependencies import (
    get_contract_repository,
    get_llm_contract_builder,
    get_pii_stage,
    get_safe_cloud_payload_service,
    get_settings,
)
from app.schemas.pii import (
    PIIReportPublic,
    PiiCleanupResponse,
    PrivacyMode,
    PrivacyStatusResponse,
    SafeCloudPayloadPreview,
)
from app.services.pii.cleanup import cleanup_expired_pii_reports
from app.services.pii.report import to_public_report
from app.services.pii.storage import build_storage_policy
from app.services.pipeline.pii_stage import PIIStageService

router = APIRouter()


@router.get("/privacy", response_model=PrivacyStatusResponse)
async def get_privacy_status() -> PrivacyStatusResponse:
    settings = get_settings()
    stage = get_pii_stage()
    mode = stage.privacy_mode
    cloud_unsafe = mode == PrivacyMode.CLOUD_UNSAFE_DEV
    cloud_allowed = stage.cloud_allowed() and settings.llm_enabled
    if mode == PrivacyMode.LOCAL_ONLY:
        cloud_allowed = False
    return PrivacyStatusResponse(
        privacy_mode=mode,
        enable_pii_detection=settings.enable_pii_detection,
        enable_rehydration=settings.enable_rehydration,
        llm_enabled=settings.llm_enabled,
        cloud_allowed=cloud_allowed,
        cloud_unsafe_warning=cloud_unsafe,
        storage_policy=build_storage_policy(settings),
    )


@router.post("/privacy/cleanup", response_model=PiiCleanupResponse)
async def run_privacy_cleanup() -> PiiCleanupResponse:
    settings = get_settings()
    deleted_reports, deleted_artifacts = cleanup_expired_pii_reports(settings)
    return PiiCleanupResponse(
        deleted_reports=deleted_reports,
        deleted_artifacts=deleted_artifacts,
        message=f"Removed {deleted_reports} reports and {deleted_artifacts} artifacts",
    )


@router.get("/{project_id}/pii-report", response_model=PIIReportPublic)
async def get_pii_report(project_id: UUID) -> PIIReportPublic:
    repo = get_contract_repository()
    cached = await repo.get_pii_report(project_id)
    if cached:
        return to_public_report(cached)

    extraction = await repo.get_extraction(project_id)
    if not extraction:
        raise HTTPException(404, "ExtractionResult not found. Upload materials first.")

    stage: PIIStageService = get_pii_stage()
    report, _summary = await stage.prescan(extraction)
    await repo.save_pii_report(report)
    return to_public_report(report)


@router.post("/{project_id}/pii-prescan", response_model=PIIReportPublic)
async def run_pii_prescan(project_id: UUID) -> PIIReportPublic:
    repo = get_contract_repository()
    extraction = await repo.get_extraction(project_id)
    if not extraction:
        raise HTTPException(404, "ExtractionResult not found. Upload materials first.")

    stage = get_pii_stage()
    report, _summary = await stage.prescan(extraction)
    await repo.save_pii_report(report)
    return to_public_report(report)


@router.get("/{project_id}/safe-cloud-payload", response_model=SafeCloudPayloadPreview)
async def get_safe_cloud_payload(project_id: UUID) -> SafeCloudPayloadPreview:
    repo = get_contract_repository()
    extraction = await repo.get_extraction(project_id)
    if not extraction:
        raise HTTPException(404, "ExtractionResult not found. Upload materials first.")

    report = await repo.get_pii_report(project_id)
    service = get_safe_cloud_payload_service()
    llm_builder = get_llm_contract_builder()
    return await service.build_preview(project_id, extraction, report, llm_builder)
