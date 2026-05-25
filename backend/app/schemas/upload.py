from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.pii import PiiSummary


class FileKind(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    IMAGE = "image"
    SCREENSHOT = "screenshot"
    TEXT = "text"
    OTHER = "other"


class UploadedFileMeta(BaseModel):
    id: UUID
    project_id: UUID
    original_name: str
    stored_name: str
    kind: FileKind
    mime_type: str | None
    size_bytes: int
    uploaded_at: datetime


class UploadResponse(BaseModel):
    project_id: UUID
    files: list[UploadedFileMeta]
    message: str = Field(default="Files stored. Run pipeline or use auto-build on upload.")
    pii_summary: PiiSummary | None = None
