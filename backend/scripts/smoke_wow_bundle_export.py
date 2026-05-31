"""Offline smoke for the Interactive WOW Bundle export (Stage P.7.2).

Builds a ZIP from a synthetic Indlab-like contract using the real frontend build
and verifies the bundle is portable and complete:

  - dist-wow assets are present (else a clear build instruction);
  - ZIP contains index.html, assets/wow-app.js, assets/wow/cat-assistant.png, data JSON, README;
  - wow-app.js embeds cat mascot build markers (rejects stale robot bundles);
  - index.html embeds the wow-data JSON and references no external CDN;
  - bundle data has >= 4 metrics and a pipeline.

Run (Windows PowerShell, from backend/):
    ..\\.venv\\Scripts\\python.exe scripts\\smoke_wow_bundle_export.py
"""

from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.services.export import wow_bundle_exporter  # noqa: E402
from app.services.export.wow_bundle_exporter import (  # noqa: E402
    build_wow_bundle_zip_with_meta,
    validate_cat_mascot_png,
)
from tests.fixtures.export_contract_fixture import make_wow_indlab_fixture  # noqa: E402

BUILD_INSTRUCTION = "cd frontend && npm run build:wow-bundle"

FORBIDDEN_ASSET_PARTS = (
    "landing-preview",
    "screenshot",
    "hero-preview",
    "mockup",
)


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def main() -> None:
    assets_dir = wow_bundle_exporter.DEFAULT_ASSETS_DIR
    js_path = assets_dir / "wow-app.js"
    if not js_path.is_file():
        _fail(
            f"frontend WOW bundle not built ({js_path} missing). "
            f"Build it first: {BUILD_INSTRUCTION}"
        )

    _, contract, _ = make_wow_indlab_fixture()
    result = build_wow_bundle_zip_with_meta(contract)
    names = set(zipfile.ZipFile(io.BytesIO(result.data)).namelist())

    required = {
        "index.html",
        "assets/wow-app.js",
        "assets/wow/cat-assistant.png",
        "data/landing-contract.json",
        "README_DEMO.txt",
    }
    missing = required - names
    if missing:
        _fail(f"ZIP missing entries: {sorted(missing)}")

    with zipfile.ZipFile(io.BytesIO(result.data)) as zf:
        index_html = zf.read("index.html").decode("utf-8")
        payload = json.loads(zf.read("data/landing-contract.json").decode("utf-8"))
        js = zf.read("assets/wow-app.js").decode("utf-8")
        cat_png = zf.read("assets/wow/cat-assistant.png")

    for marker in ("cat-assistant", "wow-hero-mascot", "wow-hero-mascot-rig", "wow-bundle-cat-mascot-v2"):
        if marker not in js:
            _fail(f"wow-app.js missing cat mascot marker: {marker!r}")
    if "PhoneStage" in js or "function Assistant" in js:
        _fail("wow-app.js still contains stale robot scene markers")
    if "wow-hero-mascot-image" not in js and "wow-hero-mascot-img" not in js:
        _fail("wow-app.js missing wow-hero-mascot-image marker")
    try:
        validate_cat_mascot_png(cat_png)
    except ValueError as exc:
        _fail(str(exc))

    for name in names:
        lowered = name.lower()
        if lowered == "assets/wow/cat-assistant.png":
            continue
        for part in FORBIDDEN_ASSET_PARTS:
            if part in lowered:
                _fail(f"ZIP contains forbidden preview/mockup asset: {name!r}")

    if 'id="wow-data"' not in index_html:
        _fail("index.html does not embed the wow-data JSON")
    if re.search(r'(?:src|href)=["\']https?://', index_html) or "cdn" in index_html.lower():
        _fail("index.html references an external CDN")

    for name in names:
        normalized = name.replace("\\", "/")
        if normalized.startswith("/") or ".." in normalized.split("/"):
            _fail(f"unsafe ZIP entry path: {name!r}")

    if len(payload["metrics"]) < 4:
        _fail(f"expected >= 4 metrics, got {len(payload['metrics'])}")
    if not payload["pipeline"]:
        _fail("bundle data has no pipeline")

    print("PASS: interactive WOW bundle export")
    print("PASS: cat mascot included")
    print(f"  entries: {sorted(names)}")
    print(f"  metrics: {result.metric_count}, pipeline: {result.pipeline_count}, css: {result.has_css}")
    print(f"  zip size: {len(result.data) // 1024} KB")


if __name__ == "__main__":
    main()
