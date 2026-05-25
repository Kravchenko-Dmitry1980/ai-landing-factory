"""OCR engine base interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.services.ocr.ocr_contracts import OcrEngineResult


class OcrEngine(ABC):
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when engine and dependencies are ready."""

    @abstractmethod
    def extract_text(self, image: bytes | Path) -> OcrEngineResult:
        """Extract text from image bytes or file path."""
