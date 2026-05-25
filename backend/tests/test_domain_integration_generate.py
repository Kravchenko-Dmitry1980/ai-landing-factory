"""Integration: generate pipeline uses domain report."""

import pytest
from uuid import uuid4

from app.config import Settings
from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
from app.repositories.domain_repository import DomainRepository
from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.services.domain.engine import DomainIntelligenceEngine
from app.services.pipeline.pii_stage import PIIStageService
from app.services.semantic.generator import SemanticGenerationEngine


@pytest.fixture
def settings(tmp_path):
    s = Settings(
        data_dir=tmp_path / "data",
        contracts_dir=tmp_path / "data" / "contracts",
        extractions_dir=tmp_path / "data" / "extractions",
        uploads_dir=tmp_path / "data" / "uploads",
        domain_intelligence_enabled=True,
        semantic_use_llm=False,
    )
    s.contracts_dir.mkdir(parents=True)
    s.domain_reports_dir.mkdir(parents=True)
    s.knowledge_graphs_dir.mkdir(parents=True)
    return s


@pytest.mark.asyncio
async def test_generate_uses_domain_report(settings):
    project_id = uuid4()
    contract = LandingContract(
        project_id=project_id,
        style=LandingStylePreset.TECH,
        blocks=[
            LandingBlock(
                key="essence",
                title="E",
                content="RAG Qdrant retrieval knowledge base",
                bullets=[],
            ),
            LandingBlock(
                key="tech_stack",
                title="Stack",
                content="",
                bullets=["FastAPI", "Qdrant"],
            ),
        ],
        updated_at=utc_now(),
    )
    repo = ContractRepository(settings)
    await repo.save_contract(contract)

    domain_repo = DomainRepository(settings)
    domain_engine = DomainIntelligenceEngine(settings, domain_repo, PIIStageService(settings))
    semantic_engine = SemanticGenerationEngine(settings, repo, PIIStageService(settings), domain_engine=domain_engine)

    result = await semantic_engine.generate(project_id)
    assert result.semantic.intelligence_domain_profile is not None
    assert result.semantic.intelligence_domain_profile.get("primary_domain") == "rag_system"
    assert result.semantic.metadata.domain_intelligence_id == str(project_id)

    report = await domain_repo.get_report(project_id)
    assert report is not None
    assert len(report.graph.entities) >= 1
