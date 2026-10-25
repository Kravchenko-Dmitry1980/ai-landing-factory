from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None = None


class ProjectSummary(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    version: int = 1
    # Library state of the landing; None when it was never published.
    publication_status: Literal["published", "withdrawn"] | None = None
    published_path: str | None = None
    published_contract_version: int | None = None
