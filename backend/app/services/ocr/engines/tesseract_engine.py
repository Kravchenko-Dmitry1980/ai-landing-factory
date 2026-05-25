"""Tesseract OCR engine (optional dependency)."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

from app.services.ocr.engines.base import OcrEngine
from app.services.ocr.ocr_contracts import OcrEngineResult

logger = logging.getLogger(__name__)


class TesseractOcrEngine(OcrEngine):
    name = "tesseract"

    def __init__(self) -> None:
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
            self._available = True
        except Exception:
            logger.debug("Tesseract/pytesseract not available")
            self._available = False
        return self._available

    def extract_text(self, image: bytes | Path) -> OcrEngineResult:
        if not self.is_available():
            return OcrEngineResult(
                warnings=[
                    "Tesseract not available; install pytesseract and tesseract binary.",
                ],
            )
        try:
            import pytesseract
            from PIL import Image

            if isinstance(image, bytes):
                img = Image.open(BytesIO(image))
            else:
                img = Image.open(image)
            text = pytesseract.image_to_string(img, lang="rus+eng")
            data = pytesseract.image_to_data(img, lang="rus+eng", output_type=pytesseract.Output.DICT)
            confidences = [
                float(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and float(c) >= 0
            ]
            avg_conf = sum(confidences) / len(confidences) / 100.0 if confidences else None
            return OcrEngineResult(text=text.strip(), confidence=avg_conf)
        except Exception as exc:
            logger.warning("Tesseract extraction failed: %s", exc)
            return OcrEngineResult(warnings=[f"Tesseract failed: {exc}"])
