"""LLM structured output schema (pre-normalization to LandingContract)."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.enrichment import ConfidenceScores, SourceTraceItem


class TeamMember(BaseModel):
    role: str = ""
    name: str = ""
    contribution: str = ""


class StackCategory(BaseModel):
    category: str = "general"
    items: list[str] = Field(default_factory=list)


class LLMContractOutput(BaseModel):
    title: str | None = None
    client: str | None = None
    timeline: str | None = None
    lead: str | None = None
    essence: str | None = None
    tasks: list[str] = Field(default_factory=list)
    purpose: str | None = None
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    results: list[str] = Field(default_factory=list)
    roadmap: str | None = None
    stack: list[Any] = Field(default_factory=list)
    team: list[Any] = Field(default_factory=list)
    quote: str | None = None
    confidence: ConfidenceScores = Field(default_factory=ConfidenceScores)
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    source_trace: list[SourceTraceItem] = Field(default_factory=list)

    @field_validator("tasks", "inputs", "outputs", "results", "missing_fields", "assumptions", mode="before")
    @classmethod
    def ensure_str_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v.strip() else []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return []
