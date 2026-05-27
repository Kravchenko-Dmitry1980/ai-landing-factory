"""Team review UX schemas — minimal human-in-the-loop for OCR team."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class TeamPublicationMode(StrEnum):
    draft_auto = "draft_auto"
    safe_public = "safe_public"
    user_accepted = "user_accepted"
    manual_edited = "manual_edited"


class TeamReviewSummary(BaseModel):
    total_candidates: int = 0
    verified_count: int = 0
    probable_count: int = 0
    needs_review_count: int = 0
    rejected_count: int = 0
    publication_mode: str = TeamPublicationMode.draft_auto
    can_publish_team: bool = False
    warning: str | None = None


class TeamReviewCandidate(BaseModel):
    id: str
    raw_name: str
    display_name: str
    role: str | None = None
    contributions: list[str] = Field(default_factory=list)
    status: str
    source: str = ""
    source_is_ocr: bool = False
    confidence: float | None = None
    warning: str | None = None


class ManualTeamUpdateRequest(BaseModel):
    text: str


class TeamBulkActionRequest(BaseModel):
    action: str  # accept_all | keep_verified_only | reset_to_auto


class TeamReviewResponse(BaseModel):
    project_id: UUID
    summary: TeamReviewSummary = Field(default_factory=TeamReviewSummary)
    candidates: list[TeamReviewCandidate] = Field(default_factory=list)
    editable_text: str = ""
    publication_mode: str = TeamPublicationMode.draft_auto


class TeamReviewActionResponse(BaseModel):
    project_id: UUID
    publication_mode: str
    summary: TeamReviewSummary
    team_count: int = 0
