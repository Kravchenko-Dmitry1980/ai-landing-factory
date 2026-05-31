#!/usr/bin/env python3
"""Optional P.5 smoke: showcase export works offline and is injection-safe.

Usage:
    cd C:\\Dima\\Projects\\CURSOR\\_uat\\ai-landing-factory-fresh\\backend
    ..\\.venv\\Scripts\\python.exe scripts\\smoke_showcase_export.py

Checks (no network, no backend server required):
    * exporter produces an <a-scene> and a 2D fallback section;
    * default export uses local vendored A-Frame path (no CDN);
    * export_showcase_demo copies vendor asset next to HTML;
    * CDN override references allowlisted A-Frame URL;
    * malicious aframe_src rejected;
    * malicious title / javascript: demo URL handled safely.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter
from app.services.showcase.showcase_schema import (
    ShowcaseConfig,
    ShowcaseProject,
)
from app.services.showcase.showcase_vendor import (
    ALLOWED_AFRAME_CDN,
    DEFAULT_AFRAME_SRC,
    VENDOR_SOURCE,
)

DEMO_HTML = BACKEND / "data" / "exports" / "showcase_demo.html"
DEMO_VENDOR = BACKEND / "data" / "exports" / "vendor" / "aframe" / "aframe.min.js"


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    if not VENDOR_SOURCE.is_file():
        _fail(f"vendored runtime missing in repo: {VENDOR_SOURCE}")

    config = ShowcaseConfig(
        title="Smoke Showcase",
        projects=[
            ShowcaseProject(
                id="safe",
                title="Безопасный проект",
                description="Обычное описание.",
                demo_url="https://aistudio.google.com/",
                landing_url="/landings/safe",
                category="Demo",
                tags=["one", "two"],
            ),
            ShowcaseProject(
                id="malicious",
                title="<script>alert('xss')</script>",
                description="<img src=x onerror=alert(1)>",
                demo_url="javascript:alert(1)",
                landing_url="data:text/html,<script>alert(2)</script>",
            ),
        ],
    )

    result = ShowcaseHtmlExporter().export(config)
    html = result.html

    if "<a-scene" not in html:
        _fail("missing <a-scene> in output")
    if "showcase-fallback" not in html:
        _fail("missing 2D fallback section")
    if result.project_count != 2:
        _fail(f"project_count mismatch: {result.project_count}")

    if DEFAULT_AFRAME_SRC not in html:
        _fail(f"default HTML must reference local vendor path: {DEFAULT_AFRAME_SRC}")
    if "aframe.io/releases" in html:
        _fail("default HTML must not reference A-Frame CDN")
    if "<!-- A-Frame runtime: local vendored -->" not in html:
        _fail("missing local vendored runtime comment")

    if "<script>alert('xss')</script>" in html:
        _fail("malicious title was not escaped")
    if "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" not in html:
        _fail("escaped title marker not found")

    if "javascript:alert(1)" in html:
        _fail("javascript: URL leaked into output")
    if "data:text/html" in html:
        _fail("data: URL leaked into output")

    if not any("demo_url rejected" in w for w in result.warnings):
        _fail("expected warning for rejected demo_url")

    cdn_result = ShowcaseHtmlExporter(aframe_src=ALLOWED_AFRAME_CDN).export(config)
    if ALLOWED_AFRAME_CDN not in cdn_result.html:
        _fail("CDN override must reference allowlisted A-Frame URL")
    if "<!-- A-Frame runtime: CDN override -->" not in cdn_result.html:
        _fail("missing CDN override runtime comment")

    bad_exporter = ShowcaseHtmlExporter(aframe_src="javascript:alert(1)")
    bad_result = bad_exporter.export(config)
    if bad_exporter._aframe_src != DEFAULT_AFRAME_SRC:
        _fail("malicious aframe_src must fall back to default")
    if not any("aframe_src rejected" in w for w in bad_result.warnings):
        _fail("expected warning for rejected aframe_src")

    ext_exporter = ShowcaseHtmlExporter(aframe_src="https://evil.example/aframe.min.js")
    ext_result = ext_exporter.export(config)
    if ext_exporter._aframe_src != DEFAULT_AFRAME_SRC:
        _fail("arbitrary external aframe_src must fall back to default")
    if not any("aframe_src rejected" in w for w in ext_result.warnings):
        _fail("expected warning for non-allowlisted external aframe_src")

    demo_script = BACKEND / "scripts" / "export_showcase_demo.py"
    code = subprocess.run(
        [sys.executable, str(demo_script)],
        cwd=str(BACKEND),
        capture_output=True,
        text=True,
    )
    if code.returncode != 0:
        _fail(f"export_showcase_demo failed: {code.stderr or code.stdout}")

    if not DEMO_HTML.is_file():
        _fail(f"demo HTML missing: {DEMO_HTML}")
    if not DEMO_VENDOR.is_file():
        _fail(f"demo vendor runtime missing: {DEMO_VENDOR}")

    demo_html = DEMO_HTML.read_text(encoding="utf-8")
    if DEFAULT_AFRAME_SRC not in demo_html:
        _fail("demo HTML must reference local vendor path")
    if "aframe.io/releases" in demo_html:
        _fail("demo HTML must not reference CDN by default")
    if "showcase-fallback" not in demo_html:
        _fail("demo HTML missing fallback section")

    print("SHOWCASE EXPORT SMOKE PASSED")
    print(f"  projects={result.project_count} mode={result.mode}")
    print(f"  html_bytes={len(html)}")
    print(f"  vendor_source={VENDOR_SOURCE}")
    print(f"  demo_vendor={DEMO_VENDOR}")
    print(f"  warnings={len(result.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
