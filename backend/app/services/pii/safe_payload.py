"""Build safe cloud payload preview — what LLM would receive."""

from __future__ import annotations

from uuid import UUID

from app.config import Settings
from app.schemas.extraction import ExtractionResult
from app.schemas.pii import (
    PIIReportFull,
    PiiSummary,
    PrivacyMode,
    SafeCloudPayloadPreview,
)
from app.services.analysis.llm_contract_builder import LLMContractBuilderService
from app.services.pipeline.pii_stage import PIIStageService
from app.services.pii.report import to_pii_summary


class SafeCloudPayloadService:
    def __init__(self, settings: Settings, pii_stage: PIIStageService) -> None:
        self._settings = settings
        self._pii = pii_stage

    async def build_preview(
        self,
        project_id: UUID,
        extraction: ExtractionResult,
        report: PIIReportFull | None,
        llm_builder: LLMContractBuilderService | None = None,
    ) -> SafeCloudPayloadPreview:
        mode = self._pii.privacy_mode
        warnings: list[str] = list(report.warnings if report else [])

        if mode == PrivacyMode.LOCAL_ONLY:
            return SafeCloudPayloadPreview(
                project_id=project_id,
                privacy_mode=mode,
                safe_for_cloud=False,
                unsafe=False,
                blocked_reason="local_only",
                pii_summary=to_pii_summary(report, mode) if report else None,
                warnings=warnings,
            )

        if not self._settings.enable_pii_detection:
            warnings.append("pii_detection_disabled")
            raw_text = _compact_raw(extraction, llm_builder)
            return SafeCloudPayloadPreview(
                project_id=project_id,
                privacy_mode=mode,
                safe_for_cloud=False,
                unsafe=mode == PrivacyMode.CLOUD_UNSAFE_DEV,
                chars_count=len(raw_text),
                files=[f.filename for f in extraction.files],
                preview_text_redacted=raw_text[:4000],
                pii_summary=to_pii_summary(report, mode) if report else None,
                warnings=warnings,
            )

        _redacted, _fresh_report, llm_view = await self._pii.process(extraction)
        active_report = report or _fresh_report
        preview_text = _compact_raw(llm_view, llm_builder)
        summary = to_pii_summary(active_report, mode)

        if mode == PrivacyMode.CLOUD_UNSAFE_DEV:
            warnings.append("cloud_unsafe_dev_active")
            return SafeCloudPayloadPreview(
                project_id=project_id,
                privacy_mode=mode,
                safe_for_cloud=False,
                unsafe=True,
                chars_count=len(preview_text),
                files=[f.filename for f in llm_view.files],
                preview_text_redacted=preview_text[:4000],
                pii_summary=summary,
                warnings=warnings,
            )

        safe = active_report.safe_for_cloud and summary.safe_for_cloud_current_mode
        return SafeCloudPayloadPreview(
            project_id=project_id,
            privacy_mode=mode,
            safe_for_cloud=safe,
            unsafe=False,
            chars_count=len(preview_text),
            files=[f.filename for f in llm_view.files],
            preview_text_redacted=preview_text[:4000],
            pii_summary=summary,
            warnings=warnings,
        )


def _compact_raw(
    extraction: ExtractionResult,
    llm_builder: LLMContractBuilderService | None,
) -> str:
    if llm_builder:
        return llm_builder.compact_extraction_text(extraction)
    parts = []
    for f in extraction.files:
        parts.append(f"### {f.filename}\n{f.extracted_text or ''}")
    return "\n\n".join(parts)
