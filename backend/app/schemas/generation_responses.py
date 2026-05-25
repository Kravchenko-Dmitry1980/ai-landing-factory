from pydantic import BaseModel, Field

from app.schemas.architecture import ArchitectureTopology
from app.schemas.generation import GeneratedLanding
from app.schemas.semantic_generation import GeneratedSemanticLanding
from app.schemas.semantic_responses import SemanticGenerationResponse


class GenerateRequest(BaseModel):
    enrich: bool = False
    mode: str = Field(default="full", pattern="^(full|stub)$")


class UnifiedGenerateResponse(BaseModel):
    semantic: GeneratedSemanticLanding | None = None
    landing: GeneratedLanding
    architecture: ArchitectureTopology | None = None
    message: str = ""


class ArchitectureResponse(BaseModel):
    project_id: str
    architecture: ArchitectureTopology | None = None
    has_topology: bool = False


class SemanticDebugResponse(BaseModel):
    semantic: GeneratedSemanticLanding
    architecture: ArchitectureTopology | None = None
    topology_warnings: list[str] = Field(default_factory=list)
