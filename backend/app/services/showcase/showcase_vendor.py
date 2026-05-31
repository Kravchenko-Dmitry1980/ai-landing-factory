"""Vendored A-Frame runtime paths and export-side asset copying (Stage P.5.1)."""

from __future__ import annotations

import shutil
from pathlib import Path

# Relative script src emitted in exported showcase HTML (sibling to HTML file).
DEFAULT_AFRAME_SRC = "vendor/aframe/aframe.min.js"

# Allowlisted CDN override (explicit opt-in only).
ALLOWED_AFRAME_CDN = "https://aframe.io/releases/1.7.0/aframe.min.js"

_REPO_ROOT = Path(__file__).resolve().parents[4]
VENDOR_DIR = _REPO_ROOT / "frontend" / "public" / "vendor" / "aframe"
VENDOR_SOURCE = VENDOR_DIR / "aframe.min.js"
VENDOR_LICENSE = VENDOR_DIR / "LICENSE.txt"

# Hardcoded paths inside portable ZIP bundles (never user-controlled).
ZIP_HTML_NAME = "showcase.html"
ZIP_AFRAME_ENTRY = "vendor/aframe/aframe.min.js"
ZIP_LICENSE_ENTRY = "vendor/aframe/LICENSE.txt"
ZIP_DOWNLOAD_FILENAME = "ai-showcase.zip"


def is_local_aframe_src(src: str) -> bool:
    """True when the runtime is a relative/vendored path (not http(s))."""

    lowered = src.strip().lower()
    return not lowered.startswith("http://") and not lowered.startswith("https://")


def copy_aframe_vendor_to_export_dir(html_output_path: Path) -> Path:
    """Copy the vendored A-Frame runtime next to an exported showcase HTML file.

    Creates ``<html_dir>/vendor/aframe/aframe.min.js`` so ``file://`` and
    offline opens work without CDN.
    """

    if not VENDOR_SOURCE.is_file():
        raise FileNotFoundError(
            f"Vendored A-Frame runtime missing: {VENDOR_SOURCE}. "
            "Run from repo root after adding frontend/public/vendor/aframe/aframe.min.js"
        )
    dest = html_output_path.parent / "vendor" / "aframe" / "aframe.min.js"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(VENDOR_SOURCE, dest)
    return dest
