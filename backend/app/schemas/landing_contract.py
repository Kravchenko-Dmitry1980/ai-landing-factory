from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.enrichment import EnrichmentMetadata
from app.schemas.fidelity import FidelityMetadata
from app.schemas.style_config import LandingStyleConfigModel


class ContractStatus(str, Enum):
    DRAFT = "draft"
    DRAFT_FALLBACK = "draft_fallback"
    REVIEW = "review"
    READY = "ready"
    ENRICHED = "enriched"


class LandingStylePreset(str, Enum):
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    TECH = "tech"
    BOLD = "bold"


class LandingBlock(BaseModel):
    """Single canonical section of the landing."""

    key: str
    title: str
    content: str
    bullets: list[str] = Field(default_factory=list)


class LandingContract(BaseModel):
    """
    Unified content contract — single source of truth before generation/render.
    Content-first: built from ExtractionPayload, not from raw files.
    """

    project_id: UUID
    status: ContractStatus = ContractStatus.DRAFT
    style: LandingStylePreset = LandingStylePreset.MINIMAL

    title: str | None = None
    client: str | None = None
    timeline: str | None = None
    lead: str | None = None
    quote: str | None = None
    goals: list[str] = Field(default_factory=list)
    presentation_style: str | None = None
    style_config: LandingStyleConfigModel | None = None
    visual_assets: list[str] = Field(default_factory=list)

    blocks: list[LandingBlock] = Field(default_factory=list)
    enrichment: EnrichmentMetadata | None = None
    fidelity: FidelityMetadata | None = None

    updated_at: datetime
    version: int = 1


class LandingContractUpdate(BaseModel):
    style: LandingStylePreset | None = None
    blocks: list[LandingBlock] | None = None
    client: str | None = None
    goals: list[str] | None = None
    presentation_style: str | None = None
    style_config: LandingStyleConfigModel | None = None
