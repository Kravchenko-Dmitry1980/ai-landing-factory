from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.landing_contract import LandingStylePreset


class LandingBlockContent(BaseModel):
    key: str
    title: str
    body: str
    bullets: list[str] = Field(default_factory=list)


class GeneratedLanding(BaseModel):
    """Rendered-ready copy produced from LandingContract via prompt engine."""

    project_id: UUID
    style: LandingStylePreset
    blocks: list[LandingBlockContent]
    generated_at: datetime
    prompt_version: str = "landing-v1-stub"
