"""Semantic AI generation schemas (Stage E)."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.architecture import ArchitectureTopology


class DomainProfile(str, Enum):
    MEDICAL = "medical"
    EDUCATION = "education"
    AI_RESEARCH = "ai_research"
    ANALYTICS = "analytics"
    ENTERPRISE = "enterprise"
    NEURO = "neuro"
    FINTECH = "fintech"
    INFRASTRUCTURE = "infrastructure"
    CYBERSECURITY = "cybersecurity"
    GENERAL = "general"


class SectionType(str, Enum):
    PROBLEM = "problem"
    SYSTEM = "system"
    ARCHITECTURE = "architecture"
    MODULES = "modules"
    METRICS = "metrics"
    PIPELINE = "pipeline"
    COMPLIANCE = "compliance"
    VALIDATION = "validation"
    LEARNING_FLOW = "learning_flow"
    DASHBOARDS = "dashboards"
    INGESTION = "ingestion"
    ORCHESTRATION = "orchestration"
    ROADMAP = "roadmap"
    STACK = "stack"
    TEAM = "team"
    ESSENCE = "essence"
    INSIGHTS = "insights"


class SectionConfidence(BaseModel):
    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    factual_grounding: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("overall", "factual_grounding", "completeness", mode="before")
    @classmethod
    def clamp(cls, v: Any) -> float:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, f))


class ArchitectureNode(BaseModel):
    id: str
    label: str
    role: str | None = None
    connections: list[str] = Field(default_factory=list)


class SemanticSection(BaseModel):
    section_type: SectionType | str
    semantic_goal: str = ""
    title: str = ""
    subtitle: str | None = None
    narrative: str = ""
    bullets: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    architecture_nodes: list[ArchitectureNode] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    callouts: list[str] = Field(default_factory=list)
    visual_hints: list[str] = Field(default_factory=list)
    confidence: SectionConfidence = Field(default_factory=SectionConfidence)
    source_keys: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class SemanticNarrative(BaseModel):
    arc: str = "problem_system_architecture_modules_metrics_roadmap"
    problem: str = ""
    system: str = ""
    architecture: str = ""
    modules: str = ""
    metrics: str = ""
    roadmap: str = ""
    tone: str = "engineering-first"


class SourceTraceEntry(BaseModel):
    field: str
    section_type: str
    source_key: str | None = None
    evidence: str = Field(default="", max_length=500)


class SemanticGenerationMetadata(BaseModel):
    provider: str = "fallback"
    llm_enabled: bool = False
    fallback_used: bool = True
    domain: DomainProfile = DomainProfile.GENERAL
    layout_preset: str = "architecture_first"
    style_profile: str = "enterprise"
    selected_sections: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    hallucination_warnings: list[str] = Field(default_factory=list)
    source_trace: list[SourceTraceEntry] = Field(default_factory=list)
    privacy_redacted: bool = False
    generated_at: datetime | None = None
    prompt_version: str = "semantic-v1"
    domain_intelligence_id: str | None = None


class GeneratedSemanticLanding(BaseModel):
    project_id: UUID
    domain: DomainProfile = DomainProfile.GENERAL
    layout_preset: str = "architecture_first"
    style_profile: str = "enterprise"
    narrative: SemanticNarrative = Field(default_factory=SemanticNarrative)
    sections: list[SemanticSection] = Field(default_factory=list)
    architecture: ArchitectureTopology | None = None
    metadata: SemanticGenerationMetadata = Field(default_factory=SemanticGenerationMetadata)
    # Stage G domain intelligence (PII-safe summaries)
    intelligence_domain_profile: dict[str, Any] | None = None
    system_archetypes: list[dict[str, Any]] = Field(default_factory=list)
    architecture_patterns: list[dict[str, Any]] = Field(default_factory=list)
