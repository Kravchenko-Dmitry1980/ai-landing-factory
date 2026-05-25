"""Smoke test for Stage G domain intelligence."""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.models.domain import utc_now
from app.repositories.domain_repository import DomainRepository
from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.services.domain.engine import DomainIntelligenceEngine
from app.services.pipeline.pii_stage import PIIStageService


async def main() -> None:
    contract = LandingContract(
        project_id=uuid4(),
        title="Medical Copilot",
        style=LandingStylePreset.TECH,
        blocks=[
            LandingBlock(
                key="essence",
                title="Essence",
                content="AI copilot for physician with Whisper STT and clinical audit",
                bullets=[],
            ),
            LandingBlock(
                key="tech_stack",
                title="Stack",
                content="",
                bullets=["Whisper", "FastAPI", "PostgreSQL"],
            ),
        ],
        updated_at=utc_now(),
    )
    repo = DomainRepository(settings)
    engine = DomainIntelligenceEngine(settings, repo, PIIStageService(settings))
    report = await engine.analyze(contract, force=True)
    g = report.graph
    print(f"Domain: {g.domain_profile.primary_domain.value} ({g.domain_profile.confidence:.2f})")
    print(f"Archetypes: {[a.archetype for a in g.system_archetypes]}")
    print(f"Patterns: {[p.pattern for p in g.architecture_patterns[:3]]}")
    print(f"Entities: {len(g.entities)} Relations: {len(g.relations)}")
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
