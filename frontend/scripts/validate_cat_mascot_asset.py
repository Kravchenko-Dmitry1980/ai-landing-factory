"""Validate cat-assistant.png for WOW hero (dimensions + transparency)."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - build env should have Pillow
    Image = None  # type: ignore

FRONTEND = Path(__file__).resolve().parents[1]
DEFAULT_ASSET = FRONTEND / "public" / "assets" / "wow" / "cat-assistant.png"
MIN_TRANSPARENT_RATIO = 0.08
MAX_WIDTH_TO_HEIGHT = 1.35


def _png_dimensions(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 24:
        return None
    w, h = struct.unpack(">II", data[16:24])
    return (w, h) if w > 0 and h > 0 else None


def validate(path: Path = DEFAULT_ASSET) -> None:
    if not path.is_file():
        raise ValueError(f"cat mascot asset missing: {path}")
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"{path.name} must be PNG with alpha (got non-PNG)")
    dims = _png_dimensions(data)
    if dims is None:
        raise ValueError(f"{path.name} has unreadable PNG dimensions")
    width, height = dims
    if width > height * MAX_WIDTH_TO_HEIGHT:
        raise ValueError(
            f"{path.name} looks like a wide landing screenshot ({width}x{height})"
        )
    if Image is None:
        return
    img = Image.open(path).convert("RGBA")
    alpha = img.split()[-1]
    lo, hi = alpha.getextrema()
    if hi < 255 or lo >= 250:
        raise ValueError(
            f"{path.name} has no transparent background (alpha range {lo}-{hi}); "
            "run frontend/scripts/prepare_transparent_cat_mascot.py"
        )
    alpha_values = getattr(alpha, "get_flattened_data", alpha.getdata)()
    transparent = sum(1 for v in alpha_values if v < 250)
    ratio = transparent / (img.width * img.height)
    if ratio < MIN_TRANSPARENT_RATIO:
        raise ValueError(
            f"{path.name} has too little transparency ({ratio:.1%}); "
            "expected standalone cat without opaque backdrop"
        )


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ASSET
    try:
        validate(target)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: transparent cat mascot valid ({target})")


if __name__ == "__main__":
    main()
