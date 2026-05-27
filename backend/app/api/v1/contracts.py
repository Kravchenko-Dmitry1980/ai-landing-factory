from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.core.dependencies import (
    get_contract_builder,
    get_contract_repository,
    get_generation_service,
    get_llm_contract_builder,
    get_semantic_engine,
    get_team_review_service,
    get_unified_generator,
)
from app.schemas.evidence_visibility import EvidenceVisibilityResponse
from app.schemas.team_review import (
    ManualTeamUpdateRequest,
    TeamBulkActionRequest,
    TeamReviewActionResponse,
    TeamReviewResponse,
)
from app.schemas.fidelity import ContractCompletenessReport, SourceStructureReport
from app.services.evidence.evidence_visibility import EvidenceVisibilityBuilder
from app.schemas.generation_responses import (
    ArchitectureResponse,
    GenerateRequest,
    SemanticDebugResponse,
    UnifiedGenerateResponse,
)
from app.schemas.landing_contract import LandingContract, LandingContractUpdate
from app.schemas.generation import GeneratedLanding
from app.schemas.responses import EnrichmentResponse
from app.schemas.semantic_generation import GeneratedSemanticLanding
from app.schemas.semantic_responses import SemanticGenerationResponse
from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate

router = APIRouter()


@router.get("/{project_id}/contract-completeness", response_model=ContractCompletenessReport)
async def get_contract_completeness(project_id: UUID) -> ContractCompletenessReport:
    contract = await get_contract_repository().get_contract(project_id)
    if not contract:
        raise HTTPException(404, "LandingContract not found")
    if contract.fidelity and contract.fidelity.completeness:
        return contract.fidelity.completeness
    return ContractCompletenessGate().evaluate(contract)


@router.get("/{project_id}/evidence-report", response_model=EvidenceVisibilityResponse)
async def get_evidence_report(project_id: UUID) -> EvidenceVisibilityResponse:
    contract = await get_contract_repository().get_contract(project_id)
    if not contract:
        raise HTTPException(404, "LandingContract not found")
    return EvidenceVisibilityBuilder().build(contract)


@router.get("/{project_id}/team-review", response_model=TeamReviewResponse)
async def get_team_review(project_id: UUID) -> TeamReviewResponse:
    try:
        return await get_team_review_service().get_review(project_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post(
    "/{project_id}/team-review/bulk-action",
    response_model=TeamReviewActionResponse,
)
async def team_review_bulk_action(
    project_id: UUID,
    body: TeamBulkActionRequest,
) -> TeamReviewActionResponse:
    try:
        result = await get_team_review_service().apply_bulk_action(
            project_id, body.action
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    await get_generation_service().generate(project_id)
    return result


@router.post(
    "/{project_id}/team-review/manual-text",
    response_model=TeamReviewActionResponse,
)
async def team_review_manual_text(
    project_id: UUID,
    body: ManualTeamUpdateRequest,
) -> TeamReviewActionResponse:
    try:
        result = await get_team_review_service().apply_manual_text(
            project_id, body.text
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    await get_generation_service().generate(project_id)
    return result


@router.get("/{project_id}/source-structure", response_model=SourceStructureReport)
async def get_source_structure(project_id: UUID) -> SourceStructureReport:
    extraction = await get_contract_repository().get_extraction(project_id)
    if not extraction:
        raise HTTPException(404, "ExtractionResult not found")
    return get_contract_builder().build_source_structure(extraction)


@router.post("/{project_id}/reparse-structured-landing", response_model=LandingContract)
async def reparse_structured_landing(project_id: UUID) -> LandingContract:
    contract = await get_contract_builder().reparse_structured(project_id)
    if not contract:
        raise HTTPException(404, "ExtractionResult not found")
    await get_generation_service().generate(project_id)
    return contract


@router.patch("/{project_id}/contract", response_model=LandingContract)
async def update_contract(
    project_id: UUID,
    body: LandingContractUpdate,
) -> LandingContract:
    builder = get_contract_builder()
    updated = await builder.update_contract(
        project_id,
        blocks=body.blocks,
        style=body.style,
        client=body.client,
        goals=body.goals,
        presentation_style=body.presentation_style,
    )
    if not updated:
        raise HTTPException(404, "LandingContract not found")
    return updated


@router.post("/{project_id}/contract/enrich", response_model=EnrichmentResponse)
async def enrich_contract(project_id: UUID) -> EnrichmentResponse:
    try:
        result = await get_llm_contract_builder().enrich(project_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    await get_generation_service().generate(project_id)
    return result


@router.post("/{project_id}/semantic-generate", response_model=SemanticGenerationResponse)
async def semantic_generate(project_id: UUID) -> SemanticGenerationResponse:
    contract = await get_contract_repository().get_contract(project_id)
    if not contract:
        raise HTTPException(404, "LandingContract not found")
    try:
        return await get_semantic_engine().generate(project_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/{project_id}/semantic-landing", response_model=GeneratedSemanticLanding)
async def get_semantic_landing(project_id: UUID) -> GeneratedSemanticLanding:
    semantic = await get_contract_repository().get_semantic(project_id)
    if not semantic:
        raise HTTPException(404, "GeneratedSemanticLanding not found")
    return semantic


@router.post("/{project_id}/generate", response_model=UnifiedGenerateResponse)
async def regenerate_landing(
    project_id: UUID,
    body: GenerateRequest | None = None,
) -> UnifiedGenerateResponse:
    contract = await get_contract_repository().get_contract(project_id)
    if not contract:
        raise HTTPException(404, "LandingContract not found")

    req = body or GenerateRequest()
    unified = get_unified_generator()

    if req.mode == "stub":
        try:
            landing = await unified.generate_stub(project_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        semantic = await get_contract_repository().get_semantic(project_id)
        return UnifiedGenerateResponse(
            semantic=semantic,
            landing=landing,
            architecture=semantic.architecture if semantic else None,
            message="Landing regenerated from contract (stub mode).",
        )

    try:
        result = await unified.generate_full(project_id, enrich=req.enrich)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

    return UnifiedGenerateResponse(
        semantic=result.semantic,
        landing=result.landing,
        architecture=result.semantic.architecture,
        message=result.message,
    )


@router.get("/{project_id}/architecture", response_model=ArchitectureResponse)
async def get_architecture(project_id: UUID) -> ArchitectureResponse:
    semantic = await get_contract_repository().get_semantic(project_id)
    if not semantic:
        raise HTTPException(404, "Architecture topology not found")
    arch = semantic.architecture
    return ArchitectureResponse(
        project_id=str(project_id),
        architecture=arch,
        has_topology=arch is not None and len(arch.nodes) > 0,
    )


@router.get("/{project_id}/semantic-debug", response_model=SemanticDebugResponse)
async def get_semantic_debug(project_id: UUID) -> SemanticDebugResponse:
    semantic = await get_contract_repository().get_semantic(project_id)
    if not semantic:
        raise HTTPException(404, "GeneratedSemanticLanding not found")
    warnings = list(semantic.architecture.warnings) if semantic.architecture else []
    return SemanticDebugResponse(
        semantic=semantic,
        architecture=semantic.architecture,
        topology_warnings=warnings,
    )
