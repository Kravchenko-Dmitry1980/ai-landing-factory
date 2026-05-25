"""Optional OCR engines."""

from app.services.ocr.engines.base import OcrEngine
from app.services.ocr.engines.paddleocr_engine import PaddleOcrEngine
from app.services.ocr.engines.tesseract_engine import TesseractOcrEngine

__all__ = ["OcrEngine", "PaddleOcrEngine", "TesseractOcrEngine"]
