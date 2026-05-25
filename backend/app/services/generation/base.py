from abc import ABC, abstractmethod
from uuid import UUID

from app.schemas.generation import GeneratedLanding


class LandingGenerator(ABC):
    @abstractmethod
    async def generate(self, project_id: UUID) -> GeneratedLanding:
        """Produce render-ready copy from LandingContract via prompts."""
