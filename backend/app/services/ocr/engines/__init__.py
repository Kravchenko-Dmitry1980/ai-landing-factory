"""Optional OCR engines."""

from app.services.ocr.engines.base import OcrEngine
from app.services.ocr.engines.paddleocr_engine import PaddleOcrEngine
from app.services.ocr.engines.tesseract_engine import TesseractOcrEngine

__all__ = ["OcrEngine", "PaddleOcrEngine", "TesseractOcrEngine", "EasyOcrEngine", "SuryaOcrEngine"]

try:
    from app.services.ocr.engines.easyocr_engine import EasyOcrEngine
except ImportError:
    EasyOcrEngine = None  # type: ignore

try:
    from app.services.ocr.engines.surya_engine import SuryaOcrEngine
except ImportError:
    SuryaOcrEngine = None  # type: ignore
