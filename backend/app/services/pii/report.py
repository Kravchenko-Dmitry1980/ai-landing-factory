import hashlib
from datetime import timedelta
from uuid import UUID

from app.config import Settings
from app.models.domain import utc_now
from app.schemas.extraction import ExtractionResult
from app.schemas.pii import (
    PIIEntity,
    PIIEntityPublic,
    PIIEntityType,
    PIIReportFull,
    PIIReportPublic,
    PIIRiskLevel,
    PiiSummary,
    PrivacyMode,
    StoragePolicy,
)
from app.services.pii.audit import log_pii_audit


def hash_original(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def extraction_fingerprint(extraction: ExtractionResult) -> str:
    parts = [str(extraction.project_id)]
    for f in extraction.files:
        parts.append(f.filename)
        parts.append(f.extracted_text or "")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:24]


def build_pii_report(
    project_id: UUID,
    entities: list[PIIEntity],
    privacy_mode: PrivacyMode,
    *,
    settings: Settings | None = None,
    storage_policy: StoragePolicy | None = None,
    source_files: list[str] | None = None,
    detectors_used: list[str] | None = None,
    warnings: list[str] | None = None,
    extraction_fp: str | None = None,
) -> PIIReportFull:
    risk = _assess_risk(entities)
    now = utc_now()
    ttl_hours = storage_policy.ttl_hours if storage_policy else 72
    expires = now + timedelta(hours=ttl_hours)

    safe_for_cloud = _compute_safe_for_cloud(
        privacy_mode, entities, settings.enable_pii_detection if settings else True
    )

    report = PIIReportFull(
        project_id=project_id,
        has_pii=bool(entities),
        entities=entities,
        redaction_count=len({e.placeholder for e in entities if e.placeholder}),
        risk_level=risk,
        privacy_mode=privacy_mode,
        detectors_used=sorted(set(detectors_used or _collect_detectors(entities))),
        created_at=now,
        expires_at=expires,
        source_files=source_files or sorted({e.source_file for e in entities if e.source_file}),
        storage_policy=storage_policy,
        safe_for_cloud=safe_for_cloud,
        warnings=warnings or [],
        extraction_fingerprint=extraction_fp,
    )
    log_pii_audit(
        event="pii_detection_complete",
        project_id=project_id,
        privacy_mode=privacy_mode.value,
        redaction_count=report.redaction_count,
        entity_types=sorted({e.type.value for e in entities}),
        has_pii=report.has_pii,
        risk_level=risk.value,
        detectors_used=",".join(report.detectors_used),
        safe_for_cloud=safe_for_cloud,
    )
    return report


def to_public_report(report: PIIReportFull) -> PIIReportPublic:
    return PIIReportPublic(
        project_id=report.project_id,
        has_pii=report.has_pii,
        entities=[
            PIIEntityPublic(
                type=e.type,
                placeholder=e.placeholder,
                confidence=e.confidence,
                source_file=e.source_file,
                detector=e.detector,
                context_preview_redacted=e.context_preview_redacted,
            )
            for e in report.entities
        ],
        redaction_count=report.redaction_count,
        risk_level=report.risk_level,
        privacy_mode=report.privacy_mode,
        detectors_used=report.detectors_used,
        created_at=report.created_at,
        expires_at=report.expires_at,
        source_files=report.source_files,
        safe_for_cloud=report.safe_for_cloud,
        warnings=report.warnings,
    )


def to_pii_summary(report: PIIReportFull | None, mode: PrivacyMode) -> PiiSummary:
    if not report:
        return PiiSummary(
            has_pii=False,
            risk_level=PIIRiskLevel.UNKNOWN,
            safe_for_cloud_current_mode=False,
        )
    safe = report.safe_for_cloud
    if mode == PrivacyMode.LOCAL_ONLY:
        safe = False
    elif mode == PrivacyMode.CLOUD_UNSAFE_DEV:
        safe = False
    return PiiSummary(
        has_pii=report.has_pii,
        risk_level=report.risk_level,
        redaction_count=report.redaction_count,
        safe_for_cloud_current_mode=safe,
        detectors_used=report.detectors_used,
        warnings=report.warnings,
    )


def is_report_fresh(report: PIIReportFull, extraction: ExtractionResult) -> bool:
    if report.extraction_fingerprint:
        return report.extraction_fingerprint == extraction_fingerprint(extraction)
    if report.created_at and extraction.extracted_at:
        return extraction.extracted_at <= report.created_at
    return False


def _collect_detectors(entities: list[PIIEntity]) -> list[str]:
    return sorted({e.detector for e in entities if e.detector})


def _compute_safe_for_cloud(
    mode: PrivacyMode,
    entities: list[PIIEntity],
    detection_enabled: bool,
) -> bool:
    if mode != PrivacyMode.HYBRID_SAFE:
        return False
    if not detection_enabled:
        return False
    return True


def _assess_risk(entities: list[PIIEntity]) -> PIIRiskLevel:
    if not entities:
        return PIIRiskLevel.LOW

    types = {e.type for e in entities}
    if PIIEntityType.MEDICAL_DATA in types or PIIEntityType.PASSPORT_ID in types:
        return PIIRiskLevel.CRITICAL
    if len(entities) >= 15:
        return PIIRiskLevel.HIGH
    if PIIEntityType.PERSON_NAME in types and (
        PIIEntityType.EMAIL in types or PIIEntityType.PHONE in types
    ):
        return PIIRiskLevel.HIGH
    if len(entities) >= 5:
        return PIIRiskLevel.MEDIUM
    return PIIRiskLevel.LOW
