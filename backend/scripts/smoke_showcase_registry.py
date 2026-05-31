#!/usr/bin/env python3
"""Stage P.6 smoke: showcase registry CRUD + export from saved showcase.

Usage:
    cd C:\\Dima\\Projects\\CURSOR\\_uat\\ai-landing-factory-fresh\\backend
    ..\\.venv\\Scripts\\python.exe scripts\\smoke_showcase_registry.py

Flow (uses an isolated temp storage dir; cleans up after itself):
    1. create showcase;
    2. add 3 projects (incl. an unsafe URL that must be sanitized);
    3. export HTML from the saved showcase;
    4. export ZIP from the saved showcase;
    5. verify ZIP entries;
    6. delete showcase;
    7. PASS.

No network and no running backend server required.
"""

from __future__ import annotations

import io
import sys
import tempfile
import zipfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter
from app.services.showcase.showcase_registry import ShowcaseRegistry
from app.services.showcase.showcase_schema import (
    ShowcaseCreateRequest,
    ShowcaseProjectCreateRequest,
)
from app.services.showcase.showcase_vendor import (
    VENDOR_SOURCE,
    ZIP_AFRAME_ENTRY,
    ZIP_HTML_NAME,
    ZIP_LICENSE_ENTRY,
)
from app.services.showcase.showcase_zip_exporter import build_showcase_zip_with_meta


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="showcase_smoke_") as tmp:
        registry = ShowcaseRegistry(base_dir=Path(tmp) / "showcases")

        # 1. create
        config = registry.create_showcase(
            ShowcaseCreateRequest(title="Витрина AI-проектов УИИ")
        )
        sid = config.id
        if not sid:
            _fail("created showcase has no id")

        # 2. add 3 projects
        registry.add_project(
            sid,
            ShowcaseProjectCreateRequest(
                title="Эндокринология+",
                demo_url="https://aistudio.google.com/",
                landing_url="/preview/endo",
                tags=["health", "ai"],
            ),
        )
        registry.add_project(
            sid,
            ShowcaseProjectCreateRequest(
                title="Второй проект",
                description="Демо-стенд.",
            ),
        )
        config = registry.add_project(
            sid,
            ShowcaseProjectCreateRequest(
                title="Небезопасный",
                demo_url="javascript:alert(1)",  # must be sanitized to None
            ),
        )
        if len(config.projects) != 3:
            _fail(f"expected 3 projects, got {len(config.projects)}")
        unsafe = next(p for p in config.projects if p.title == "Небезопасный")
        if unsafe.demo_url is not None:
            _fail("unsafe demo_url was not sanitized to None")

        saved = registry.get_showcase(sid)

        # 3. export HTML
        html_result = ShowcaseHtmlExporter().export(saved)
        if not html_result.html.startswith("<!DOCTYPE html>"):
            _fail("exported HTML is not a valid document")
        if html_result.project_count != 3:
            _fail("export HTML project_count mismatch")
        if "Эндокринология+" not in html_result.html:
            _fail("project title missing from exported HTML")
        if "javascript:alert(1)" in html_result.html:
            _fail("unsafe URL leaked into exported HTML")

        # 4 + 5. export ZIP and verify entries
        if VENDOR_SOURCE.is_file():
            zip_result = build_showcase_zip_with_meta(saved)
            with zipfile.ZipFile(io.BytesIO(zip_result.data)) as archive:
                names = set(archive.namelist())
            required = {ZIP_HTML_NAME, ZIP_AFRAME_ENTRY, ZIP_LICENSE_ENTRY}
            missing = required - names
            if missing:
                _fail(f"ZIP missing entries: {sorted(missing)}")
            zip_note = f"zip_bytes={len(zip_result.data)} entries={sorted(names)}"
        else:
            zip_note = "zip skipped (vendored A-Frame runtime missing)"

        # 6. delete
        if not registry.delete_showcase(sid):
            _fail("delete_showcase returned False")
        if registry.list_summaries():
            _fail("registry not empty after delete")

    # 7. PASS
    print("SHOWCASE REGISTRY SMOKE PASSED")
    print(f"  showcase_id={sid}")
    print(f"  html_bytes={len(html_result.html)} projects={html_result.project_count}")
    print(f"  {zip_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
