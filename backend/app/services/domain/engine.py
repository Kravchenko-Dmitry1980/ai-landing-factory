"""Domain Intelligence Layer orchestrator — Stage G."""

import logging
from uuid import UUID

from app.config import Settings
from app.models.domain import utc_now
from app.repositories.domain_repository import DomainRepository
from app.schemas.domain_intelligence import DomainIntelligenceReport, ProjectKnowledgeGraph
from app.schemas.landing_contract import LandingContract
from app.schemas.pii import PrivacyMode
from app.services.domain.domain_validator import validate_report
from app.services.domain.fallback_domain_engine import build_fallback_report
from app.services.domain.knowledge_graph_builder import build_knowledge_graph
from app.services.pipeline.pii_stage import PIIStageService

logger = logging.getLogger(__name__)


class DomainIntelligenceEngine:
    def __init__(
        self,
        settings: Settings,
        repository: DomainRepository,
        pii_stage: PIIStageService | None = None,
    ) -> None:
        self._settings = settings
        self._repo = repository
        self._pii = pii_stage

    def is_stale(self, report: DomainIntelligenceReport | None, contract: LandingContract) -> bool:
        if not report or not report.created_at:
            return True
        if report.project_id != contract.project_id:
            return True
        contract_ts = contract.updated_at
        if contract_ts and report.created_at < contract_ts:
            return True
        return False

    async def analyze(
        self,
        contract: LandingContract,
        *,
        force: bool = False,
    ) -> DomainIntelligenceReport:
        if not self._settings.domain_intelligence_enabled:
            report = build_fallback_report(contract)
            await self._repo.save_report(report)
            return report

        existing = await self._repo.get_report(contract.project_id)
        if existing and not force and not self.is_stale(existing, contract):
            return existing

        use_llm = (
            self._settings.domain_use_llm
            and self._settings.llm_enabled
            and (not self._pii or self._pii.privacy_mode != PrivacyMode.LOCAL_ONLY)
        )
        if self._pii and self._pii.privacy_mode == PrivacyMode.LOCAL_ONLY:
            use_llm = False

        assumptions: list[str] = []
        if not use_llm:
            assumptions.append("Deterministic domain analysis (LLM disabled or LOCAL_ONLY)")

        graph = build_knowledge_graph(contract, self._settings)
        report = DomainIntelligenceReport(
            project_id=contract.project_id,
            status="completed",
            graph=graph,
            assumptions=assumptions,
            created_at=utc_now(),
        )
        report = validate_report(report, contract)
        await self._repo.save_report(report)
        await self._repo.save_knowledge_graph(graph)
        logger.info(
            "Domain analysis complete for %s: domain=%s entities=%d",
            contract.project_id,
            graph.domain_profile.primary_domain.value,
            len(graph.entities),
        )
        return report

    async def get_or_analyze(self, project_id: UUID, contract: LandingContract) -> DomainIntelligenceReport:
        existing = await self._repo.get_report(project_id)
        if existing and not self.is_stale(existing, contract):
            return existing
        return await self.analyze(contract)

    async def get_report(self, project_id: UUID) -> DomainIntelligenceReport | None:
        return await self._repo.get_report(project_id)

    async def get_graph(self, project_id: UUID) -> ProjectKnowledgeGraph | None:
        return await self._repo.get_knowledge_graph(project_id)
