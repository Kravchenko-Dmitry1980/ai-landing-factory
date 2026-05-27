"""Tesseract OCR engine (optional dependency)."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

from app.config import settings
from app.services.ocr.engines.base import OcrEngine
from app.services.ocr.ocr_contracts import OcrEngineResult

logger = logging.getLogger(__name__)


def get_tesseract_lang() -> str:
    return (settings.ocr_tesseract_lang or "rus+eng").strip() or "rus+eng"


def check_russian_language_available() -> tuple[bool, list[str]]:
    """Return (rus_available, installed_languages)."""
    try:
        import pytesseract

        langs = pytesseract.get_languages(config="")
        has_rus = "rus" in langs
        return has_rus, langs
    except Exception:
        return False, []


def tesseract_language_warnings() -> list[str]:
    warnings: list[str] = []
    has_rus, langs = check_russian_language_available()
    if not has_rus:
        warnings.append(
            "Russian language data 'rus' is missing. OCR of Russian names may be poor."
        )
    lang = get_tesseract_lang()
    if "rus" in lang and not has_rus:
        warnings.append(f"Configured OCR_TESSERACT_LANG={lang!r} but 'rus' is not installed.")
    if langs and logger.isEnabledFor(logging.DEBUG):
        logger.debug("Tesseract languages: %s", langs)
    return warnings


class TesseractOcrEngine(OcrEngine):
    name = "tesseract"

    def __init__(self) -> None:
        self._available: bool | None = None
        self._last_lang: str | None = None

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

    @property
    def lang(self) -> str:
        return get_tesseract_lang()

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

            lang = self.lang
            self._last_lang = lang
            warnings = list(tesseract_language_warnings())

            if isinstance(image, bytes):
                img = Image.open(BytesIO(image))
            else:
                img = Image.open(image)
            text = pytesseract.image_to_string(img, lang=lang)
            data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
            confidences = [
                float(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and float(c) >= 0
            ]
            avg_conf = sum(confidences) / len(confidences) / 100.0 if confidences else None
            return OcrEngineResult(text=text.strip(), confidence=avg_conf, warnings=warnings)
        except Exception as exc:
            logger.warning("Tesseract extraction failed: %s", exc)
            return OcrEngineResult(warnings=[f"Tesseract failed: {exc}"])
