"""Prepare standalone transparent cat-assistant.png for WOW hero (Stage P.8.1).

Removes near-white background via corner flood-fill so the mascot sits on the
hero CSS background without an opaque white plate.

Usage (from repo root):
    python frontend/scripts/prepare_transparent_cat_mascot.py [source.png]
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PIL import Image

FRONTEND = Path(__file__).resolve().parents[1]
DEFAULT_OUT = FRONTEND / "public" / "assets" / "wow" / "cat-assistant.png"
TARGET_SIZE = 1024


def _is_background(r: int, g: int, b: int, *, tolerance: int = 28) -> bool:
    """True for flat near-white studio/backdrop pixels."""

    lum = (r + g + b) / 3.0
    chroma = max(r, g, b) - min(r, g, b)
    return lum >= 235 - tolerance * 0.35 and chroma <= 22 + tolerance * 0.25


def flood_transparent(img: Image.Image) -> Image.Image:
    """Flood-fill background from image corners; keep subject + contact shadow."""

    rgba = img.convert("RGBA")
    w, h = rgba.size
    pixels = rgba.load()
    visited = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        q.append((x, y))

    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        visited[y][x] = True
        r, g, b, a = pixels[x, y]
        if a == 0 or not _is_background(r, g, b):
            continue
        pixels[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return rgba


def prepare(source: Path, dest: Path = DEFAULT_OUT) -> None:
    img = Image.open(source)
    if max(img.size) != TARGET_SIZE:
        img = img.convert("RGBA")
        img.thumbnail((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
        ox = (TARGET_SIZE - img.width) // 2
        oy = (TARGET_SIZE - img.height) // 2
        canvas.paste(img, (ox, oy), img)
        img = canvas
    out = flood_transparent(img)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest, format="PNG", optimize=True)
    alpha = out.split()[-1]
    lo, hi = alpha.getextrema()
    transparent = sum(1 for v in alpha.getdata() if v < 250)
    total = alpha.size[0] * alpha.size[1]
    print(f"OK: saved {dest} ({out.width}x{out.height}) alpha={lo}-{hi} "
          f"transparent_px={transparent}/{total} ({100 * transparent / total:.1f}%)")


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    if not src.is_file():
        print(f"FAIL: source not found: {src}", file=sys.stderr)
        sys.exit(1)
    prepare(src, DEFAULT_OUT)


if __name__ == "__main__":
    main()
