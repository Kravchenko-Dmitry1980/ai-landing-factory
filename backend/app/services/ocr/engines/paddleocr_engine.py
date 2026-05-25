"""PaddleOCR engine (optional dependency)."""

from __future__ import annotations

import logging
from pathlib import Path

from app.services.ocr.engines.base import OcrEngine
from app.services.ocr.ocr_contracts import OcrEngineResult

logger = logging.getLogger(__name__)


class PaddleOcrEngine(OcrEngine):
    name = "paddleocr"

    def __init__(self) -> None:
        self._ocr = None
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            from paddleocr import PaddleOCR  # noqa: F401

            self._available = True
        except ImportError:
            logger.debug("PaddleOCR not installed")
            self._available = False
        return self._available

    def _ensure_engine(self) -> bool:
        if not self.is_available():
            return False
        if self._ocr is None:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(use_angle_cls=True, lang="ru", show_log=False)
        return True

    def extract_text(self, image: bytes | Path) -> OcrEngineResult:
        if not self._ensure_engine():
            return OcrEngineResult(
                warnings=["PaddleOCR not installed; install paddleocr for primary OCR."],
            )
        try:
            import tempfile

            if isinstance(image, bytes):
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(image)
                    path = tmp.name
            else:
                path = str(image)

            result = self._ocr.ocr(path, cls=True)
            lines: list[str] = []
            confidences: list[float] = []
            if result:
                for block in result:
                    if not block:
                        continue
                    for line in block:
                        if len(line) >= 2:
                            text_part = line[1]
                            if isinstance(text_part, (list, tuple)) and text_part:
                                lines.append(str(text_part[0]))
                                if len(text_part) > 1 and text_part[1] is not None:
                                    confidences.append(float(text_part[1]))
            text = "\n".join(lines)
            avg_conf = sum(confidences) / len(confidences) if confidences else None
            return OcrEngineResult(text=text, confidence=avg_conf)
        except Exception as exc:
            logger.warning("PaddleOCR extraction failed: %s", exc)
            return OcrEngineResult(warnings=[f"PaddleOCR failed: {exc}"])
