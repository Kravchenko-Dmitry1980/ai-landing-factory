from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

class SourceTraceItem(BaseModel):
    field: str
    filename: str | None = None
    evidence: str = Field(..., max_length=500)


class ConfidenceScores(BaseModel):
    title: float = Field(default=0.0, ge=0.0, le=1.0)
    client: float = Field(default=0.0, ge=0.0, le=1.0)
    team: float = Field(default=0.0, ge=0.0, le=1.0)
    stack: float = Field(default=0.0, ge=0.0, le=1.0)
    results: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("title", "client", "team", "stack", "results", mode="before")
    @classmethod
    def clamp_confidence(cls, v: Any) -> float:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, f))


class EnrichmentMetadata(BaseModel):
    confidence: ConfidenceScores = Field(default_factory=ConfidenceScores)
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    source_trace: list[SourceTraceItem] = Field(default_factory=list)
    provider: str = "mock"
    llm_enabled: bool = False
    fallback_used: bool = False
    enriched_at: datetime | None = None
    privacy_mode: str | None = None
    pii_detected: bool = False
    pii_redaction_count: int = 0
    cloud_payload_safe: bool = True
    cloud_unsafe_warning: bool = False


