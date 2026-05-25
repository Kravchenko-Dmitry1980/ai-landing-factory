from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID

from app.schemas.extraction import ExtractionResult, FileExtraction


class FileExtractor(ABC):
    """Extracts plain text from a single file on disk."""

    @abstractmethod
    def supports(self, path: Path) -> bool:
        ...

    @abstractmethod
    def extract(self, path: Path, filename: str | None = None) -> FileExtraction:
        ...


class DocumentExtractor(ABC):
    """Project-level extraction orchestration."""

    @abstractmethod
    async def extract(self, project_id: UUID) -> ExtractionResult:
        """Produce ExtractionResult from all stored project files."""
