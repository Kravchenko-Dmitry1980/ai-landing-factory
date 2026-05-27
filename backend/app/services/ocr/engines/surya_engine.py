"""Surya OCR engine (experimental optional dependency)."""

from __future__ import annotations

import logging
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

from app.services.ocr.engines.base import OcrEngine
from app.services.ocr.ocr_contracts import OcrEngineResult

logger = logging.getLogger(__name__)

SURYA_UNAVAILABLE = "Surya OCR package not installed or API unsupported."


class SuryaOcrEngine(OcrEngine):
    name = "surya"

    def __init__(self) -> None:
        self._available: bool | None = None
        self._init_error: str | None = None
        self._predictors: Any = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import surya  # noqa: F401

            self._available = True
        except ImportError:
            self._init_error = SURYA_UNAVAILABLE
            self._available = False
        return self._available

    def extract_text(self, image: bytes | Path) -> OcrEngineResult:
        if not self.is_available():
            return OcrEngineResult(warnings=[self._init_error or SURYA_UNAVAILABLE])
        try:
            from PIL import Image

            if isinstance(image, (str, Path)):
                img = Image.open(image)
            else:
                img = Image.open(BytesIO(image))

            # Experimental adapter — API varies by surya version.
            try:
                from surya.foundation import FoundationPredictor
                from surya.recognition import RecognitionPredictor
                from surya.detection import DetectionPredictor

                if self._predictors is None:
                    foundation = FoundationPredictor()
                    self._predictors = (
                        DetectionPredictor(),
                        RecognitionPredictor(foundation),
                    )
                det, rec = self._predictors
                det_result = det([img])
                rec_result = rec([img], det_result)
                lines: list[str] = []
                for page in rec_result:
                    for line in getattr(page, "text_lines", []) or []:
                        text = getattr(line, "text", "") or ""
                        if text.strip():
                            lines.append(text.strip())
                if lines:
                    return OcrEngineResult(text="\n".join(lines))
            except Exception as api_exc:
                logger.debug("Surya modern API failed: %s", api_exc)

            # Legacy fallback attempt
            try:
                from surya.ocr import run_ocr

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    img.save(tmp.name)
                    path = tmp.name
                result = run_ocr([path])
                lines = []
                for page in result or []:
                    for line in page.get("text_lines", []):
                        text = line.get("text", "")
                        if text.strip():
                            lines.append(text.strip())
                if lines:
                    return OcrEngineResult(text="\n".join(lines))
            except Exception as legacy_exc:
                logger.debug("Surya legacy API failed: %s", legacy_exc)

            return OcrEngineResult(warnings=[SURYA_UNAVAILABLE])
        except Exception as exc:
            logger.warning("Surya extraction failed: %s", exc)
            return OcrEngineResult(warnings=[f"Surya failed: {exc}"])
