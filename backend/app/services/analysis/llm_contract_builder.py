import logging
import re
from uuid import UUID

from app.config import Settings
from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
from app.schemas.enrichment import EnrichmentMetadata
from app.schemas.extraction import ExtractionResult
from app.schemas.landing import LLMContractOutput
from app.schemas.landing_contract import ContractStatus, LandingBlock, LandingContract
from app.schemas.responses import EnrichmentResponse
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.analysis.normalization import normalize_llm_output, parse_llm_json, repair_json_text
from app.services.analysis.source_trace import merge_trace_with_files
from app.services.llm.base import LLMClient
from app.services.llm.errors import LLMError, LLMUnavailableError
from app.services.llm.mock_client import MockLLMClient
from app.services.llm.openai_client import OpenAIClient
from app.services.pipeline.pii_stage import PIIStageService
from app.services.pii.audit import log_pii_audit
from app.services.pii.rehydrator import PIIRehydrator
from app.services.prompts.engine import PromptEngine
from app.schemas.pii import PrivacyMode

logger = logging.getLogger(__name__)

KEYWORDS = (
    "проект",
    "цель",
    "задач",
    "результат",
    "команда",
    "стек",
    "архитектур",
    "клиент",
    "вводн",
    "выходн",
    "перспектив",
)


class LLMContractBuilderService:
    def __init__(
        self,
        settings: Settings,
        repository: ContractRepository,
        heuristic_builder: ContractBuilderService,
        prompt_engine: PromptEngine | None = None,
        pii_stage: PIIStageService | None = None,
    ) -> None:
        self._settings = settings
        self._repo = repository
        self._heuristic = heuristic_builder
        self._prompts = prompt_engine or PromptEngine()
        self._pii = pii_stage or PIIStageService(settings)

    def _resolve_client(self, extraction: ExtractionResult) -> LLMClient:
        if not self._settings.llm_enabled:
            raise LLMUnavailableError("LLM_ENABLED is false")
        provider = (self._settings.llm_provider or "mock").lower()
        if provider == "openai":
            return OpenAIClient(self._settings)
        mock = MockLLMClient(extraction)
        return mock

    def compact_extraction_text(self, extraction: ExtractionResult) -> str:
        per_file = self._settings.llm_max_chars_per_file
        total_max = self._settings.llm_max_total_chars
        sections: list[str] = []
        used = 0

        for f in extraction.files:
            text = f.extracted_text or ""
            if not text.strip():
                header = f"### {f.filename} ({f.file_type})\n[no text]\n"
                sections.append(header)
                continue
            compact = _compact_text(text, per_file)
            block = f"### {f.filename} ({f.file_type})\n{compact}\n"
            if f.warnings:
                block += f"warnings: {', '.join(f.warnings)}\n"
            if used + len(block) > total_max:
                remain = max(0, total_max - used)
                block = block[:remain] + "\n[truncated]\n"
            sections.append(block)
            used += len(block)
            if used >= total_max:
                break

        return "\n".join(sections)

    async def enrich(self, project_id: UUID) -> EnrichmentResponse:
        extraction = await self._repo.get_extraction(project_id)
        if not extraction:
            raise ValueError("ExtractionResult not found. Upload materials first.")

        heuristic = await self._repo.get_contract(project_id)
        if not heuristic:
            heuristic = await self._heuristic.build_and_save(extraction)

        cached_report = await self._repo.get_pii_report(project_id)
        _redacted, pii_report, llm_extraction = await self._pii.process(
            extraction, cached_report=cached_report
        )
        if not cached_report or cached_report.extraction_fingerprint != pii_report.extraction_fingerprint:
            await self._repo.save_pii_report(pii_report)

        privacy_meta = self._privacy_meta(pii_report)

        provider = (self._settings.llm_provider or "mock").lower()
        if self._pii.privacy_mode == PrivacyMode.LOCAL_ONLY and provider == "openai":
            return await self._fallback_response(
                extraction,
                heuristic,
                message="LOCAL_ONLY: cloud LLM blocked. Heuristic contract kept.",
                privacy_meta=privacy_meta,
            )

        if not self._settings.llm_enabled:
            return await self._fallback_response(
                extraction,
                heuristic,
                message="LLM disabled (LLM_ENABLED=false). Heuristic contract kept.",
                privacy_meta=privacy_meta,
            )

        is_cloud = provider == "openai"
        cloud_unsafe = self._pii.is_cloud_unsafe_dev()

        try:
            client = self._resolve_client(llm_extraction)
            if isinstance(client, MockLLMClient):
                client.set_extraction(llm_extraction)

            system = self._prompts.load_template("landing_contract_system.txt")
            user = self._build_user_prompt(llm_extraction, heuristic)
            payload_chars = len(user)

            if is_cloud:
                log_pii_audit(
                    event="cloud_llm_request",
                    project_id=project_id,
                    privacy_mode=self._pii.privacy_mode.value,
                    has_pii=pii_report.has_pii,
                    redaction_count=pii_report.redaction_count,
                    entity_types=[e.type.value for e in pii_report.entities],
                    cloud_sent=True,
                    cloud_provider=provider,
                    payload_chars=payload_chars,
                )

            raw = await client.generate_json(
                system,
                user,
                schema_name="landing_contract",
            )
            try:
                llm_out = normalize_llm_output(raw)
            except Exception:
                repaired = parse_llm_json(repair_json_text(str(raw)))
                llm_out = normalize_llm_output(repaired)

            if self._settings.enable_rehydration and _redacted.mapping:
                llm_out = PIIRehydrator(_redacted.mapping).rehydrate_llm_output(llm_out)

            contract, meta = self._to_contract(
                project_id,
                llm_out,
                extraction,
                provider=self._settings.llm_provider,
                fallback=False,
            )
            contract = self._preserve_structured_fields(heuristic, contract)
            meta = self._merge_privacy_meta(meta, privacy_meta, cloud_unsafe=cloud_unsafe)
            if self._settings.enable_rehydration and _redacted.mapping:
                contract = PIIRehydrator(_redacted.mapping).rehydrate_contract(contract)

            contract.version = (heuristic.version or 1) + 1
            await self._repo.save_contract(contract)
            msg = "Contract enriched via LLM."
            if cloud_unsafe:
                msg += " WARNING: CLOUD_UNSAFE_DEV — raw PII may have been sent."
            return EnrichmentResponse(
                contract=contract,
                enrichment=meta,
                message=msg,
            )
        except (LLMError, LLMUnavailableError, ValueError, Exception) as exc:
            logger.warning("LLM enrich failed, fallback: %s", exc)
            log_pii_audit(
                event="llm_enrich_fallback",
                project_id=project_id,
                privacy_mode=self._pii.privacy_mode.value,
                has_pii=pii_report.has_pii,
                redaction_count=pii_report.redaction_count,
                fallback=True,
            )
            return await self._fallback_response(
                extraction,
                heuristic,
                message=f"LLM enrich failed ({exc}). Heuristic fallback applied.",
                privacy_meta=privacy_meta,
            )

    def _privacy_meta(self, pii_report) -> dict:
        mode = self._pii.privacy_mode
        cloud_safe = (
            mode == PrivacyMode.HYBRID_SAFE
            and self._settings.enable_pii_detection
            and not self._pii.is_cloud_unsafe_dev()
        )
        return {
            "privacy_mode": mode.value,
            "pii_detected": pii_report.has_pii,
            "pii_redaction_count": pii_report.redaction_count,
            "cloud_payload_safe": cloud_safe,
            "cloud_unsafe_warning": self._pii.is_cloud_unsafe_dev(),
        }

    @staticmethod
    def _merge_privacy_meta(meta: EnrichmentMetadata, extra: dict, cloud_unsafe: bool) -> EnrichmentMetadata:
        data = meta.model_dump()
        data.update(extra)
        data["cloud_unsafe_warning"] = cloud_unsafe
        return EnrichmentMetadata.model_validate(data)

    async def _fallback_response(
        self,
        extraction: ExtractionResult,
        heuristic: LandingContract | None,
        message: str,
        privacy_meta: dict | None = None,
    ) -> EnrichmentResponse:
        contract = self._heuristic.build(extraction)
        contract.status = ContractStatus.DRAFT_FALLBACK
        if heuristic:
            contract.version = heuristic.version + 1
            contract.style = heuristic.style
            contract.visual_assets = heuristic.visual_assets
        base_meta = {
            "provider": "heuristic",
            "llm_enabled": self._settings.llm_enabled,
            "fallback_used": True,
            "enriched_at": utc_now(),
            "missing_fields": ["llm_unavailable_or_failed"],
            "assumptions": ["Used heuristic contract builder"],
        }
        if privacy_meta:
            base_meta.update(privacy_meta)
        contract.enrichment = EnrichmentMetadata.model_validate(base_meta)
        await self._repo.save_contract(contract)
        return EnrichmentResponse(contract=contract, enrichment=contract.enrichment, message=message)

    def _build_user_prompt(
        self,
        extraction: ExtractionResult,
        heuristic: LandingContract | None,
    ) -> str:
        warnings: list[str] = []
        for f in extraction.files:
            warnings.extend(f.warnings)
            warnings.extend(f.errors)

        draft = ""
        preserve_note = ""
        if heuristic:
            draft = "\n".join(
                f"- {b.title}: {b.content[:300]}" for b in heuristic.blocks if b.content
            )
            if not draft:
                draft = "\n".join(
                    f"- {b.title}: {len(b.bullets)} items"
                    for b in heuristic.blocks
                    if b.bullets
                )
            if heuristic.fidelity and heuristic.fidelity.parser_mode in (
                "structured",
                "project_presentation",
            ):
                preserve_note = (
                    "\n\nВАЖНО: Исходный контракт получен из structured landing parser. "
                    "Режим preserve and polish — сохрани все поля, не удаляй команду, "
                    "стек, результаты и списки. Не сжимай списки."
                )

        template = self._prompts.load_template("landing_contract_user.txt")
        return template.format(
            project_id=str(extraction.project_id),
            files_section=self.compact_extraction_text(extraction),
            warnings_section="\n".join(warnings) or "none",
            heuristic_draft=(draft or "empty") + preserve_note,
        )

    def _to_contract(
        self,
        project_id: UUID,
        output: LLMContractOutput,
        extraction: ExtractionResult,
        provider: str,
        fallback: bool,
    ) -> tuple[LandingContract, EnrichmentMetadata]:
        from app.services.analysis.normalization import collect_missing_fields

        missing = collect_missing_fields(output)
        filenames = [f.filename for f in extraction.files]
        trace = merge_trace_with_files(output, filenames)

        team_lines = _normalize_team_list(output.team)
        stack_lines = _normalize_stack_list(output.stack)

        blocks = [
            LandingBlock(key="essence", title="Суть проекта", content=output.essence or "", bullets=[]),
            LandingBlock(
                key="tasks",
                title="Задачи проекта",
                content="",
                bullets=output.tasks,
            ),
            LandingBlock(key="purpose", title="Для чего", content=output.purpose or "", bullets=[]),
            LandingBlock(key="inputs", title="Вводные данные", content="", bullets=output.inputs),
            LandingBlock(key="outputs", title="Выходные данные", content="", bullets=output.outputs),
            LandingBlock(key="results", title="Результаты проекта", content="", bullets=output.results),
            LandingBlock(
                key="outlook",
                title="Перспектива развития",
                content=output.roadmap or "",
                bullets=[],
            ),
            LandingBlock(
                key="tech_stack",
                title="Используемый технологический стек",
                content="",
                bullets=stack_lines,
            ),
            LandingBlock(
                key="team",
                title="Команда проекта",
                content="",
                bullets=team_lines,
            ),
            LandingBlock(
                key="tagline",
                title="Фраза проекта",
                content=output.quote or "",
                bullets=[],
            ),
        ]

        meta = EnrichmentMetadata(
            confidence=output.confidence,
            missing_fields=missing,
            assumptions=output.assumptions,
            source_trace=trace,
            provider=provider,
            llm_enabled=self._settings.llm_enabled,
            fallback_used=fallback,
            enriched_at=utc_now(),
        )

        contract = LandingContract(
            project_id=project_id,
            status=ContractStatus.ENRICHED if not fallback else ContractStatus.DRAFT_FALLBACK,
            title=output.title,
            client=output.client,
            timeline=output.timeline,
            lead=output.lead,
            quote=output.quote,
            goals=output.tasks[:3],
            visual_assets=extraction.payload.visual_assets,
            blocks=blocks,
            enrichment=meta,
            updated_at=utc_now(),
        )
        return contract, meta

    def _preserve_structured_fields(
        self,
        original: LandingContract | None,
        enriched: LandingContract,
    ) -> LandingContract:
        """Merge structured parser data back if LLM dropped fields."""
        if not original or not original.fidelity:
            return enriched
        if original.fidelity.parser_mode not in ("structured", "project_presentation"):
            return enriched

        fid = original.fidelity
        enriched.fidelity = fid.model_copy(deep=True)
        if original.fidelity.parser_mode == "structured":
            enriched.fidelity.parser_mode = "structured+llm"
        else:
            enriched.fidelity.parser_mode = "project_presentation+llm"

        if fid.modules and not enriched.goals:
            enriched.goals = [m.name for m in fid.modules]

        if fid.team_structured:
            team_block = next((b for b in enriched.blocks if b.key == "team"), None)
            orig_team = next((b for b in original.blocks if b.key == "team"), None)
            if team_block and orig_team and len(team_block.bullets) < len(orig_team.bullets):
                team_block.bullets = orig_team.bullets

        if fid.tech_stack_grouped:
            stack_block = next((b for b in enriched.blocks if b.key == "tech_stack"), None)
            orig_stack = next((b for b in original.blocks if b.key == "tech_stack"), None)
            if stack_block and orig_stack and len(stack_block.bullets) < len(orig_stack.bullets):
                stack_block.bullets = orig_stack.bullets

        list_keys = ("tasks", "purpose", "inputs", "outputs", "results", "outlook")
        for key in list_keys:
            orig = next((b for b in original.blocks if b.key == key), None)
            new = next((b for b in enriched.blocks if b.key == key), None)
            if orig and new:
                orig_count = len(orig.bullets) or (1 if orig.content.strip() else 0)
                new_count = len(new.bullets) or (1 if new.content.strip() else 0)
                if new_count < orig_count:
                    new.bullets = orig.bullets
                    new.content = orig.content

        essence_orig = next((b for b in original.blocks if b.key == "essence"), None)
        essence_new = next((b for b in enriched.blocks if b.key == "essence"), None)
        if essence_orig and essence_new and len(essence_new.content) < len(essence_orig.content) * 0.5:
            essence_new.content = essence_orig.content

        for field in ("title", "client", "timeline", "lead"):
            if getattr(original, field, None) and not getattr(enriched, field, None):
                setattr(enriched, field, getattr(original, field))

        return enriched


def _compact_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    lines = text.splitlines()
    priority: list[str] = []
    rest: list[str] = []
    for ln in lines:
        low = ln.lower()
        if any(k in low for k in KEYWORDS) or re.match(r"^[\s]*[-•*\d]", ln):
            priority.append(ln)
        else:
            rest.append(ln)
    combined = "\n".join(priority + rest)
    if len(combined) <= max_chars:
        return combined
    head = combined[: int(max_chars * 0.7)]
    tail = combined[-int(max_chars * 0.25) :]
    return f"{head}\n...\n{tail}"


def _normalize_team_list(team: list) -> list[str]:
    from app.services.analysis.normalization import _normalize_team

    return _normalize_team(team)


def _normalize_stack_list(stack: list) -> list[str]:
    from app.services.analysis.normalization import _normalize_stack

    flat, _ = _normalize_stack(stack)
    return flat

