import logging
from uuid import UUID

from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
from app.schemas.generation import GeneratedLanding, LandingBlockContent
from app.services.generation.base import LandingGenerator
from app.services.prompts.engine import PromptEngine

logger = logging.getLogger(__name__)


class StubGenerationService(LandingGenerator):
    """MVP: copies contract blocks; later wire PromptEngine + LLM."""

    def __init__(
        self,
        prompt_engine: PromptEngine,
        repository: ContractRepository,
    ) -> None:
        self._prompts = prompt_engine
        self._repo = repository

    async def generate(self, project_id: UUID) -> GeneratedLanding:
        contract = await self._repo.get_contract(project_id)
        if not contract:
            raise ValueError(f"No LandingContract for project {project_id}")

        # Prepare prompt context for future LLM call
        _ = self._prompts.build_generation_prompt(contract)

        blocks = [
            LandingBlockContent(
                key=b.key,
                title=b.title,
                body=b.content or (b.bullets[0] if b.bullets else ""),
                bullets=b.bullets,
            )
            for b in contract.blocks
        ]

        if contract.fidelity and contract.fidelity.modules:
            mod_bullets = [
                f"{m.name}: {m.description[:300]}"
                for m in contract.fidelity.modules
            ]
            blocks.insert(
                1,
                LandingBlockContent(
                    key="modules",
                    title="Ключевые системы",
                    body="",
                    bullets=mod_bullets,
                ),
            )

        landing = GeneratedLanding(
            project_id=project_id,
            style=contract.style,
            blocks=blocks,
            generated_at=utc_now(),
        )
        await self._repo.save_landing(landing)
        logger.info("Landing generated (stub) for %s", project_id)
        return landing
