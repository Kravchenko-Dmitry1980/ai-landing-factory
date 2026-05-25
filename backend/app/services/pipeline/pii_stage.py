import logging
from uuid import UUID



from app.config import Settings

from app.models.domain import utc_now

from app.schemas.extraction import ExtractionResult

from app.schemas.pii import (

    PIIReportFull,

    PIIRiskLevel,

    PiiSummary,

    PrivacyMode,

    RedactedExtractionResult,

)

from app.services.pii.audit import log_pii_audit

from app.services.pii.detector import PIIDetector

from app.services.pii.redactor import PIIRedactor

from app.services.pii.report import (

    build_pii_report,

    extraction_fingerprint,

    is_report_fresh,

    to_pii_summary,

)

from app.services.pii.storage import build_storage_policy



logger = logging.getLogger(__name__)





class PIIStageService:

    """

    Stage C.5/C.6: privacy layer — prescan after upload, redact before cloud LLM.

    Original extraction remains unchanged in storage.

    """



    def __init__(self, settings: Settings) -> None:

        self._settings = settings

        self._detector = PIIDetector(settings)

        self._redactor = PIIRedactor(self._detector)

        self._storage_policy = build_storage_policy(settings)



    @property

    def privacy_mode(self) -> PrivacyMode:

        raw = (self._settings.privacy_mode or "hybrid_safe").lower().replace("-", "_")

        try:

            return PrivacyMode(raw)

        except ValueError:

            logger.warning("Unknown PRIVACY_MODE=%s, defaulting to hybrid_safe", raw)

            return PrivacyMode.HYBRID_SAFE



    @property

    def storage_policy(self):

        return self._storage_policy



    def cloud_allowed(self) -> bool:

        return self.privacy_mode != PrivacyMode.LOCAL_ONLY



    def must_redact_before_cloud(self) -> bool:

        return (

            self.privacy_mode == PrivacyMode.HYBRID_SAFE

            and self._settings.enable_pii_detection

        )



    def is_cloud_unsafe_dev(self) -> bool:

        return self.privacy_mode == PrivacyMode.CLOUD_UNSAFE_DEV



    async def prescan(self, extraction: ExtractionResult) -> tuple[PIIReportFull, PiiSummary]:

        """

        Run PII detection after upload/extraction. Does not mutate stored extraction.

        """

        mode = self.privacy_mode

        fp = extraction_fingerprint(extraction)



        if not self._settings.enable_pii_detection:

            report = build_pii_report(

                extraction.project_id,

                [],

                mode,

                settings=self._settings,

                storage_policy=self._storage_policy,

                warnings=["pii_detection_disabled"],

                extraction_fp=fp,

            )

            summary = to_pii_summary(report, mode)

            log_pii_audit(

                event="pii_prescan_skipped",

                project_id=extraction.project_id,

                privacy_mode=mode.value,

                cloud_sent=False,

            )

            return report, summary



        try:

            redacted, entities, warnings = self._redactor.redact_extraction(extraction)
            warnings = sorted(set(warnings))

            detectors = sorted({e.detector for e in entities})

            report = build_pii_report(

                extraction.project_id,

                entities,

                mode,

                settings=self._settings,

                storage_policy=self._storage_policy,

                source_files=[f.filename for f in extraction.files],

                detectors_used=detectors,

                warnings=warnings,

                extraction_fp=fp,

            )

            summary = to_pii_summary(report, mode)

            log_pii_audit(

                event="pii_prescan_complete",

                project_id=extraction.project_id,

                privacy_mode=mode.value,

                has_pii=report.has_pii,

                redaction_count=report.redaction_count,

                entity_types=[e.type.value for e in entities],

                risk_level=report.risk_level.value,

                detectors_used=",".join(detectors),

                safe_for_cloud=report.safe_for_cloud,

            )

            return report, summary

        except Exception as exc:

            logger.warning("PII prescan failed for %s: %s", extraction.project_id, exc)

            report = build_pii_report(

                extraction.project_id,

                [],

                mode,

                settings=self._settings,

                storage_policy=self._storage_policy,

                warnings=["prescan_failed"],

                extraction_fp=fp,

            )

            report.risk_level = PIIRiskLevel.UNKNOWN

            report.safe_for_cloud = False

            summary = PiiSummary(

                has_pii=False,

                risk_level=PIIRiskLevel.UNKNOWN,

                safe_for_cloud_current_mode=False,

                warnings=["prescan_failed"],

            )

            return report, summary



    async def process(

        self,

        extraction: ExtractionResult,

        cached_report: PIIReportFull | None = None,

    ) -> tuple[RedactedExtractionResult, PIIReportFull, ExtractionResult]:

        """

        Returns redacted bundle, report, and extraction view for LLM (may be redacted or raw).

        Reuses cached report when fresh.

        """

        mode = self.privacy_mode



        if cached_report and is_report_fresh(cached_report, extraction):

            return self._process_from_report(extraction, cached_report)



        if not self._settings.enable_pii_detection:

            passthrough = RedactedExtractionResult(

                project_id=extraction.project_id,

                raw_removed=False,

                safe_text="",

                mapping={},

                files=[f.model_dump() for f in extraction.files],

                payload_snapshot=extraction.payload.model_dump(),

            )

            report = build_pii_report(

                extraction.project_id,

                [],

                mode,

                settings=self._settings,

                storage_policy=self._storage_policy,

                extraction_fp=extraction_fingerprint(extraction),

            )

            llm_view = extraction

            log_pii_audit(

                event="pii_detection_skipped",

                project_id=extraction.project_id,

                privacy_mode=mode.value,

                cloud_sent=False,

            )

            return passthrough, report, llm_view



        redacted, entities, warnings = self._redactor.redact_extraction(extraction)
        warnings = sorted(set(warnings))
        detectors = sorted({e.detector for e in entities})

        report = build_pii_report(

            extraction.project_id,

            entities,

            mode,

            settings=self._settings,

            storage_policy=self._storage_policy,

            source_files=[f.filename for f in extraction.files],

            detectors_used=detectors,

            warnings=warnings,

            extraction_fp=extraction_fingerprint(extraction),

        )



        if self.is_cloud_unsafe_dev():

            llm_view = extraction

            log_pii_audit(

                event="cloud_unsafe_dev_bypass",

                project_id=extraction.project_id,

                privacy_mode=mode.value,

                has_pii=report.has_pii,

                redaction_count=report.redaction_count,

                entity_types=[e.type.value for e in entities],

                cloud_sent=True,

                risk_level=report.risk_level.value,

            )

        else:

            llm_view = self._redactor.to_extraction_result(redacted, extraction)

            log_pii_audit(

                event="redaction_applied",

                project_id=extraction.project_id,

                privacy_mode=mode.value,

                has_pii=report.has_pii,

                redaction_count=report.redaction_count,

                entity_types=[e.type.value for e in entities],

                risk_level=report.risk_level.value,

                safe_for_cloud=report.safe_for_cloud,

            )



        return redacted, report, llm_view



    def _process_from_report(

        self,

        extraction: ExtractionResult,

        report: PIIReportFull,

    ) -> tuple[RedactedExtractionResult, PIIReportFull, ExtractionResult]:

        mode = self.privacy_mode

        redacted, entities, _ = self._redactor.redact_extraction(extraction)



        if self.is_cloud_unsafe_dev():

            llm_view = extraction

        else:

            llm_view = self._redactor.to_extraction_result(redacted, extraction)



        log_pii_audit(

            event="pii_report_reused",

            project_id=extraction.project_id,

            privacy_mode=mode.value,

            has_pii=report.has_pii,

            redaction_count=report.redaction_count,

            risk_level=report.risk_level.value,

            safe_for_cloud=report.safe_for_cloud,

        )

        return redacted, report, llm_view



    def build_safe_payload_log_meta(self, llm_view: ExtractionResult) -> int:

        return sum(len(f.extracted_text or "") for f in llm_view.files)



    def is_report_expired(self, report: PIIReportFull) -> bool:

        if not report.expires_at:

            return False

        return report.expires_at <= utc_now()


