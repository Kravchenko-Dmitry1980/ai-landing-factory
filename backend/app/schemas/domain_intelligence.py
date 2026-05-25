"""Domain Intelligence & Knowledge Graph schemas (Stage G)."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PrimaryDomain(str, Enum):
    MEDICAL_AI = "medical_ai"
    EDUCATION_AI = "education_ai"
    ENTERPRISE_AI = "enterprise_ai"
    ANALYTICS_PLATFORM = "analytics_platform"
    NEUROASSISTANT = "neuroassistant"
    RAG_SYSTEM = "rag_system"
    MULTI_AGENT_SYSTEM = "multi_agent_system"
    COMPUTER_VISION = "computer_vision"
    SPEECH_AI = "speech_ai"
    HR_AI = "hr_ai"
    SALES_AI = "sales_ai"
    DOCUMENT_AI = "document_ai"
    INFRASTRUCTURE_AI = "infrastructure_ai"
    GENERAL = "general"


class SystemArchetypeType(str, Enum):
    AI_COPILOT = "AI Copilot"
    RAG_KNOWLEDGE_ASSISTANT = "RAG Knowledge Assistant"
    MULTI_AGENT_ORCHESTRATOR = "Multi-Agent Orchestrator"
    ANALYTICS_DASHBOARD = "Analytics Dashboard"
    DECISION_SUPPORT_SYSTEM = "Decision Support System"
    WORKFLOW_AUTOMATION_PLATFORM = "Workflow Automation Platform"
    DOCUMENT_PROCESSING_PIPELINE = "Document Processing Pipeline"
    REALTIME_SPEECH_PIPELINE = "Realtime Speech Pipeline"
    CV_DIAGNOSTIC_ASSISTANT = "CV Diagnostic Assistant"
    LEARNING_PLATFORM = "Learning Platform"
    RECOMMENDATION_ENGINE = "Recommendation Engine"


class ArchitecturePatternType(str, Enum):
    INGESTION_PIPELINE = "ingestion pipeline"
    RAG_PIPELINE = "RAG pipeline"
    MULTI_AGENT_ORCHESTRATION = "multi-agent orchestration"
    EVENT_DRIVEN_ARCHITECTURE = "event-driven architecture"
    REAL_TIME_STREAMING = "real-time streaming"
    HUMAN_IN_THE_LOOP = "human-in-the-loop"
    PRIVACY_FIRST_ARCHITECTURE = "privacy-first architecture"
    MICROSERVICES = "microservices"
    MONOLITH_MVP = "monolith MVP"
    API_GATEWAY = "API gateway"
    ASYNC_WORKER_PIPELINE = "async worker pipeline"
    VECTOR_SEARCH = "vector search"
    SEMANTIC_ENRICHMENT = "semantic enrichment"
    CLINICAL_DECISION_SUPPORT = "clinical decision support"
    SCORING_ENGINE = "scoring engine"
    RECOMMENDATION_ENGINE = "recommendation engine"


class EntityType(str, Enum):
    PROJECT = "project"
    MODULE = "module"
    SUBSYSTEM = "subsystem"
    ACTOR = "actor"
    STAKEHOLDER = "stakeholder"
    DATA_SOURCE = "data_source"
    DOCUMENT_SOURCE = "document_source"
    AI_MODEL = "ai_model"
    LLM = "llm"
    CV_MODEL = "cv_model"
    SPEECH_MODEL = "speech_model"
    VECTOR_DB = "vector_db"
    DATABASE = "database"
    API = "api"
    PIPELINE = "pipeline"
    PROCESS = "process"
    INTERFACE = "interface"
    METRIC = "metric"
    RISK = "risk"
    OUTPUT = "output"
    INTEGRATION = "integration"
    SECURITY_LAYER = "security_layer"
    COMPLIANCE_CONSTRAINT = "compliance_constraint"
    TEAM_ROLE = "team_role"
    TECHNOLOGY = "technology"


class RelationType(str, Enum):
    USES = "uses"
    DEPENDS_ON = "depends_on"
    PRODUCES = "produces"
    CONSUMES = "consumes"
    TRANSFORMS = "transforms"
    VALIDATES = "validates"
    STORES = "stores"
    RETRIEVES_FROM = "retrieves_from"
    SENDS_TO = "sends_to"
    RECEIVES_FROM = "receives_from"
    ORCHESTRATES = "orchestrates"
    PROTECTS = "protects"
    MEASURES = "measures"
    MITIGATES = "mitigates"
    INTEGRATES_WITH = "integrates_with"
    BELONGS_TO = "belongs_to"
    SUPPORTS = "supports"
    EXPOSES = "exposes"
    TRIGGERS = "triggers"


class DomainProfile(BaseModel):
    primary_domain: PrimaryDomain = PrimaryDomain.GENERAL
    secondary_domains: list[PrimaryDomain] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SystemArchetype(BaseModel):
    archetype: SystemArchetypeType | str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = ""
    evidence: list[str] = Field(default_factory=list)


class ArchitecturePattern(BaseModel):
    pattern: ArchitecturePatternType | str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    detected_from: str = ""
    evidence: list[str] = Field(default_factory=list)
    related_modules: list[str] = Field(default_factory=list)


class KnowledgeEntity(BaseModel):
    id: str
    label: str
    entity_type: EntityType | str
    description: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_fields: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    pii_safe: bool = True

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: Any) -> float:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, f))


class KnowledgeRelation(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType | str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    inferred: bool = False


class ConfidenceSummary(BaseModel):
    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    domain: float = 0.0
    archetype: float = 0.0
    patterns: float = 0.0
    entities: float = 0.0
    relations: float = 0.0


class ProjectKnowledgeGraph(BaseModel):
    project_id: UUID
    domain_profile: DomainProfile = Field(default_factory=DomainProfile)
    system_archetypes: list[SystemArchetype] = Field(default_factory=list)
    architecture_patterns: list[ArchitecturePattern] = Field(default_factory=list)
    entities: list[KnowledgeEntity] = Field(default_factory=list)
    relations: list[KnowledgeRelation] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    missing_knowledge: list[str] = Field(default_factory=list)
    confidence_summary: ConfidenceSummary = Field(default_factory=ConfidenceSummary)


class DomainIntelligenceReport(BaseModel):
    project_id: UUID
    status: str = "completed"
    graph: ProjectKnowledgeGraph
    warnings: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
