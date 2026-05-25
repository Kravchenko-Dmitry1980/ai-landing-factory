"""Deterministic fallback when domain intelligence is disabled."""

from uuid import UUID

from app.models.domain import utc_now
from app.schemas.domain_intelligence import (
    DomainIntelligenceReport,
    DomainProfile,
    PrimaryDomain,
    ProjectKnowledgeGraph,
)
from app.schemas.landing_contract import LandingContract


def build_fallback_report(contract: LandingContract) -> DomainIntelligenceReport:
    graph = ProjectKnowledgeGraph(
        project_id=contract.project_id,
        domain_profile=DomainProfile(
            primary_domain=PrimaryDomain.GENERAL,
            confidence=0.3,
            evidence=["domain_intelligence_disabled"],
            warnings=["Domain intelligence layer disabled — minimal graph"],
        ),
        missing_knowledge=["Domain analysis skipped"],
    )
    return DomainIntelligenceReport(
        project_id=contract.project_id,
        status="fallback",
        graph=graph,
        warnings=["Domain intelligence disabled"],
        assumptions=["Using general domain fallback"],
        created_at=utc_now(),
    )
