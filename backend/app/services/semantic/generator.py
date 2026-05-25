"""Semantic AI Generation Engine — Stage E orchestrator."""

import logging
from uuid import UUID

from app.config import Settings
from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
from app.repositories.domain_repository import DomainRepository
from app.schemas.generation import GeneratedLanding
from app.schemas.landing_contract import LandingContract
from app.schemas.pii import PrivacyMode
from app.schemas.semantic_generation import GeneratedSemanticLanding
from app.schemas.semantic_responses import SemanticGenerationResponse
from app.services.domain.domain_mapper import map_to_semantic_domain
from app.services.domain.engine import DomainIntelligenceEngine
from app.services.domain.semantic_enricher import apply_domain_intelligence
from app.services.llm.errors import LLMError, LLMUnavailableError
from app.services.llm.openai_client import OpenAIClient
from app.services.pipeline.pii_stage import PIIStageService
from app.services.prompts.engine import PromptEngine
from app.services.semantic.domain_classifier import classify_domain
from app.services.semantic.fallback_generator import generate_fallback_semantic
from app.services.semantic.hallucination_guard import guard_hallucinations
from app.services.semantic.landing_bridge import semantic_to_landing
from app.services.semantic.mock_semantic_llm import MockSemanticLLMClient
from app.services.semantic.narrative_builder import build_narrative
from app.services.semantic.prompt_builder import build_safe_contract_payload, build_semantic_prompts
from app.services.semantic.section_planner import layout_for_domain, plan_sections, style_for_domain
from app.services.architecture.topology_builder import enrich_semantic_topology
from app.services.semantic.semantic_validator import try_parse_semantic, validate_semantic_llm_output

logger = logging.getLogger(__name__)


class SemanticGenerationEngine:
    def __init__(
        self,
        settings: Settings,
        repository: ContractRepository,
        pii_stage: PIIStageService | None = None,
        prompt_engine: PromptEngine | None = None,
        domain_engine: DomainIntelligenceEngine | None = None,
    ) -> None:
        self._settings = settings
        self._repo = repository
        self._pii = pii_stage or PIIStageService(settings)
        self._prompts = prompt_engine or PromptEngine()
        self._domain = domain_engine or DomainIntelligenceEngine(
            settings, DomainRepository(settings), self._pii
        )

    async def generate(
        self,
        project_id: UUID,
        *,
        domain_report=None,
    ) -> SemanticGenerationResponse:
        contract = await self._repo.get_contract(project_id)
        if not contract:
            raise ValueError("LandingContract not found")

        if domain_report is None and self._settings.domain_intelligence_enabled:
            domain_report = await self._domain.get_or_analyze(project_id, contract)

        if domain_report and domain_report.graph.domain_profile.primary_domain.value != "general":
            semantic_domain = map_to_semantic_domain(domain_report.graph.domain_profile.primary_domain)
            classification_confidence = domain_report.graph.domain_profile.confidence
            classification_signals = domain_report.graph.domain_profile.evidence
        else:
            legacy = classify_domain(contract)
            semantic_domain = legacy.domain
            classification_confidence = legacy.confidence
            classification_signals = legacy.signals

        narrative = build_narrative(contract)
        section_plan = plan_sections(semantic_domain)

        use_llm = (
            self._settings.semantic_generation_enabled
            and self._settings.semantic_use_llm
            and self._settings.llm_enabled
        )
        provider = (self._settings.llm_provider or "mock").lower()

        if (
            use_llm
            and provider == "openai"
            and self._pii.privacy_mode == PrivacyMode.LOCAL_ONLY
        ):
            semantic = self._fallback(contract, semantic_domain, "LOCAL_ONLY blocks cloud LLM")
            semantic = self._finalize(contract, semantic, domain_report)
            landing, semantic = await self._persist(project_id, contract, semantic, domain_report)
            return SemanticGenerationResponse(
                semantic=semantic,
                landing=landing,
                message="LOCAL_ONLY: semantic fallback (cloud blocked).",
            )

        if not self._settings.semantic_generation_enabled or not use_llm:
            semantic = self._fallback(
                contract,
                semantic_domain,
                "semantic LLM disabled — deterministic fallback",
            )
            semantic = self._finalize(contract, semantic, domain_report)
            landing, semantic = await self._persist(project_id, contract, semantic, domain_report)
            return SemanticGenerationResponse(
                semantic=semantic,
                landing=landing,
                message="Semantic generation via fallback (LLM disabled).",
            )

        try:
            semantic = await self._generate_with_llm(
                contract,
                semantic_domain,
                section_plan,
                narrative,
                provider,
            )
            msg = f"Semantic landing generated via {provider}."
        except (LLMError, LLMUnavailableError, ValueError, Exception) as exc:
            logger.warning("Semantic LLM failed: %s", exc)
            semantic = self._fallback(contract, semantic_domain, str(exc))
            msg = f"Semantic LLM failed ({exc}). Fallback applied."

        semantic = self._finalize(contract, semantic, domain_report)
        landing, semantic = await self._persist(project_id, contract, semantic, domain_report)
        return SemanticGenerationResponse(semantic=semantic, landing=landing, message=msg)

    async def _generate_with_llm(
        self,
        contract: LandingContract,
        domain,
        section_plan,
        narrative,
        provider: str,
    ) -> GeneratedSemanticLanding:
        detector = self._pii._detector if self._pii else None
        safe_payload = build_safe_contract_payload(
            contract,
            detector,
        )
        templates_dir = self._prompts._dir
        system, user = build_semantic_prompts(
            safe_payload,
            domain.value if hasattr(domain, "value") else str(domain),
            [s.value for s in section_plan],
            narrative.model_dump_json(),
            templates_dir,
        )

        if provider == "openai":
            client = OpenAIClient(self._settings)
        else:
            client = MockSemanticLLMClient(contract)

        raw = await client.generate_json(system, user, "semantic_landing")
        parsed = try_parse_semantic(raw, project_id=contract.project_id)
        if not parsed:
            parsed = validate_semantic_llm_output(raw, project_id=contract.project_id)
        parsed.project_id = contract.project_id
        parsed.domain = domain
        parsed.layout_preset = layout_for_domain(domain)
        parsed.style_profile = style_for_domain(domain)
        parsed.metadata.provider = provider
        parsed.metadata.llm_enabled = True
        parsed.metadata.fallback_used = False
        parsed.metadata.privacy_redacted = True
        parsed.metadata.generated_at = utc_now()

        report = guard_hallucinations(parsed, contract)
        parsed.sections = report.adjusted_sections
        parsed.metadata.hallucination_warnings = report.warnings
        return parsed

    def _fallback(self, contract: LandingContract, domain, reason: str) -> GeneratedSemanticLanding:
        semantic = generate_fallback_semantic(contract, domain)
        semantic.metadata.assumptions = list(
            dict.fromkeys(semantic.metadata.assumptions + [reason[:200]])
        )
        return semantic

    def _apply_topology(
        self,
        contract: LandingContract,
        semantic: GeneratedSemanticLanding,
        knowledge_graph=None,
    ) -> GeneratedSemanticLanding:
        try:
            return enrich_semantic_topology(contract, semantic, knowledge_graph=knowledge_graph)
        except Exception as exc:
            logger.warning("Topology generation failed: %s", exc)
            return semantic

    def _finalize(self, contract, semantic, domain_report):
        if domain_report and self._settings.domain_intelligence_enabled:
            return apply_domain_intelligence(semantic, contract, domain_report)
        return semantic

    async def _persist(
        self,
        project_id: UUID,
        contract: LandingContract,
        semantic: GeneratedSemanticLanding,
        domain_report=None,
    ) -> tuple[GeneratedLanding, GeneratedSemanticLanding]:
        semantic.project_id = project_id
        kg = domain_report.graph if domain_report else None
        semantic = self._apply_topology(contract, semantic, knowledge_graph=kg)
        landing = semantic_to_landing(semantic, contract)
        await self._repo.save_semantic(semantic)
        await self._repo.save_landing(landing)

        contract.presentation_style = f"layout:{semantic.layout_preset}"
        contract.updated_at = utc_now()
        contract.version += 1
        await self._repo.save_contract(contract)
        return landing, semantic
