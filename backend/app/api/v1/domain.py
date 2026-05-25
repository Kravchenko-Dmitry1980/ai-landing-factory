"""Domain Intelligence API — Stage G."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.core.dependencies import get_contract_repository, get_domain_engine
from app.schemas.domain_intelligence import DomainIntelligenceReport, ProjectKnowledgeGraph

router = APIRouter()


@router.post("/{project_id}/domain-analyze", response_model=DomainIntelligenceReport)
async def domain_analyze(project_id: UUID) -> DomainIntelligenceReport:
    contract = await get_contract_repository().get_contract(project_id)
    if not contract:
        raise HTTPException(404, "LandingContract not found")
    return await get_domain_engine().analyze(contract, force=True)


@router.get("/{project_id}/domain-report", response_model=DomainIntelligenceReport)
async def get_domain_report(project_id: UUID) -> DomainIntelligenceReport:
    report = await get_domain_engine().get_report(project_id)
    if not report:
        raise HTTPException(404, "Domain intelligence report not found")
    return report


@router.get("/{project_id}/knowledge-graph", response_model=ProjectKnowledgeGraph)
async def get_knowledge_graph(project_id: UUID) -> ProjectKnowledgeGraph:
    graph = await get_domain_engine().get_graph(project_id)
    if not graph:
        raise HTTPException(404, "Knowledge graph not found")
    return graph
