"""Load standalone image files for OCR."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImageLoadItem:
    image_bytes: bytes
    ext: str
    width: int | None = None
    height: int | None = None


def load_image_bytes(path: Path) -> ImageLoadItem | None:
    if not path.exists():
        return None
    data = path.read_bytes()
    ext = path.suffix.lstrip(".").lower() or "png"
    return ImageLoadItem(image_bytes=data, ext=ext)
