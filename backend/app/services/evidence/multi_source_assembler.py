"""Orchestrate multi-source evidence assembly into LandingContract."""

from __future__ import annotations

import logging

from app.models.domain import utc_now
from app.schemas.evidence import EvidenceAssemblyReport
from app.schemas.extraction import ExtractionResult
from app.schemas.fidelity import DetectionResult, FidelityMetadata
from app.schemas.landing_contract import ContractStatus, LandingBlock, LandingContract
from app.schemas.style_config import default_style_config
from app.services.contract_fidelity.stack_parser import stack_to_bullets
from app.services.contract_fidelity.team_parser import team_to_bullets
from app.services.evidence.evidence_extractor import EvidenceExtractor
from app.services.evidence.field_assembler import FieldAssembler
from app.services.evidence.field_evidence_builder import FieldEvidenceBuilder
from app.services.evidence.gap_analyzer import GapAnalyzer
from app.services.evidence.source_inventory import SourceInventoryBuilder

logger = logging.getLogger(__name__)

ASSEMBLY_CONFIDENCE_THRESHOLD = 0.45


class MultiSourceEvidenceAssembler:
    """Build LandingContract from all extraction files via evidence layer."""

    def __init__(self) -> None:
        self._inventory_builder = SourceInventoryBuilder()
        self._evidence_extractor = EvidenceExtractor()
        self._field_evidence_builder = FieldEvidenceBuilder()
        self._field_assembler = FieldAssembler()
        self._gap_analyzer = GapAnalyzer()

    def assemble(
        self,
        extraction: ExtractionResult,
        *,
        detection: DetectionResult | None = None,
    ) -> tuple[LandingContract, EvidenceAssemblyReport]:
        inventory = self._inventory_builder.build(extraction)
        evidence_items = self._evidence_extractor.extract(extraction, inventory)
        field_evidence = self._field_evidence_builder.build(evidence_items, inventory)
        assembled, traces = self._field_assembler.assemble_all(field_evidence, inventory)

        fe_team = field_evidence.get("team")
        team_evidence_exists = bool(fe_team and fe_team.items)

        missing, weak, strong, warnings = self._gap_analyzer.analyze(
            assembled,
            field_evidence,
            team_evidence_exists=team_evidence_exists,
        )

        confidence = _assembly_confidence(strong, weak, missing, len(evidence_items))

        report = EvidenceAssemblyReport(
            project_id=str(extraction.project_id) if extraction.project_id else None,
            sources=inventory,
            total_evidence_items=len(evidence_items),
            fields=field_evidence,
            missing_fields=missing,
            weak_fields=weak,
            strong_fields=strong,
            parser_strategy="multi_source_assembly",
            confidence=confidence,
            warnings=warnings,
            field_traces=traces,
        )

        contract = self._to_contract(extraction, assembled, report, detection)
        logger.info(
            "Multi-source assembly for %s: sources=%d evidence=%d confidence=%.2f",
            extraction.project_id,
            len(inventory),
            len(evidence_items),
            confidence,
        )
        return contract, report

    def _to_contract(
        self,
        extraction: ExtractionResult,
        assembled: dict[str, object],
        report: EvidenceAssemblyReport,
        detection: DetectionResult | None,
    ) -> LandingContract:
        modules = assembled.get("modules") or []
        if not isinstance(modules, list):
            modules = []
        team = assembled.get("team") or []
        if not isinstance(team, list):
            team = []
        stack = assembled.get("tech_stack") or {}
        if not isinstance(stack, dict):
            stack = {}

        stack_bullets = stack_to_bullets(stack)
        team_bullets = team_to_bullets(team)

        def _list_field(key: str) -> list[str]:
            val = assembled.get(key)
            return val if isinstance(val, list) else []

        blocks = [
            LandingBlock(
                key="essence",
                title="Суть проекта",
                content=str(assembled.get("essence") or ""),
                bullets=[],
            ),
            LandingBlock(key="tasks", title="Задачи проекта", content="", bullets=_list_field("tasks")),
            LandingBlock(key="purpose", title="Для чего", content="", bullets=_list_field("purpose")),
            LandingBlock(key="inputs", title="Вводные данные", content="", bullets=_list_field("inputs")),
            LandingBlock(key="outputs", title="Выходные данные", content="", bullets=_list_field("outputs")),
            LandingBlock(key="results", title="Результаты проекта", content="", bullets=_list_field("results")),
            LandingBlock(key="outlook", title="Перспектива развития", content="", bullets=_list_field("outlook")),
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
                content=str(assembled.get("tagline") or assembled.get("title") or ""),
                bullets=[],
            ),
        ]

        fidelity = FidelityMetadata(
            parser_mode="multi_source_assembly",
            detection=detection,
            modules=modules,
            team_structured=team,
            tech_stack_grouped=stack,
            source_count=len(report.sources),
            evidence_count=report.total_evidence_items,
            source_types=list(dict.fromkeys(s.detected_source_type for s in report.sources)),
            field_sources=report.field_traces,
            missing_fields=report.missing_fields,
            weak_fields=report.weak_fields,
            assembly_confidence=report.confidence,
            evidence_report=report,
        )

        goals = [m.name for m in modules if hasattr(m, "name")] or extraction.payload.goals

        return LandingContract(
            project_id=extraction.project_id,
            status=ContractStatus.DRAFT,
            title=assembled.get("title"),
            client=assembled.get("client"),
            timeline=assembled.get("timeline"),
            lead=assembled.get("lead"),
            quote=str(assembled.get("tagline") or "") or None,
            goals=goals,
            presentation_style=extraction.payload.presentation_style,
            style_config=default_style_config(),
            visual_assets=extraction.payload.visual_assets,
            blocks=blocks,
            fidelity=fidelity,
            updated_at=utc_now(),
        )


def _assembly_confidence(
    strong: list[str],
    weak: list[str],
    missing: list[str],
    evidence_count: int,
) -> float:
    base = len(strong) * 0.08 + len(weak) * 0.03
    penalty = len(missing) * 0.04
    ev_boost = min(evidence_count / 30.0, 0.25)
    return round(min(max(base - penalty + ev_boost, 0.1), 1.0), 3)
