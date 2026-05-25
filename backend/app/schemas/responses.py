from pydantic import BaseModel

from app.schemas.enrichment import EnrichmentMetadata
from app.schemas.landing_contract import LandingContract


class EnrichmentResponse(BaseModel):
    contract: LandingContract
    enrichment: EnrichmentMetadata
    message: str = ""
