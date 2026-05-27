#!/usr/bin/env python3
"""Smoke test: university_platform HTML export quality gate."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass

import httpx

DEFAULT_PROJECT_ID = "55a98f90-73fc-4d26-a477-3c974a0cbeed"
DEFAULT_BACKEND_URL = "http://127.0.0.1:8001"

REQUIRED_CONTENT = (
    "Эндокринология+",
    "GlaucoLogic",
    "Copilot врача",
    "VitaCalc",
    "Используемый технологический стек",
    "Команда проекта",
    "team-card",
    "stack-tag",
    "max-width: 1200px",
)

LIGHT_BG_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"--alf-bg\s*:\s*#(?:fff(?:fff)?|ffffff)\b", re.I),
    re.compile(r"--bg\s*:\s*#(?:fff(?:fff)?|ffffff)\b", re.I),
    re.compile(r"--bg\s*:\s*var\s*\(\s*--alf-bg\s*\)", re.I),
    re.compile(r"background(?:-color)?\s*:\s*#(?:fff(?:fff)?|ffffff)\b", re.I),
    re.compile(r"background(?:-color)?\s*:\s*white\b", re.I),
    re.compile(r"#ffffff\b", re.I),
)

PURPLE_ACCENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"#7[Cc]3[Aa][Ee][Dd]\b"),
    re.compile(r"#8[Bb]5[Cc][Ff]6\b"),
    re.compile(r"--alf-accent\s*:\s*#(?:7[Cc]3[Aa][Ee][Dd]|8[Bb]5[Cc][Ff]6)\b"),
    re.compile(r"--accent\s*:\s*#(?:7[Cc]3[Aa][Ee][Dd]|8[Bb]5[Cc][Ff]6)\b"),
)

DARK_TEXT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"#111111\b"),
    re.compile(r"#0[Bb]1220\b"),
    re.compile(r"--alf-text\s*:\s*#(?:111111|0[Bb]1220)\b"),
    re.compile(r"--text\s*:\s*#(?:111111|0[Bb]1220)\b"),
    re.compile(r"--text\s*:\s*var\s*\(\s*--alf-text\s*\)", re.I),
)

SECTION_SEPARATOR_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"border-bottom\s*:\s*[^;]+", re.I),
    re.compile(r"border-bottom\s*:\s*1px", re.I),
    re.compile(r"border-bottom\s*:\s*2px", re.I),
)

DARK_FORBIDDEN_STRINGS = (
    "--bg: #0f1419",
    "--bg:#0f1419",
    "--surface: #1a2332",
    "--surface:#1a2332",
)

DARK_BG_VAR_PATTERN = re.compile(
    r"--bg\s*:\s*#(?:0[Ff]1419|1[Aa]2332|0[Bb]1220|111827)\b"
)
LEGACY_MAX_WIDTH_PATTERN = re.compile(r"max-width\s*:\s*720px", re.I)
DARK_BG_WITH_VAR_PATTERN = re.compile(
    r"background\s*:\s*var\s*\(\s*--bg\s*\)", re.I
)


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    label: str

    @property
    def prefix(self) -> str:
        return "OK" if self.ok else "FAIL"


def _any_match(patterns: tuple[re.Pattern[str], ...], html: str) -> bool:
    return any(p.search(html) for p in patterns)


def check_required_content(html: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    for token in REQUIRED_CONTENT:
        ok = token in html
        label = f"contains {token!r}" if ok else f"missing required content {token!r}"
        results.append(CheckResult(ok=ok, label=label))
    return results


def check_university_style_markers(html: str) -> list[CheckResult]:
    checks = (
        ("light background marker (#ffffff / --alf-bg / --bg alias)", _any_match(LIGHT_BG_PATTERNS, html)),
        (
            "purple accent marker (#7C3AED / --alf-accent)",
            _any_match(PURPLE_ACCENT_PATTERNS, html),
        ),
        ("dark text marker (#111111 / --alf-text)", _any_match(DARK_TEXT_PATTERNS, html)),
        (
            "section border-bottom / separator marker",
            _any_match(SECTION_SEPARATOR_PATTERNS, html),
        ),
    )
    return [CheckResult(ok=ok, label=label) for label, ok in checks]


def check_no_dark_enterprise_markers(html: str) -> list[CheckResult]:
    results: list[CheckResult] = []

    for token in DARK_FORBIDDEN_STRINGS:
        ok = token not in html
        label = (
            f"no dark token {token!r}"
            if ok
            else f"dark enterprise marker present: {token!r}"
        )
        results.append(CheckResult(ok=ok, label=label))

    has_dark_bg_var = bool(DARK_BG_VAR_PATTERN.search(html))
    results.append(
        CheckResult(
            ok=not has_dark_bg_var,
            label=(
                "no dark --bg CSS variable"
                if not has_dark_bg_var
                else "dark --bg CSS variable detected (enterprise theme)"
            ),
        )
    )

    has_var_bg = bool(DARK_BG_WITH_VAR_PATTERN.search(html))
    has_light_bg = _any_match(LIGHT_BG_PATTERNS, html)
    if has_var_bg and not has_light_bg:
        results.append(
            CheckResult(
                ok=False,
                label="background: var(--bg) without light university background",
            )
        )
    else:
        results.append(
            CheckResult(
                ok=True,
                label="no dark background: var(--bg) pattern",
            )
        )

    legacy_match = LEGACY_MAX_WIDTH_PATTERN.search(html)
    results.append(
        CheckResult(
            ok=legacy_match is None,
            label=(
                "no legacy max-width: 720px fallback"
                if legacy_match is None
                else "legacy max-width: 720px fallback detected"
            ),
        )
    )

    has_project_landing_fallback = "Project Landing" in html
    results.append(
        CheckResult(
            ok=not has_project_landing_fallback,
            label=(
                "no Project Landing title fallback"
                if not has_project_landing_fallback
                else 'title fallback "Project Landing" detected'
            ),
        )
    )

    return results


def validate_university_export_html(html: str) -> list[CheckResult]:
    """Run all HTML checks for university_platform export."""
    return [
        *check_required_content(html),
        *check_university_style_markers(html),
        *check_no_dark_enterprise_markers(html),
    ]


def fetch_export_html(project_id: str, backend_url: str) -> tuple[int, str]:
    base = backend_url.rstrip("/")
    url = f"{base}/api/v1/projects/{project_id}/export/html"
    with httpx.Client(timeout=60.0, trust_env=False) as client:
        response = client.get(url, params={"theme": "university_platform"})
    return response.status_code, response.text


def parse_html_payload(response_text: str, status_code: int) -> str:
    if status_code != 200:
        return ""
    try:
        import json

        payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"export response is not JSON: {exc}") from exc
    html = payload.get("html")
    if not isinstance(html, str):
        raise RuntimeError("export response missing string field 'html'")
    return html


def run_smoke(project_id: str, backend_url: str) -> int:
    print(f"University export smoke — project_id={project_id}")
    print(f"Backend: {backend_url}")
    print(f"GET /api/v1/projects/{project_id}/export/html?theme=university_platform\n")

    try:
        status_code, response_text = fetch_export_html(project_id, backend_url)
    except httpx.HTTPError as exc:
        print(f"FAIL: HTTP request failed — {exc}", file=sys.stderr)
        return 1

    http_ok = status_code == 200
    print(f"{'OK' if http_ok else 'FAIL'}: HTTP status {status_code}")
    if not http_ok:
        preview = response_text[:300].replace("\n", " ")
        print(f"FAIL: response body preview: {preview!r}", file=sys.stderr)
        return 1

    try:
        html = parse_html_payload(response_text, status_code)
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    results = validate_university_export_html(html)
    failed = 0
    for result in results:
        print(f"{result.prefix}: {result.label}")
        if not result.ok:
            failed += 1

    print()
    if failed:
        print(
            f"=== UNIVERSITY EXPORT SMOKE FAILED ({failed} check(s)) ===",
            file=sys.stderr,
        )
        print(
            "Hint: exporter may not support theme=university_platform yet "
            "(dark enterprise CSS is expected to FAIL).",
            file=sys.stderr,
        )
        return 1

    print("=== UNIVERSITY EXPORT SMOKE PASSED ===")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test university_platform HTML export via API",
    )
    parser.add_argument(
        "--project-id",
        default=DEFAULT_PROJECT_ID,
        help=f"Project UUID (default: {DEFAULT_PROJECT_ID})",
    )
    parser.add_argument(
        "--backend-url",
        default=DEFAULT_BACKEND_URL,
        help=f"Backend base URL without /api/v1 (default: {DEFAULT_BACKEND_URL})",
    )
    args = parser.parse_args()
    return run_smoke(args.project_id, args.backend_url)


if __name__ == "__main__":
    raise SystemExit(main())
