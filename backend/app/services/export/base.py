from abc import ABC, abstractmethod
from uuid import UUID


class LandingExporter(ABC):
    @abstractmethod
    async def to_html(self, project_id: UUID) -> str:
        ...

    @abstractmethod
    async def to_json_bundle(self, project_id: UUID) -> dict:
        ...
