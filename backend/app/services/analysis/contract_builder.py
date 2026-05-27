import logging

from uuid import UUID



from app.models.domain import utc_now

from app.repositories.contract_repository import ContractRepository

from app.schemas.extraction import ExtractionResult

from app.schemas.fidelity import (

    DetectionResult,

    FidelityMetadata,

    SectionInfo,

    SourceStructureReport,

)

from app.schemas.landing_contract import ContractStatus, LandingBlock, LandingContract
from app.schemas.style_config import default_style_config

from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate

from app.services.contract_fidelity.landing_document_detector import (

    CONFIDENCE_THRESHOLD,

    LandingDocumentDetector,

)

from app.services.contract_fidelity.presentation_landing_synthesizer import (
    PresentationLandingSynthesizer,
)
from app.services.contract_fidelity.source_type_detector import (
    PRESENTATION_CONFIDENCE_THRESHOLD,
    SourceTypeDetector,
)
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser

from app.services.contract_fidelity.stack_parser import stack_to_bullets

from app.services.contract_fidelity.team_parser import team_to_bullets

from app.services.evidence.multi_source_assembler import (
    ASSEMBLY_CONFIDENCE_THRESHOLD,
    MultiSourceEvidenceAssembler,
)
from app.services.evidence.source_inventory import (
    SourceInventoryBuilder,
    has_single_high_confidence_ready_doc,
)
from app.services.fusion.field_fusion_engine import FieldFusionEngine
from app.services.ocr.ocr_enrichment import OcrEnrichmentService
from app.services.orchestration.document_orchestrator import DocumentOrchestrator
from app.services.visual.visual_evidence_builder import VisualEvidenceBuilder
from app.services.visual.visual_source_classifier import VisualSourceClassifier
from app.services.vlm.vlm_router import VlmEnrichmentService



logger = logging.getLogger(__name__)



BLOCK_SPECS: list[tuple[str, str, str]] = [

    ("essence", "Суть проекта", "essence"),

    ("tasks", "Задачи проекта", "tasks"),

    ("purpose", "Для чего", "purpose"),

    ("inputs", "Вводные данные", "inputs"),

    ("outputs", "Выходные данные", "outputs"),

    ("results", "Результаты проекта", "results"),

    ("outlook", "Перспектива развития", "outlook"),

    ("tech_stack", "Используемый технологический стек", "tech_stack"),

    ("team", "Команда проекта", "team"),

    ("tagline", "Фраза проекта", "tagline"),

]





class ContractBuilderService:

    """Maps ExtractionResult → canonical LandingContract (fidelity-first)."""



    def __init__(self, repository: ContractRepository) -> None:

        self._repo = repository

        self._detector = LandingDocumentDetector()

        self._source_type_detector = SourceTypeDetector()

        self._structured_parser = StructuredLandingParser()

        self._presentation_synthesizer = PresentationLandingSynthesizer()

        self._completeness_gate = ContractCompletenessGate()

        self._inventory_builder = SourceInventoryBuilder()

        self._multi_source_assembler = MultiSourceEvidenceAssembler()

        self._field_fusion_engine = FieldFusionEngine()
        self._document_orchestrator = DocumentOrchestrator()
        self._ocr_enrichment = OcrEnrichmentService()
        self._visual_classifier = VisualSourceClassifier()
        self._vlm_enrichment = VlmEnrichmentService()



    def _ensure_fidelity_deps(self) -> None:

        if not hasattr(self, "_detector"):

            self._detector = LandingDocumentDetector()

        if not hasattr(self, "_source_type_detector"):

            self._source_type_detector = SourceTypeDetector()

        if not hasattr(self, "_structured_parser"):

            self._structured_parser = StructuredLandingParser()

        if not hasattr(self, "_presentation_synthesizer"):

            self._presentation_synthesizer = PresentationLandingSynthesizer()

        if not hasattr(self, "_completeness_gate"):

            self._completeness_gate = ContractCompletenessGate()

        if not hasattr(self, "_inventory_builder"):

            self._inventory_builder = SourceInventoryBuilder()

        if not hasattr(self, "_multi_source_assembler"):

            self._multi_source_assembler = MultiSourceEvidenceAssembler()

        if not hasattr(self, "_field_fusion_engine"):

            self._field_fusion_engine = FieldFusionEngine()

        if not hasattr(self, "_document_orchestrator"):

            self._document_orchestrator = DocumentOrchestrator()
        if not hasattr(self, "_ocr_enrichment"):
            self._ocr_enrichment = OcrEnrichmentService()
        if not hasattr(self, "_visual_classifier"):
            self._visual_classifier = VisualSourceClassifier()
        if not hasattr(self, "_vlm_enrichment"):
            self._vlm_enrichment = VlmEnrichmentService()
        self._document_orchestrator = DocumentOrchestrator()



    def build(self, extraction: ExtractionResult) -> LandingContract:

        self._ensure_fidelity_deps()

        from app.config import settings

        visual_report = None
        ocr_warnings: list[str] = []
        if settings.effective_advanced_visual_pipeline:
            visual_report = self._visual_classifier.classify_extraction(extraction)
            extraction, ocr_warnings = self._ocr_enrichment.enrich(
                extraction,
                visual_report=visual_report,
            )
        extraction, vlm_report = self._vlm_enrichment.enrich(
            extraction,
            visual_report=visual_report,
        )

        text = _primary_extracted_text(extraction)

        file_type = _primary_file_type(extraction)

        detection = self._detector.detect(text)

        source_type = self._source_type_detector.detect(text, file_type=file_type)

        inventory = self._inventory_builder.build(extraction)

        orchestration_trace = self._document_orchestrator.run(extraction)

        use_structured_only = (
            detection.is_structured_landing
            and detection.confidence >= CONFIDENCE_THRESHOLD
            and has_single_high_confidence_ready_doc(inventory)
        )

        if use_structured_only:

            contract = self._build_from_structured(extraction, text, detection)

            logger.info(

                "Structured landing parser used for %s (confidence=%.2f)",

                extraction.project_id,

                detection.confidence,

            )

        else:

            contract, report = self._multi_source_assembler.assemble(
                extraction, detection=detection
            )

            ms_completeness = self._completeness_gate.evaluate(contract)

            if contract.fidelity:

                contract.fidelity.completeness = ms_completeness

            pres_contract = None
            pres_completeness = None

            if (
                source_type.source_type == "project_presentation"
                and source_type.confidence >= PRESENTATION_CONFIDENCE_THRESHOLD
            ):
                pres_contract = self._build_from_presentation(
                    extraction, text, detection, source_type
                )
                pres_completeness = self._completeness_gate.evaluate(pres_contract)

            if len(inventory) >= 2:
                fusion_candidates: dict[str, LandingContract] = {
                    "multi_source": contract,
                }
                if pres_contract:
                    fusion_candidates["presentation"] = pres_contract
                fusion_result = self._field_fusion_engine.fuse(
                    extraction=extraction,
                    inventory=inventory,
                    candidates=fusion_candidates,
                    evidence_report=report,
                    detection=detection,
                    base_contract=contract,
                )
                contract = fusion_result.contract
                logger.info(
                    "Field-level fusion for %s (sources=%d, candidates=%d, score=%d)",
                    extraction.project_id,
                    len(inventory),
                    len(fusion_candidates),
                    fusion_result.trace.final_completeness,
                )
            else:
                ms_score = ms_completeness.score
                pres_score = pres_completeness.score if pres_completeness else 0

                if pres_contract and pres_score > ms_score:
                    ms_contract = contract
                    contract = pres_contract
                    if contract.fidelity:
                        contract.fidelity.evidence_report = report
                        contract.fidelity.completeness = pres_completeness
                    contract = self._merge_team_from_ms_contract(contract, ms_contract)
                    logger.info(
                        "Presentation synthesizer chosen for %s (pres=%d > ms=%d)",
                        extraction.project_id,
                        pres_score,
                        ms_score,
                    )
                elif ms_score >= 70 or (
                    ms_score >= 55 and ms_score >= pres_score
                ):
                    logger.info(
                        "Multi-source evidence assembly for %s "
                        "(completeness=%d, pres=%d, sources=%d)",
                        extraction.project_id,
                        ms_score,
                        pres_score,
                        len(inventory),
                    )
                elif pres_contract:
                    ms_contract = contract
                    contract = pres_contract
                    if contract.fidelity:
                        contract.fidelity.evidence_report = report
                        contract.fidelity.completeness = pres_completeness
                    contract = self._merge_team_from_ms_contract(contract, ms_contract)
                    logger.info(
                        "Presentation fallback for %s (ms=%d)",
                        extraction.project_id,
                        ms_score,
                    )
                else:
                    contract = self._build_heuristic(extraction)
                    contract.fidelity = FidelityMetadata(
                        parser_mode="heuristic",
                        detection=detection,
                        evidence_report=report,
                        source_count=len(inventory),
                        evidence_count=report.total_evidence_items,
                        source_types=[s.detected_source_type for s in inventory],
                        missing_fields=report.missing_fields,
                        weak_fields=report.weak_fields,
                        assembly_confidence=report.confidence,
                        field_sources=report.field_traces,
                        completeness=ms_completeness,
                    )
                    logger.info(
                        "Heuristic fallback for %s (ms=%d, pres=%d)",
                        extraction.project_id,
                        ms_score,
                        pres_score,
                    )



        if not contract.fidelity or contract.fidelity.completeness is None:

            completeness = self._completeness_gate.evaluate(contract)

            if contract.fidelity:

                contract.fidelity.completeness = completeness

            else:

                contract.fidelity = FidelityMetadata(completeness=completeness)

        contract = self._supplement_pptx_team(contract, extraction, text, source_type)

        contract = self._apply_team_verification(contract, extraction)

        contract = self._attach_orchestration_trace(contract, orchestration_trace)
        contract = self._attach_ocr_warnings(contract, ocr_warnings)
        contract = self._attach_visual_evidence(contract, visual_report)
        contract = self._attach_vlm_evidence(contract, vlm_report)

        return contract

    def _apply_team_verification(
        self,
        contract: LandingContract,
        extraction: ExtractionResult,
    ) -> LandingContract:
        """OCR team verification gate — only verified members in team_structured."""
        from app.services.contract_fidelity.team_candidate_validator import filter_team_members
        from app.services.contract_fidelity.team_parser import team_to_bullets
        from app.services.team_verification.export_policy import (
            draft_team_from_report,
            team_publication_warning,
        )
        from app.services.team_verification.team_verification_service import (
            TeamVerificationService,
        )
        from app.schemas.team_review import TeamPublicationMode

        fidelity = contract.fidelity
        if not fidelity or not fidelity.team_structured:
            return contract

        all_members = filter_team_members(fidelity.team_structured)
        if not all_members:
            return contract

        service = TeamVerificationService()
        report = service.verify(all_members, extraction)

        fidelity.team_verification_report = report
        fidelity.ocr_review_candidates = (
            report.review_candidates + report.probable_candidates
        )
        fidelity.team_publication_policy = "verified_only"
        fidelity.team_publication_mode = TeamPublicationMode.draft_auto
        fidelity.accepted_team_candidate_ids = []
        fidelity.manual_team_override = False
        fidelity.manual_team_text = None

        draft_team = draft_team_from_report(report)
        fidelity.team_structured = draft_team if draft_team else all_members
        fidelity.team_review_warning = (
            "Команда извлечена из изображения через OCR. Возможны ошибки в ФИО."
            if report.review_candidates or report.probable_candidates
            else None
        )

        team_bullets = team_to_bullets(fidelity.team_structured)
        for block in contract.blocks:
            if block.key == "team":
                block.bullets = team_bullets
                break

        pub_warning = team_publication_warning(
            report, fidelity.team_publication_mode
        )
        if pub_warning:
            report_ev = fidelity.evidence_report
            if report_ev:
                report_ev.warnings = list(
                    dict.fromkeys(list(report_ev.warnings) + [pub_warning])
                )

        if fidelity.completeness:
            fidelity.completeness = self._completeness_gate.evaluate(contract)

        logger.info(
            "Team verification gate: draft=%d verified=%d review=%d rejected=%d ocr=%d",
            len(fidelity.team_structured),
            report.metrics.verified_count,
            report.metrics.needs_review_count,
            report.metrics.rejected_count,
            report.metrics.ocr_candidates,
        )
        return contract

    def _attach_visual_evidence(
        self,
        contract: LandingContract,
        visual_report,
    ) -> LandingContract:
        if not visual_report or visual_report.visual_items_count <= 0:
            return contract
        if not contract.fidelity:
            contract.fidelity = FidelityMetadata()
        contract.fidelity.visual_evidence_report = visual_report
        contract.fidelity.visual_items_count = visual_report.visual_items_count
        contract.fidelity.vlm_candidates_count = visual_report.vlm_candidates_count
        contract.fidelity.ocr_visual_candidates_count = visual_report.ocr_candidates_count
        report = contract.fidelity.evidence_report
        if report and visual_report.warnings:
            report.warnings = list(
                dict.fromkeys(list(report.warnings) + visual_report.warnings)
            )
        return contract

    def _attach_vlm_evidence(
        self,
        contract: LandingContract,
        vlm_report,
    ) -> LandingContract:
        if vlm_report is None:
            return contract
        if not contract.fidelity:
            contract.fidelity = FidelityMetadata()
        fidelity = contract.fidelity
        fidelity.vlm_extraction_report = vlm_report
        fidelity.vlm_enabled = bool(vlm_report.enabled)
        fidelity.vlm_provider = vlm_report.provider or "disabled"
        fidelity.vlm_processed_count = vlm_report.processed_count
        fidelity.vlm_skipped_count = vlm_report.skipped_count
        if vlm_report.warnings:
            report = fidelity.evidence_report
            if report:
                report.warnings = list(
                    dict.fromkeys(list(report.warnings) + vlm_report.warnings)
                )
        return contract

    def _attach_ocr_warnings(
        self,
        contract: LandingContract,
        ocr_warnings: list[str],
    ) -> LandingContract:
        if not ocr_warnings:
            return contract
        if not contract.fidelity:
            contract.fidelity = FidelityMetadata()
        report = contract.fidelity.evidence_report
        if report:
            report.warnings = list(dict.fromkeys(list(report.warnings) + ocr_warnings))
        trace = contract.fidelity.orchestration_trace
        if trace:
            trace.global_warnings = list(
                dict.fromkeys(list(trace.global_warnings or []) + ocr_warnings)
            )
        return contract

    def _attach_orchestration_trace(
        self,
        contract: LandingContract,
        trace,
    ) -> LandingContract:
        if not contract.fidelity:
            contract.fidelity = FidelityMetadata()
        contract.fidelity.orchestration_trace = trace
        report = contract.fidelity.evidence_report
        if report and trace.global_warnings:
            merged = list(dict.fromkeys(list(report.warnings) + trace.global_warnings))
            report.warnings = merged
        return contract

    def _merge_team_from_ms_contract(
        self,
        contract: LandingContract,
        ms_contract: LandingContract,
    ) -> LandingContract:
        """Keep team from multi-source assembly when presentation path wins overall."""
        from app.services.contract_fidelity.team_candidate_validator import filter_team_members

        ms_fidelity = ms_contract.fidelity
        if not ms_fidelity or not ms_fidelity.team_structured:
            return contract

        ms_team = filter_team_members(ms_fidelity.team_structured)
        if not ms_team:
            return contract

        fidelity = contract.fidelity
        existing = (
            filter_team_members(fidelity.team_structured)
            if fidelity and fidelity.team_structured
            else []
        )
        if len(existing) >= len(ms_team):
            return contract

        if not fidelity:
            contract.fidelity = FidelityMetadata(team_structured=ms_team)
            fidelity = contract.fidelity
        else:
            fidelity.team_structured = ms_team

        team_bullets = team_to_bullets(ms_team)
        updated = False
        for block in contract.blocks:
            if block.key == "team":
                block.bullets = team_bullets
                updated = True
                break
        if not updated:
            contract.blocks.append(
                LandingBlock(
                    key="team",
                    title="Команда проекта",
                    content="",
                    bullets=team_bullets,
                )
            )

        if fidelity.missing_fields and "team" in fidelity.missing_fields:
            fidelity.missing_fields = [f for f in fidelity.missing_fields if f != "team"]
        if fidelity.weak_fields and "team" in fidelity.weak_fields:
            fidelity.weak_fields = [f for f in fidelity.weak_fields if f != "team"]

        report = fidelity.evidence_report
        if report:
            if "team" in report.missing_fields:
                report.missing_fields = [f for f in report.missing_fields if f != "team"]
            if "team" not in report.strong_fields and ms_team:
                report.strong_fields = list(report.strong_fields) + ["team"]

        fidelity.completeness = self._completeness_gate.evaluate(contract)
        logger.info(
            "Merged team from multi-source assembly (%d members) for %s",
            len(ms_team),
            contract.project_id,
        )
        return contract

    def _supplement_pptx_team(
        self,
        contract: LandingContract,
        extraction: ExtractionResult,
        text: str,
        source_type,
    ) -> LandingContract:
        """If PPTX-only contract has no team, try presentation synthesizer team slide."""
        from app.services.contract_fidelity.team_candidate_validator import filter_team_members

        fidelity = contract.fidelity
        if not fidelity or fidelity.team_structured:
            return contract
        if len(extraction.files) != 1:
            return contract
        if extraction.files[0].file_type != "pptx":
            return contract

        parsed = self._presentation_synthesizer.synthesize(text, source_type)
        team = filter_team_members(parsed.team)
        if not team:
            return contract

        fidelity.team_structured = team
        team_bullets = team_to_bullets(team)
        updated = False
        for block in contract.blocks:
            if block.key == "team":
                block.bullets = team_bullets
                updated = True
                break
        if not updated:
            contract.blocks.append(
                LandingBlock(
                    key="team",
                    title="Команда проекта",
                    content="",
                    bullets=team_bullets,
                )
            )
        fidelity.completeness = self._completeness_gate.evaluate(contract)
        logger.info(
            "Supplemented PPTX-only team from presentation synthesizer (%d members)",
            len(team),
        )
        return contract



    def build_source_structure(self, extraction: ExtractionResult) -> SourceStructureReport:

        self._ensure_fidelity_deps()

        text = _primary_extracted_text(extraction)

        file_type = _primary_file_type(extraction)

        detection = self._detector.detect(text)

        source_type = self._source_type_detector.detect(text, file_type=file_type)

        parser_mode = "heuristic"

        sections: list[SectionInfo] = []



        if detection.is_structured_landing and detection.confidence >= CONFIDENCE_THRESHOLD:

            parsed = self._structured_parser.parse(text)

            parser_mode = "structured"

            for key, length in parsed.section_lengths.items():

                item_count = 0

                if key == "tasks":

                    item_count = len(parsed.tasks)

                elif key == "team":

                    item_count = len(parsed.team)

                elif key == "tech_stack":

                    item_count = sum(len(v) for v in parsed.tech_stack_grouped.values())

                sections.append(

                    SectionInfo(key=key, title=key, length=length, item_count=item_count)

                )

        elif (
            source_type.source_type == "project_presentation"
            and source_type.confidence >= PRESENTATION_CONFIDENCE_THRESHOLD
        ):

            parsed = self._presentation_synthesizer.synthesize(text, source_type)

            parser_mode = "project_presentation"

            for key, length in parsed.section_lengths.items():

                item_count = 0

                if key == "tasks":

                    item_count = len(parsed.tasks)

                elif key == "team":

                    item_count = len(parsed.team)

                elif key == "tech_stack":

                    item_count = sum(len(v) for v in parsed.tech_stack_grouped.values())

                elif key == "essence":

                    item_count = 1 if parsed.essence else 0

                sections.append(

                    SectionInfo(key=key, title=key, length=length, item_count=item_count)

                )



        return SourceStructureReport(

            parser_mode=parser_mode,

            detection=detection,

            sections=sections,

            parser_confidence=detection.confidence,

            missing_sections=detection.missing_sections,

        )



    async def reparse_structured(self, project_id: UUID) -> LandingContract | None:

        extraction = await self._repo.get_extraction(project_id)

        if not extraction:

            return None

        contract = self.build(extraction)

        existing = await self._repo.get_contract(project_id)

        if existing:

            contract.version = existing.version + 1

        await self._repo.save_contract(contract)

        return contract



    def _build_from_structured(

        self,

        extraction: ExtractionResult,

        text: str,

        detection: DetectionResult,

    ) -> LandingContract:

        parsed = self._structured_parser.parse(text)

        stack_bullets = stack_to_bullets(parsed.tech_stack_grouped)

        team_bullets = team_to_bullets(parsed.team)



        purpose_content = ""

        purpose_bullets = parsed.purpose

        outlook_content = ""

        outlook_bullets = parsed.outlook



        blocks = [

            LandingBlock(

                key="essence",

                title="Суть проекта",

                content=parsed.essence,

                bullets=[],

            ),

            LandingBlock(

                key="tasks",

                title="Задачи проекта",

                content="",

                bullets=parsed.tasks,

            ),

            LandingBlock(

                key="purpose",

                title="Для чего",

                content=purpose_content,

                bullets=purpose_bullets,

            ),

            LandingBlock(

                key="inputs",

                title="Вводные данные",

                content="",

                bullets=parsed.inputs,

            ),

            LandingBlock(

                key="outputs",

                title="Выходные данные",

                content="",

                bullets=parsed.outputs,

            ),

            LandingBlock(

                key="results",

                title="Результаты проекта",

                content="",

                bullets=parsed.results,

            ),

            LandingBlock(

                key="outlook",

                title="Перспектива развития",

                content=outlook_content,

                bullets=outlook_bullets,

            ),

            LandingBlock(

                key="tech_stack",

                title="Используемый технологический стек",

                content="",

                bullets=stack_bullets,

            ),

            LandingBlock(

                key="team",

                title="Команда проекта",

                content="",

                bullets=team_bullets,

            ),

            LandingBlock(

                key="tagline",

                title="Фраза проекта",

                content=parsed.tagline or parsed.title or "",

                bullets=[],

            ),

        ]



        fidelity = FidelityMetadata(

            parser_mode="structured",

            detection=detection,

            modules=parsed.modules,

            team_structured=parsed.team,

            tech_stack_grouped=parsed.tech_stack_grouped,

        )



        return LandingContract(

            project_id=extraction.project_id,

            status=ContractStatus.DRAFT,

            title=parsed.title,

            client=parsed.client,

            timeline=parsed.timeline,

            lead=parsed.lead,

            quote=parsed.tagline,

            goals=[m.name for m in parsed.modules] or extraction.payload.goals,

            presentation_style=extraction.payload.presentation_style,

            style_config=default_style_config(),

            visual_assets=extraction.payload.visual_assets,

            blocks=blocks,

            fidelity=fidelity,

            updated_at=utc_now(),

        )



    def _build_from_presentation(

        self,

        extraction: ExtractionResult,

        text: str,

        detection: DetectionResult,

        source_type,

    ) -> LandingContract:

        parsed = self._presentation_synthesizer.synthesize(text, source_type)

        stack_bullets = stack_to_bullets(parsed.tech_stack_grouped)

        team_bullets = team_to_bullets(parsed.team)



        blocks = [

            LandingBlock(

                key="essence",

                title="Суть проекта",

                content=parsed.essence,

                bullets=[],

            ),

            LandingBlock(

                key="tasks",

                title="Задачи проекта",

                content="",

                bullets=parsed.tasks,

            ),

            LandingBlock(

                key="purpose",

                title="Для чего",

                content="",

                bullets=parsed.purpose,

            ),

            LandingBlock(

                key="inputs",

                title="Вводные данные",

                content="",

                bullets=parsed.inputs,

            ),

            LandingBlock(

                key="outputs",

                title="Выходные данные",

                content="",

                bullets=parsed.outputs,

            ),

            LandingBlock(

                key="results",

                title="Результаты проекта",

                content="",

                bullets=parsed.results,

            ),

            LandingBlock(

                key="outlook",

                title="Перспектива развития",

                content="",

                bullets=parsed.outlook,

            ),

            LandingBlock(

                key="tech_stack",

                title="Используемый технологический стек",

                content="",

                bullets=stack_bullets,

            ),

            LandingBlock(

                key="team",

                title="Команда проекта",

                content="",

                bullets=team_bullets,

            ),

            LandingBlock(

                key="tagline",

                title="Фраза проекта",

                content=parsed.tagline or parsed.title or "",

                bullets=[],

            ),

        ]



        fidelity = FidelityMetadata(

            parser_mode="project_presentation",

            detection=detection,

            modules=parsed.modules,

            team_structured=parsed.team,

            tech_stack_grouped=parsed.tech_stack_grouped,

        )



        return LandingContract(

            project_id=extraction.project_id,

            status=ContractStatus.DRAFT,

            title=parsed.title,

            client=parsed.client,

            timeline=parsed.timeline,

            lead=parsed.lead,

            quote=parsed.tagline,

            goals=[m.name for m in parsed.modules] or extraction.payload.goals,

            presentation_style=extraction.payload.presentation_style,

            style_config=default_style_config(),

            visual_assets=extraction.payload.visual_assets,

            blocks=blocks,

            fidelity=fidelity,

            updated_at=utc_now(),

        )



    def _build_heuristic(self, extraction: ExtractionResult) -> LandingContract:

        p = extraction.payload

        blocks: list[LandingBlock] = []



        for key, title, attr in BLOCK_SPECS:

            value = getattr(p, attr, None)

            if isinstance(value, list):

                bullets = value

                content = "\n".join(f"• {item}" for item in bullets) if bullets else ""

            else:

                bullets = []

                content = value or ""

            blocks.append(

                LandingBlock(key=key, title=title, content=content, bullets=bullets)

            )



        return LandingContract(

            project_id=extraction.project_id,

            status=ContractStatus.DRAFT,

            client=p.client,

            goals=p.goals,

            presentation_style=p.presentation_style,

            style_config=default_style_config(),

            visual_assets=p.visual_assets,

            blocks=blocks,

            updated_at=utc_now(),

        )



    async def build_and_save(self, extraction: ExtractionResult) -> LandingContract:

        contract = self.build(extraction)

        await self._repo.save_contract(contract)

        logger.info("LandingContract built for %s", extraction.project_id)

        return contract



    async def update_contract(

        self, project_id: UUID, blocks: list[LandingBlock] | None, **fields

    ) -> LandingContract | None:

        contract = await self._repo.get_contract(project_id)

        if not contract:

            return None

        if blocks is not None:

            contract.blocks = blocks

        for key, value in fields.items():

            if value is not None and hasattr(contract, key):

                setattr(contract, key, value)

        contract.updated_at = utc_now()

        contract.version += 1

        if contract.fidelity:

            contract.fidelity.completeness = self._completeness_gate.evaluate(contract)

        await self._repo.save_contract(contract)

        return contract





def _primary_extracted_text(extraction: ExtractionResult) -> str:

    """Prefer longest doc-like file text over auxiliary uploads."""

    candidates: list[tuple[int, str]] = []

    for f in extraction.files:

        text = (f.extracted_text or "").strip()

        if not text:

            continue

        score = len(text)

        if f.file_type in ("docx", "pdf", "pptx"):

            score += 1_000_000

        candidates.append((score, text))

    if candidates:

        candidates.sort(reverse=True)

        return candidates[0][1]

    if extraction.payload.raw_notes:

        return extraction.payload.raw_notes[0]

    return ""



def _primary_file_type(extraction: ExtractionResult) -> str | None:

    """Return file_type of the primary extracted document."""

    best: tuple[int, str | None] = (0, None)

    for f in extraction.files:

        text = (f.extracted_text or "").strip()

        if not text:

            continue

        score = len(text)

        if f.file_type in ("docx", "pdf", "pptx"):

            score += 1_000_000

        if score > best[0]:

            best = (score, f.file_type)

    return best[1]


