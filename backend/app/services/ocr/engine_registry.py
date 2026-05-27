"""OCR engine registry — lazy factory for optional engines."""

from __future__ import annotations

from app.services.ocr.engines.base import OcrEngine

SUPPORTED_ENGINES = ("tesseract", "easyocr", "paddleocr", "surya")


def create_engine(name: str) -> OcrEngine | None:
    """Create engine instance by name (may be unavailable at runtime)."""
    key = name.strip().lower()
    if key == "tesseract":
        from app.services.ocr.engines.tesseract_engine import TesseractOcrEngine

        return TesseractOcrEngine()
    if key == "easyocr":
        from app.services.ocr.engines.easyocr_engine import EasyOcrEngine

        return EasyOcrEngine()
    if key == "paddleocr":
        from app.services.ocr.engines.paddleocr_engine import PaddleOcrEngine

        return PaddleOcrEngine()
    if key == "surya":
        from app.services.ocr.engines.surya_engine import SuryaOcrEngine

        return SuryaOcrEngine()
    return None


def parse_engine_list(raw: str) -> list[str]:
    return [part.strip().lower() for part in raw.split(",") if part.strip()]
