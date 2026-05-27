"""EasyOCR engine (optional dependency)."""

from __future__ import annotations

import logging
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.ocr.engines.base import OcrEngine
from app.services.ocr.ocr_contracts import OcrEngineResult

logger = logging.getLogger(__name__)


def get_easyocr_langs() -> list[str]:
    raw = (settings.ocr_easyocr_langs or "ru,en").strip()
    langs = [part.strip() for part in raw.split(",") if part.strip()]
    return langs or ["ru", "en"]


class EasyOcrEngine(OcrEngine):
    name = "easyocr"

    def __init__(self) -> None:
        self._reader: Any = None
        self._available: bool | None = None
        self._init_error: str | None = None
        self._init_failed = False

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import easyocr  # noqa: F401

            self._available = True
        except ImportError as exc:
            self._init_error = f"easyocr not installed: {exc}"
            self._available = False
        return self._available

    def _ensure_reader(self) -> bool:
        if self._reader is not None:
            return True
        if self._init_failed:
            return False
        if not self.is_available():
            return False
        try:
            import easyocr

            langs = get_easyocr_langs()
            self._reader = easyocr.Reader(langs, gpu=settings.ocr_easyocr_gpu)
            self._init_error = None
            return True
        except Exception as exc:
            self._init_error = f"EasyOCR init failed: {exc}"
            self._init_failed = True
            logger.warning(self._init_error)
            return False

    def extract_text(self, image: bytes | Path) -> OcrEngineResult:
        if not self._ensure_reader():
            msg = self._init_error or "EasyOCR not available; pip install easyocr"
            return OcrEngineResult(warnings=[msg])
        try:
            path = self._materialize_image(image)
            raw_lines = self._reader.readtext(path)
            lines: list[str] = []
            confidences: list[float] = []
            for item in raw_lines:
                if not isinstance(item, (list, tuple)) or len(item) < 3:
                    continue
                text = str(item[1]).strip()
                if text:
                    lines.append(text)
                try:
                    confidences.append(float(item[2]))
                except (TypeError, ValueError):
                    pass
            text = "\n".join(lines).strip()
            avg_conf = sum(confidences) / len(confidences) if confidences else None
            return OcrEngineResult(text=text, confidence=avg_conf)
        except Exception as exc:
            logger.warning("EasyOCR extraction failed: %s", exc)
            return OcrEngineResult(warnings=[f"EasyOCR failed: {exc}"])

    @staticmethod
    def _materialize_image(image: bytes | Path) -> str:
        if isinstance(image, Path) or (isinstance(image, str) and Path(image).is_file()):
            return str(image)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(image)
            return tmp.name
