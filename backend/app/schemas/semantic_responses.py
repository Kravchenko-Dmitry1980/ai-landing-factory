from app.schemas.semantic_generation import GeneratedSemanticLanding
from app.schemas.generation import GeneratedLanding
from pydantic import BaseModel


class SemanticGenerationResponse(BaseModel):
    semantic: GeneratedSemanticLanding
    landing: GeneratedLanding
    message: str = ""
