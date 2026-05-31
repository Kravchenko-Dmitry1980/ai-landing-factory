#!/usr/bin/env python3
"""Offline smoke for the final demo pack (Stage P.8.2).

Validates structure and content markers without dev-server or network.

Usage:
    ..\\.venv\\Scripts\\python.exe scripts\\smoke_demo_pack.py
    ..\\.venv\\Scripts\\python.exe scripts\\smoke_demo_pack.py --dir ..\\demo_release_20260531_1200
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent

INTERACTIVE_ZIP = "01_interactive_wow_landing/ai-wow-landing.zip"
STATIC_HTML = "02_static_wow_landing/wow_landing.html"
SHOWCASE_ZIP = "03_showcase_vr_ar/ai-showcase.zip"
STANDARD_HTML = "04_standard_landing/standard_landing.html"
README = "README_DEMO_RU.md"
REPORT = "CHECKS/DEMO_PACK_REPORT.md"
CHECKLIST = "CHECKS/DEMO_PACK_CHECKLIST.md"

STALE_MARKERS = (
    "PhoneStage",
    "function Assistant",
    "wow-bundle-cat-mascot-v2",
    "wow-hero-mascot-platform",
    "mini-landing",
    "wow-portal",
    "wow-ring",
)
WOW_JS_MARKERS = (
    "cat-assistant",
    "wow-hero-mascot",
    "wow-hero-mascot-rig",
    "wow-bundle-cat-mascot-v3",
)


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def _find_demo_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        path = explicit.resolve()
        if not path.is_dir():
            _fail(f"demo pack directory not found: {path}")
        return path

    candidates = sorted(
        ROOT.glob("demo_release_*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        legacy = ROOT / "demo_release"
        if legacy.is_dir():
            return legacy.resolve()
        _fail("no demo_release_* folder found — run build_demo_pack.ps1 first")
    return candidates[0].resolve()


def _assert_no_absolute_paths(text: str, *, label: str) -> None:
    if re.search(r"[A-Za-z]:\\", text):
        _fail(f"{label} contains Windows absolute path")
    if "localhost:" in text.lower() and "demo links" not in label.lower():
        # Allow mentions in README; block in HTML/JS mandatory runtime
        if label.endswith((".html", ".js", "ZIP index")):
            _fail(f"{label} references localhost for mandatory runtime")


def _check_interactive_zip(base: Path) -> None:
    path = base / INTERACTIVE_ZIP.replace("/", "\\")
    if not path.is_file():
        _fail(f"missing interactive WOW ZIP: {INTERACTIVE_ZIP}")

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        required = {
            "index.html",
            "assets/wow-app.js",
            "assets/wow/cat-assistant.png",
            "data/landing-contract.json",
        }
        missing = required - names
        if missing:
            _fail(f"interactive ZIP missing: {sorted(missing)}")

        js = zf.read("assets/wow-app.js").decode("utf-8", errors="replace")
        index_html = zf.read("index.html").decode("utf-8", errors="replace")

    for marker in WOW_JS_MARKERS:
        if marker not in js:
            _fail(f"wow-app.js missing marker: {marker!r}")
    for stale in STALE_MARKERS:
        if stale in js:
            _fail(f"wow-app.js contains stale marker: {stale!r}")

    _assert_no_absolute_paths(index_html, label="ZIP index.html")
    _assert_no_absolute_paths(js, label="wow-app.js")
    print("PASS: interactive WOW ZIP structure and markers")


def _check_showcase_zip(base: Path) -> None:
    path = base / SHOWCASE_ZIP.replace("/", "\\")
    if not path.is_file():
        _fail(f"missing showcase ZIP: {SHOWCASE_ZIP}")

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        required = {
            "showcase.html",
            "vendor/aframe/aframe.min.js",
            "vendor/aframe/LICENSE.txt",
        }
        missing = required - names
        if missing:
            _fail(f"showcase ZIP missing: {sorted(missing)}")
        html = zf.read("showcase.html").decode("utf-8", errors="replace")
        runtime = zf.read("vendor/aframe/aframe.min.js")

    if not runtime:
        _fail("empty A-Frame runtime in showcase ZIP")
    if "aframe.io/releases" in html:
        _fail("showcase.html references A-Frame CDN")
    if "showcase-fallback" not in html:
        _fail("showcase.html missing 2D fallback")
    _assert_no_absolute_paths(html, label="showcase.html")
    print("PASS: showcase ZIP structure and vendor")


def _check_static_wow(base: Path) -> None:
    path = base / STATIC_HTML.replace("/", "\\")
    if not path.is_file():
        _fail(f"missing static WOW HTML: {STATIC_HTML}")

    html = path.read_text(encoding="utf-8")
    if "wow-hero-mascot" not in html:
        _fail("static WOW HTML missing wow-hero-mascot")
    if "cat-assistant" not in html and "data:image/png;base64," not in html:
        _fail("static WOW HTML missing cat mascot asset")
    for stale in ("mini-landing", "PhoneStage", "function Assistant"):
        if stale in html:
            _fail(f"static WOW HTML contains stale marker: {stale!r}")
    if "wow-hero-mascot-platform" in html:
        _fail("static WOW HTML still has opaque platform layer")
    _assert_no_absolute_paths(html, label=STATIC_HTML)
    print("PASS: static WOW HTML")


def _check_standard(base: Path) -> None:
    path = base / STANDARD_HTML.replace("/", "\\")
    if not path.is_file():
        _fail(f"missing standard HTML: {STANDARD_HTML}")

    html = path.read_text(encoding="utf-8")
    for token in ("wow-landing", "wow-cockpit", "wow-app.js", "data-export-mode=\"wow\""):
        if token in html:
            _fail(f"standard HTML contains WOW dependency: {token!r}")
    _assert_no_absolute_paths(html, label=STANDARD_HTML)
    print("PASS: standard landing HTML")


def _update_report_verdict(base: Path, *, verdict: str, smoke_lines: list[str]) -> None:
    report_path = base / REPORT.replace("/", "\\")
    if not report_path.is_file():
        return
    text = report_path.read_text(encoding="utf-8")
    smoke_block = "\n".join(f"- {line}" for line in smoke_lines)
    replacement = (
        f"## Final verdict\n\n"
        f"**{verdict}**\n\n"
        f"### Demo pack smoke\n\n{smoke_block}\n"
    )
    if "## Final verdict" in text:
        text = re.sub(
            r"## Final verdict\n\n.*",
            replacement.rstrip() + "\n",
            text,
            flags=re.DOTALL,
        )
    else:
        text += f"\n{replacement}"
    report_path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test demo pack (P.8.2)")
    parser.add_argument("--dir", type=Path, default=None, help="Demo pack directory")
    args = parser.parse_args()

    base = _find_demo_dir(args.dir)
    print(f"Checking demo pack: {base}")

    for rel in (README, CHECKLIST, REPORT):
        if not (base / rel.replace("/", "\\")).is_file():
            _fail(f"missing required file: {rel}")

    smoke_lines: list[str] = []
    checks = [
        ("README", lambda: None),
        ("interactive ZIP", _check_interactive_zip),
        ("showcase ZIP", _check_showcase_zip),
        ("static WOW", _check_static_wow),
        ("standard HTML", _check_standard),
    ]

    for name, fn in checks:
        if name == "README":
            print("PASS: README_DEMO_RU.md exists")
            smoke_lines.append(f"{name}: PASS")
            continue
        try:
            fn(base)
            smoke_lines.append(f"{name}: PASS")
        except SystemExit:
            raise
        except Exception as exc:
            _fail(f"{name}: {exc}")

    if not (base / REPORT.replace("/", "\\")).is_file():
        _fail("DEMO_PACK_REPORT.md not created")

    _update_report_verdict(base, verdict="PASS", smoke_lines=smoke_lines)
    print("PASS: demo pack smoke")
    print(f"DEMO_PACK_DIR={base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
