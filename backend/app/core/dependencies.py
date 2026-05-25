from functools import lru_cache

from app.config import Settings, settings
from app.repositories.contract_repository import ContractRepository
from app.repositories.domain_repository import DomainRepository
from app.repositories.file_store import FileStore
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.analysis.llm_contract_builder import LLMContractBuilderService
from app.services.extraction.base import DocumentExtractor
from app.services.extraction.dispatcher import DispatcherExtractionService
from app.services.generation.stub_generator import StubGenerationService
from app.services.domain.engine import DomainIntelligenceEngine
from app.services.pipeline.pii_stage import PIIStageService
from app.services.semantic.generator import SemanticGenerationEngine
from app.services.pii.safe_payload import SafeCloudPayloadService
from app.services.prompts.engine import PromptEngine


@lru_cache
def get_settings() -> Settings:
    return settings


def get_file_store() -> FileStore:
    return FileStore(get_settings())


def get_contract_repository() -> ContractRepository:
    return ContractRepository(get_settings())


def get_domain_repository() -> DomainRepository:
    return DomainRepository(get_settings())


def get_domain_engine() -> DomainIntelligenceEngine:
    return DomainIntelligenceEngine(
        get_settings(),
        get_domain_repository(),
        get_pii_stage(),
    )


def get_prompt_engine() -> PromptEngine:
    return PromptEngine()


def get_extraction_service() -> DocumentExtractor:
    return DispatcherExtractionService(get_file_store())


def get_contract_builder() -> ContractBuilderService:
    return ContractBuilderService(get_contract_repository())


def get_generation_service() -> StubGenerationService:
    return StubGenerationService(get_prompt_engine(), get_contract_repository())


def get_pii_stage() -> PIIStageService:
    return PIIStageService(get_settings())


def get_safe_cloud_payload_service() -> SafeCloudPayloadService:
    return SafeCloudPayloadService(get_settings(), get_pii_stage())


def get_llm_contract_builder() -> LLMContractBuilderService:
    return LLMContractBuilderService(
        get_settings(),
        get_contract_repository(),
        get_contract_builder(),
        get_prompt_engine(),
        get_pii_stage(),
    )


def get_semantic_engine() -> SemanticGenerationEngine:
    return SemanticGenerationEngine(
        get_settings(),
        get_contract_repository(),
        get_pii_stage(),
        get_prompt_engine(),
        get_domain_engine(),
    )


def get_unified_generator():
    from app.services.generation.unified_generator import UnifiedGenerationService

    return UnifiedGenerationService(
        get_semantic_engine(),
        get_generation_service(),
        get_llm_contract_builder(),
        get_domain_engine(),
    )
