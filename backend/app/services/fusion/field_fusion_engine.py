"""Field-level multi-source fusion engine — contract-level symbiosis."""

from __future__ import annotations

import logging

from app.models.domain import utc_now
from app.schemas.evidence import EvidenceAssemblyReport, SourceInventoryItem
from app.schemas.extraction import ExtractionResult
from app.schemas.fidelity import DetectionResult, FidelityMetadata, LandingModule, TeamMember
from app.schemas.fusion import FieldName, FinalFusionResult, FusionTrace
from app.schemas.landing_contract import ContractStatus, LandingBlock, LandingContract
from app.schemas.style_config import default_style_config
from app.services.contract_fidelity.stack_parser import stack_to_bullets
from app.services.contract_fidelity.team_parser import team_to_bullets
from app.services.fusion.completeness_critic import CompletenessCritic
from app.services.fusion.conflict_resolver import ConflictResolver
from app.services.fusion.field_candidate import FieldCandidateBuilder
from app.services.fusion.field_strategies import FieldStrategies
from app.services.fusion.fusion_trace import build_field_sources

logger = logging.getLogger(__name__)


class FieldFusionEngine:
    """Fuse per-field best values from multiple parser-level contract candidates."""

    def __init__(self) -> None:
        self._candidate_builder = FieldCandidateBuilder()
        self._strategies = FieldStrategies()
        self._conflicts = ConflictResolver()
        self._critic = CompletenessCritic()

    def fuse(
        self,
        extraction: ExtractionResult,
        inventory: list[SourceInventoryItem],
        candidates: dict[str, LandingContract],
        *,
        evidence_report: EvidenceAssemblyReport | None = None,
        detection: DetectionResult | None = None,
        base_contract: LandingContract | None = None,
    ) -> FinalFusionResult:
        if not candidates:
            raise ValueError("FieldFusionEngine requires at least one candidate contract")

        by_field = self._candidate_builder.build_from_contracts(candidates, inventory)
        field_decisions = {}
        fused_values: dict[str, object] = {}
        all_conflicts = []

        for field_name in FieldName.ALL:
            field_candidates = by_field.get(field_name, [])
            if not field_candidates:
                continue
            value, decision = self._strategies.fuse_field(field_name, field_candidates)
            if self._is_empty(value):
                continue
            fused_values[field_name] = value
            field_decisions[field_name] = decision
            all_conflicts.extend(
                self._conflicts.detect_conflicts(field_name, field_candidates, decision)
            )

        contract = self._build_contract(
            extraction,
            fused_values,
            inventory,
            detection,
            evidence_report,
            base_contract or next(iter(candidates.values())),
        )

        completeness = self._critic.evaluate(contract)
        contract.fidelity = contract.fidelity or FidelityMetadata()
        contract.fidelity.completeness = completeness
        missing, weak = self._critic.missing_and_weak(completeness)

        trace = FusionTrace(
            source_count=len(inventory),
            candidate_count=len(candidates),
            field_decisions=field_decisions,
            conflicts=all_conflicts,
            missing_fields=missing,
            weak_fields=weak,
            final_completeness=completeness.score,
            original_parser_modes=sorted(
                {
                    c.fidelity.parser_mode
                    for c in candidates.values()
                    if c.fidelity and c.fidelity.parser_mode
                }
            ),
        )

        if contract.fidelity:
            contract.fidelity.parser_mode = "field_level_fusion"
            contract.fidelity.missing_fields = missing
            contract.fidelity.weak_fields = weak
            contract.fidelity.field_sources = build_field_sources(trace)
            contract.fidelity.fusion_trace = trace
            contract.fidelity.field_decisions = {
                k: v.model_dump() for k, v in field_decisions.items()
            }
            if evidence_report:
                contract.fidelity.evidence_report = evidence_report
                contract.fidelity.assembly_confidence = evidence_report.confidence
                contract.fidelity.evidence_count = evidence_report.total_evidence_items
            contract.fidelity.source_count = len(inventory)
            contract.fidelity.source_types = list(
                dict.fromkeys(s.detected_source_type for s in inventory)
            )

        logger.info(
            "Field-level fusion for %s: sources=%d candidates=%d completeness=%d",
            extraction.project_id,
            len(inventory),
            len(candidates),
            completeness.score,
        )
        return FinalFusionResult(contract=contract, trace=trace)

    def _build_contract(
        self,
        extraction: ExtractionResult,
        fused: dict[str, object],
        inventory: list[SourceInventoryItem],
        detection: DetectionResult | None,
        evidence_report: EvidenceAssemblyReport | None,
        base: LandingContract,
    ) -> LandingContract:
        modules = fused.get("modules") or []
        if not isinstance(modules, list):
            modules = []
        team = fused.get("team") or []
        if not isinstance(team, list):
            team = []
        stack = fused.get("tech_stack") or {}
        if not isinstance(stack, dict):
            stack = {}

        stack_bullets = stack_to_bullets(stack)
        team_bullets = team_to_bullets(team)

        def _list_field(key: str) -> list[str]:
            val = fused.get(key)
            return val if isinstance(val, list) else []

        blocks = [
            LandingBlock(
                key="essence",
                title="Суть проекта",
                content=str(fused.get("essence") or ""),
                bullets=[],
            ),
            LandingBlock(key="tasks", title="Задачи проекта", content="", bullets=_list_field("tasks")),
            LandingBlock(key="purpose", title="Для чего", content="", bullets=_list_field("purpose")),
            LandingBlock(key="inputs", title="Вводные данные", content="", bullets=_list_field("inputs")),
            LandingBlock(key="outputs", title="Выходные данные", content="", bullets=_list_field("outputs")),
            LandingBlock(
                key="results",
                title="Результаты проекта",
                content="",
                bullets=_list_field("results"),
            ),
            LandingBlock(
                key="outlook",
                title="Перспектива развития",
                content="",
                bullets=_list_field("outlook"),
            ),
            LandingBlock(
                key="tech_stack",
                title="Используемый технологический стек",
                content="",
                bullets=stack_bullets,
            ),
            LandingBlock(key="team", title="Команда проекта", content="", bullets=team_bullets),
            LandingBlock(
                key="tagline",
                title="Фраза проекта",
                content=str(fused.get("quote") or fused.get("title") or ""),
                bullets=[],
            ),
        ]

        module_objs = [m for m in modules if isinstance(m, LandingModule)]
        team_objs = [m for m in team if isinstance(m, TeamMember)]
        goals = [m.name for m in module_objs] or base.goals or extraction.payload.goals

        fidelity = FidelityMetadata(
            parser_mode="field_level_fusion",
            detection=detection or (base.fidelity.detection if base.fidelity else None),
            modules=module_objs,
            team_structured=team_objs,
            tech_stack_grouped=stack,
            source_count=len(inventory),
            evidence_count=evidence_report.total_evidence_items if evidence_report else 0,
            source_types=list(dict.fromkeys(s.detected_source_type for s in inventory)),
            evidence_report=evidence_report,
            assembly_confidence=evidence_report.confidence if evidence_report else 0.0,
        )

        return LandingContract(
            project_id=extraction.project_id,
            status=ContractStatus.DRAFT,
            title=fused.get("title") or base.title,
            client=fused.get("client") or base.client,
            timeline=fused.get("timeline") or base.timeline,
            lead=fused.get("lead") or base.lead,
            quote=str(fused.get("quote") or "") or base.quote,
            goals=goals,
            presentation_style=extraction.payload.presentation_style or base.presentation_style,
            style_config=base.style_config or default_style_config(),
            visual_assets=extraction.payload.visual_assets or base.visual_assets,
            blocks=blocks,
            fidelity=fidelity,
            updated_at=utc_now(),
        )

    def _is_empty(self, value: object) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        if isinstance(value, (list, dict)):
            return len(value) == 0
        return False
