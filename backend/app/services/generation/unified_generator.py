"""Unified landing generation pipeline (Stage F + G)."""

import logging
from uuid import UUID

from app.schemas.generation import GeneratedLanding
from app.schemas.semantic_responses import SemanticGenerationResponse
from app.services.analysis.llm_contract_builder import LLMContractBuilderService
from app.services.domain.engine import DomainIntelligenceEngine
from app.services.generation.stub_generator import StubGenerationService
from app.services.semantic.generator import SemanticGenerationEngine

logger = logging.getLogger(__name__)


class UnifiedGenerationService:
    """One-click: optional enrich → domain intelligence → semantic → topology → landing."""

    def __init__(
        self,
        semantic_engine: SemanticGenerationEngine,
        stub_generator: StubGenerationService,
        llm_builder: LLMContractBuilderService | None = None,
        domain_engine: DomainIntelligenceEngine | None = None,
    ) -> None:
        self._semantic = semantic_engine
        self._stub = stub_generator
        self._llm = llm_builder
        self._domain = domain_engine

    async def generate_full(
        self,
        project_id: UUID,
        *,
        enrich: bool = False,
    ) -> SemanticGenerationResponse:
        if enrich and self._llm:
            try:
                await self._llm.enrich(project_id)
            except Exception as exc:
                logger.warning("Optional enrich skipped: %s", exc)

        domain_report = None
        if self._domain:
            contract = await self._semantic._repo.get_contract(project_id)
            if contract:
                domain_report = await self._domain.get_or_analyze(project_id, contract)

        return await self._semantic.generate(project_id, domain_report=domain_report)

    async def generate_stub(self, project_id: UUID) -> GeneratedLanding:
        return await self._stub.generate(project_id)
