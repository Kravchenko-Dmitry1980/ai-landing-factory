#!/usr/bin/env python3
"""Optional P.5 smoke: showcase export works offline and is injection-safe.

Usage:
    cd C:\\Dima\\Projects\\CURSOR\\_uat\\ai-landing-factory-fresh\\backend
    ..\\.venv\\Scripts\\python.exe scripts\\smoke_showcase_export.py

Checks (no network, no backend server required):
    * exporter produces an <a-scene> and a 2D fallback section;
    * project card count matches input;
    * a malicious <script> title is escaped (not executable);
    * a javascript: URL is rejected (absent from output).
"""

from __future__ import annotations

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


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
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

    print("SHOWCASE EXPORT SMOKE PASSED")
    print(f"  projects={result.project_count} mode={result.mode}")
    print(f"  html_bytes={len(html)}")
    print(f"  warnings={len(result.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
