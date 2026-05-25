#!/usr/bin/env python3
"""Smoke test for group team block parsing (Indlab DOCX)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
INDLAB_DOCX = (
    REPO / "test_corpus" / "golden" / "indlab_telegram_news" / "sources" / "02_landing.docx.txt"
)

sys.path.insert(0, str(BACKEND))

from app.services.contract_fidelity.team_parser import parse_team_section


def main() -> int:
    text = INDLAB_DOCX.read_text(encoding="utf-8")
    start = text.lower().find("команда проекта")
    end = text.lower().find("фраза проекта")
    team = parse_team_section(text[start:end])

    errors: list[str] = []
    forbidden = ("Посты Telegram", "Qdrant Cloud", "Google Colab", "Схема обработки данных")

    targets = ("Быков", "Иванков", "Решетников")
    found = {key: next((m for m in team if key in m.name), None) for key in targets}

    for key, member in found.items():
        if member is None:
            errors.append(f"missing member containing {key}")
            continue
        if not member.role:
            errors.append(f"{member.name}: empty role")
        elif "Парсинг" not in member.role:
            errors.append(f"{member.name}: role={member.role!r}")
        if len(member.contributions) < 3:
            errors.append(f"{member.name}: contributions={len(member.contributions)}")

    for bad in forbidden:
        if any(bad.lower() in m.name.lower() for m in team):
            errors.append(f"forbidden team name: {bad}")

    if errors:
        print("FAIL:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(
        f"OK: group team blocks — "
        f"Быков/Иванков/Решетников role='{found['Быков'].role}', "
        f"contributions={len(found['Быков'].contributions)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
