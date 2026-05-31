#!/usr/bin/env python3
"""Optional P.5.2 smoke: portable showcase ZIP bundle export.

Usage:
    cd C:\\Dima\\Projects\\CURSOR\\_uat\\ai-landing-factory-fresh\\backend
    ..\\.venv\\Scripts\\python.exe scripts\\smoke_showcase_zip_export.py

Checks (no network, no backend server required):
    * ZIP created with expected entries;
    * showcase.html references local vendor path;
    * no aframe.io CDN by default;
    * malicious project text / URLs sanitized in bundled HTML.
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.showcase.showcase_schema import ShowcaseConfig, ShowcaseProject
from app.services.showcase.showcase_vendor import (
    DEFAULT_AFRAME_SRC,
    VENDOR_SOURCE,
    ZIP_AFRAME_ENTRY,
    ZIP_HTML_NAME,
    ZIP_LICENSE_ENTRY,
)
from app.services.showcase.showcase_zip_exporter import build_showcase_zip_with_meta


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def _assert_no_unsafe_zip_paths(names: list[str]) -> None:
    for name in names:
        normalized = name.replace("\\", "/")
        if normalized.startswith("/") or ".." in normalized.split("/"):
            _fail(f"unsafe ZIP entry path: {name!r}")
        if ":" in normalized and normalized[1:2] == ":":
            _fail(f"absolute path in ZIP: {name!r}")


def main() -> int:
    if not VENDOR_SOURCE.is_file():
        _fail(f"vendored runtime missing: {VENDOR_SOURCE}")

    config = ShowcaseConfig(
        title="ZIP Smoke Showcase",
        projects=[
            ShowcaseProject(
                id="safe",
                title="Безопасный проект",
                description="Обычное описание.",
                demo_url="https://aistudio.google.com/",
                landing_url="/landings/safe",
            ),
            ShowcaseProject(
                id="malicious",
                title="<script>alert('xss')</script>",
                description="bad",
                demo_url="javascript:alert(1)",
                landing_url="data:text/html,<script>alert(2)</script>",
            ),
        ],
    )

    result = build_showcase_zip_with_meta(config)
    if not result.data:
        _fail("ZIP data is empty")

    with zipfile.ZipFile(io.BytesIO(result.data)) as archive:
        names = archive.namelist()
        _assert_no_unsafe_zip_paths(names)

        required = {ZIP_HTML_NAME, ZIP_AFRAME_ENTRY, ZIP_LICENSE_ENTRY}
        missing = required - set(names)
        if missing:
            _fail(f"ZIP missing entries: {sorted(missing)}")

        html = archive.read(ZIP_HTML_NAME).decode("utf-8")
        runtime = archive.read(ZIP_AFRAME_ENTRY)
        license_text = archive.read(ZIP_LICENSE_ENTRY).decode("utf-8")

    if DEFAULT_AFRAME_SRC not in html:
        _fail(f"HTML must reference local vendor path: {DEFAULT_AFRAME_SRC}")
    if "aframe.io/releases" in html:
        _fail("bundled HTML must not reference A-Frame CDN")
    if "showcase-fallback" not in html:
        _fail("bundled HTML missing 2D fallback section")
    if "<script>alert('xss')</script>" in html:
        _fail("malicious title not escaped in bundled HTML")
    if "javascript:alert(1)" in html:
        _fail("javascript: demo URL leaked into bundled HTML")
    if not runtime:
        _fail("empty A-Frame runtime in ZIP")
    if "MIT" not in license_text:
        _fail("LICENSE.txt missing MIT notice")

    print("SHOWCASE ZIP EXPORT SMOKE PASSED")
    print(f"  zip_bytes={len(result.data)}")
    print(f"  entries={list(result.entries)}")
    print(f"  projects={result.project_count} mode={result.mode}")
    print(f"  warnings={len(result.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
