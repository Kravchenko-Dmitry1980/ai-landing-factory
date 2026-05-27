"""Team verification schemas — OCR gate before public export."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class TeamVerificationStatus(StrEnum):
    verified = "verified"
    probable = "probable"
    needs_review = "needs_review"
    rejected = "rejected"


class TeamVerificationSource(StrEnum):
    docx = "docx"
    txt = "txt"
    pptx_text = "pptx_text"
    pptx_ocr = "pptx_ocr"
    pdf_text = "pdf_text"
    pdf_ocr = "pdf_ocr"
    manual = "manual"
    expected_contract = "expected_contract"
    known_names = "known_names"


class TeamCandidateQuality(BaseModel):
    raw_name: str
    normalized_name: str | None = None
    corrected_name: str | None = None
    role: str | None = None
    contributions: list[str] = Field(default_factory=list)
    source_filename: str = ""
    source_type: str = ""
    source_location: str | None = None
    source_is_ocr: bool = False
    ocr_engine: str | None = None
    ocr_confidence: float | None = None
    name_quality_score: float = 0.0
    role_quality_score: float = 0.0
    verification_status: TeamVerificationStatus = TeamVerificationStatus.needs_review
    verification_reason: str = ""
    matched_trusted_name: str | None = None
    match_score: float | None = None
    warnings: list[str] = Field(default_factory=list)


class TeamVerificationMetrics(BaseModel):
    ocr_candidates: int = 0
    verified_count: int = 0
    needs_review_count: int = 0
    rejected_count: int = 0
    probable_count: int = 0


class TeamVerificationReport(BaseModel):
    verified_members: list[TeamCandidateQuality] = Field(default_factory=list)
    review_candidates: list[TeamCandidateQuality] = Field(default_factory=list)
    rejected_candidates: list[TeamCandidateQuality] = Field(default_factory=list)
    probable_candidates: list[TeamCandidateQuality] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: TeamVerificationMetrics = Field(default_factory=TeamVerificationMetrics)
    team_publication_policy: str = "verified_only"
