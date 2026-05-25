"""Smoke test: unified generate + architecture topology (Stage F)."""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
from app.schemas.landing_contract import LandingBlock, LandingContract, LandingStylePreset
from app.services.architecture.topology_builder import build_topology
from app.services.semantic.fallback_generator import generate_fallback_semantic


async def main() -> None:
    from app.config import settings

    repo = ContractRepository(settings)
    pid = uuid4()
    contract = LandingContract(
        project_id=pid,
        style=LandingStylePreset.TECH,
        title="Smoke Test Project",
        blocks=[
            LandingBlock(key="inputs", title="Inputs", content="DOCX, PDF", bullets=["FastAPI", "PII Guard"]),
            LandingBlock(key="outputs", title="Outputs", content="", bullets=["Interactive landing"]),
            LandingBlock(key="tech_stack", title="Stack", content="", bullets=["React", "PostgreSQL", "Redis"]),
        ],
        updated_at=utc_now(),
    )
    await repo.save_contract(contract)
    semantic = generate_fallback_semantic(contract)
    topo = build_topology(contract, semantic)
    print(f"project_id={pid}")
    print(f"nodes={topo.node_count} edges={topo.edge_count} diagram={topo.diagram_type}")
    print(f"warnings={topo.warnings}")
    assert topo.node_count >= 2, "expected grounded nodes"
    assert topo.edge_count >= 1, "expected at least one edge"
    print("OK: Stage F topology smoke passed")


if __name__ == "__main__":
    asyncio.run(main())
