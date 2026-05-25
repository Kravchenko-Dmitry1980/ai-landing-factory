from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class FileExtraction(BaseModel):
    """Per-file extraction artifact."""

    filename: str
    file_type: str
    extracted_text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ExtractionPayload(BaseModel):
    """Normalized facts extracted from raw materials (pre-contract)."""

    client: str | None = None
    goals: list[str] = Field(default_factory=list)
    essence: str | None = None
    tasks: list[str] = Field(default_factory=list)
    purpose: str | None = None
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    results: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    team: list[str] = Field(default_factory=list)
    outlook: str | None = None
    tagline: str | None = None
    presentation_style: str | None = None
    visual_assets: list[str] = Field(default_factory=list)
    raw_notes: list[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    project_id: UUID
    payload: ExtractionPayload
    files: list[FileExtraction] = Field(default_factory=list)
    source_file_ids: list[UUID] = Field(default_factory=list)
    extracted_at: datetime
    extractor_version: str = "dispatcher-0.2"
