#!/usr/bin/env python3
"""Smoke test: public university_platform HTML export polish (names preserved)."""

from __future__ import annotations

import argparse
import re
import sys

import httpx

DEFAULT_PROJECT_ID = "55a98f90-73fc-4d26-a477-3c974a0cbeed"
DEFAULT_BACKEND_URL = "http://127.0.0.1:8001"

REQUIRED_CONTENT = (
    "Эндокринология+",
    "GlaucoLogic",
    "Copilot врача",
    "VitaCalc",
    "Команда проекта",
    "Используемый технологический стек",
    "theme-university_platform",
    "--bg: #ffffff",
    "--accent: #7C3AED",
)

TEAM_NAMES = (
    "Кравченко Дмитрий",
    "Малицкий Андрей",
    "Беляев Борис Олегович",
)

DARK_FORBIDDEN = (
    "--bg: #0f1419",
    "--surface: #1a2332",
    "theme-enterprise_dark",
)

DUPLICATE_BULLETS = (
    "\u25cf \u25cf",  # ● ●
    "\u2022 \u2022",  # • •
)

BROKEN_ENDINGS = (
    " взаимодействие с</li>",
    " указанием для</li>",
    " с</li>",
    " для</li>",
    " по</li>",
    " и</li>",
)

WRONG_MORE_GRAMMAR = (
    "+ ещё 1 пунктов",
    "+ ещё 2 пунктов",
    "+ ещё 3 пунктов",
    "+ ещё 4 пунктов",
)

TAGLINE_DUPLICATE_PATTERN = re.compile(
    r"<h1>Эндокринология\+</h1>.*?<p class='tagline'>Эндокринология\+</p>",
    re.S,
)


def run_checks(html: str) -> tuple[list[str], list[str]]:
    ok: list[str] = []
    fail: list[str] = []

    def check(condition: bool, label: str) -> None:
        (ok if condition else fail).append(label)

    for token in REQUIRED_CONTENT:
        check(token in html, f"contains {token!r}")

    for name in TEAM_NAMES:
        check(name in html, f"contains team name {name!r}")

    for token in DARK_FORBIDDEN:
        check(token not in html, f"no dark marker {token!r}")

    for token in DUPLICATE_BULLETS:
        check(token not in html, "no duplicate bullet glyphs")

    for token in BROKEN_ENDINGS:
        check(token not in html, f"no broken ending {token!r}")

    for token in WRONG_MORE_GRAMMAR:
        check(token not in html, f"no wrong grammar {token!r}")

    check(not TAGLINE_DUPLICATE_PATTERN.search(html), "tagline does not duplicate title")
    check(
        "AI-экосистема для клинической аналитики" in html,
        "medical tagline fallback present",
    )

    return ok, fail


def main() -> int:
    parser = argparse.ArgumentParser(description="Public university export polish smoke")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    args = parser.parse_args()

    base = args.backend_url.rstrip("/")
    url = f"{base}/api/v1/projects/{args.project_id}/export/html"
    print(f"Public export polish smoke — project_id={args.project_id}")
    print(f"Backend: {base}")
    print(f"GET {url}?theme=university_platform\n")

    try:
        with httpx.Client(timeout=30.0, trust_env=False) as client:
            response = client.get(url, params={"theme": "university_platform"})
    except httpx.HTTPError as exc:
        print(f"FAIL: HTTP request error: {exc}")
        return 1

    if response.status_code != 200:
        print(f"FAIL: HTTP status {response.status_code}")
        return 1

    html = response.json().get("html", "")
    if not html:
        print("FAIL: empty HTML body")
        return 1

    ok, fail = run_checks(html)
    for label in ok:
        print(f"OK: {label}")
    for label in fail:
        print(f"FAIL: {label}")

    if fail:
        print("\n=== PUBLIC EXPORT POLISH SMOKE FAILED ===")
        return 1

    print("\n=== PUBLIC EXPORT POLISH SMOKE PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
