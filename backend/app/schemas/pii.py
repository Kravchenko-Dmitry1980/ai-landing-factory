from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class PIIEntityType(str, Enum):
    PERSON_NAME = "person_name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    URL = "url"
    ORGANIZATION = "organization"
    MEDICAL_DATA = "medical_data"
    PASSPORT_ID = "passport_id"
    TELEGRAM = "telegram"
    ROLE_PERSON = "role_person"


class PrivacyMode(str, Enum):
    LOCAL_ONLY = "local_only"
    HYBRID_SAFE = "hybrid_safe"
    CLOUD_UNSAFE_DEV = "cloud_unsafe_dev"


class PIIRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class PIIEntity(BaseModel):
    type: PIIEntityType
    original: str
    placeholder: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_file: str | None = None
    start_offset: int = Field(ge=0, validation_alias="start")
    end_offset: int = Field(ge=0, validation_alias="end")
    detector: str = "regex"
    context_preview_redacted: str | None = None
    original_hash: str | None = None
    original_encrypted: str | None = Field(default=None, exclude=True)

    model_config = {"populate_by_name": True}

    @property
    def start(self) -> int:
        return self.start_offset

    @property
    def end(self) -> int:
        return self.end_offset


class StoragePolicy(BaseModel):
    ttl_hours: int = 72
    encrypt_reports: bool = False
    raw_pii_logging: bool = False
    cleanup_enabled: bool = True
    storage_paths: list[str] = Field(default_factory=list)


class PIIReportFull(BaseModel):
    """Full report with originals — server-side only, never exposed via public API."""

    project_id: UUID
    has_pii: bool = False
    entities: list[PIIEntity] = Field(default_factory=list)
    redaction_count: int = 0
    risk_level: PIIRiskLevel = PIIRiskLevel.LOW
    privacy_mode: PrivacyMode = PrivacyMode.HYBRID_SAFE
    detectors_used: list[str] = Field(default_factory=list)
    created_at: datetime | None = Field(default=None, validation_alias="detected_at")
    expires_at: datetime | None = None
    source_files: list[str] = Field(default_factory=list)
    storage_policy: StoragePolicy | None = None
    safe_for_cloud: bool = False
    warnings: list[str] = Field(default_factory=list)
    extraction_fingerprint: str | None = None

    model_config = {"populate_by_name": True}

    @property
    def detected_at(self) -> datetime | None:
        return self.created_at


PIIReport = PIIReportFull


class RedactedExtractionResult(BaseModel):
    """Cloud-safe view of extraction; originals stay server-side only."""

    project_id: UUID
    raw_removed: bool = True
    safe_text: str = ""
    mapping: dict[str, str] = Field(default_factory=dict)
    files: list = Field(default_factory=list)
    payload_snapshot: dict = Field(default_factory=dict)


class PrivacyStatusResponse(BaseModel):
    privacy_mode: PrivacyMode
    enable_pii_detection: bool
    enable_rehydration: bool
    llm_enabled: bool
    cloud_allowed: bool
    cloud_unsafe_warning: bool = False
    storage_policy: StoragePolicy | None = None


class PIIEntityPublic(BaseModel):
    """Safe for API/logs — no original values."""

    type: PIIEntityType
    placeholder: str
    confidence: float
    source_file: str | None = None
    detector: str = "regex"
    context_preview_redacted: str | None = None


class PIIReportPublic(BaseModel):
    project_id: UUID
    has_pii: bool
    entities: list[PIIEntityPublic] = Field(default_factory=list)
    redaction_count: int
    risk_level: PIIRiskLevel
    privacy_mode: PrivacyMode
    detectors_used: list[str] = Field(default_factory=list)
    created_at: datetime | None = Field(default=None, validation_alias="detected_at")
    expires_at: datetime | None = None
    source_files: list[str] = Field(default_factory=list)
    safe_for_cloud: bool = False
    warnings: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class PiiSummary(BaseModel):
    """Compact PII summary for upload response."""

    has_pii: bool = False
    risk_level: PIIRiskLevel = PIIRiskLevel.LOW
    redaction_count: int = 0
    safe_for_cloud_current_mode: bool = False
    detectors_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SafeCloudPayloadPreview(BaseModel):
    project_id: UUID
    privacy_mode: PrivacyMode
    safe_for_cloud: bool
    unsafe: bool = False
    chars_count: int = 0
    files: list[str] = Field(default_factory=list)
    preview_text_redacted: str = ""
    blocked_reason: str | None = None
    pii_summary: PiiSummary | None = None
    warnings: list[str] = Field(default_factory=list)


class PiiCleanupResponse(BaseModel):
    deleted_reports: int = 0
    deleted_artifacts: int = 0
    message: str = "Cleanup complete"
