"""OCR result cache."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from app.config import settings
from app.schemas.ocr import OcrItem

logger = logging.getLogger(__name__)


def _cache_key(
    file_bytes: bytes,
    page_or_slide: int | None,
    image_index: int | None,
    engine: str,
    dpi: int,
) -> str:
    payload = (
        file_bytes
        + str(page_or_slide or 0).encode()
        + str(image_index or 0).encode()
        + engine.encode()
        + str(dpi).encode()
    )
    return hashlib.sha256(payload).hexdigest()


def get_cached_item(
    file_bytes: bytes,
    page_or_slide: int | None,
    image_index: int | None,
    engine: str,
    dpi: int,
) -> OcrItem | None:
    if not settings.ocr_cache_enabled:
        return None
    key = _cache_key(file_bytes, page_or_slide, image_index, engine, dpi)
    path = settings.ocr_cache_dir / f"{key}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return OcrItem.model_validate(data)
    except Exception as exc:
        logger.debug("OCR cache read failed %s: %s", path, exc)
        return None


def store_cached_item(
    file_bytes: bytes,
    item: OcrItem,
    page_or_slide: int | None,
    image_index: int | None,
    engine: str,
    dpi: int,
) -> None:
    if not settings.ocr_cache_enabled:
        return
    settings.ocr_cache_dir.mkdir(parents=True, exist_ok=True)
    key = _cache_key(file_bytes, page_or_slide, image_index, engine, dpi)
    path = settings.ocr_cache_dir / f"{key}.json"
    try:
        path.write_text(item.model_dump_json(indent=2), encoding="utf-8")
    except Exception as exc:
        logger.debug("OCR cache write failed %s: %s", path, exc)
