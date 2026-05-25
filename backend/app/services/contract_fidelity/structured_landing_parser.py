"""Section-oriented parser for pre-structured Russian project landing documents."""

from __future__ import annotations

import re

from app.schemas.fidelity import ParsedStructuredLanding
from app.services.contract_fidelity.module_parser import parse_modules
from app.services.contract_fidelity.stack_parser import parse_stack_section
from app.services.contract_fidelity.team_parser import parse_team_section

SECTION_DEFINITIONS: list[tuple[str, list[str]]] = [
    ("essence", ["Суть проекта", "Описание проекта"]),
    ("tasks", ["Задачи проекта", "Задачи"]),
    ("purpose", ["Для чего", "Цель проекта", "Цели проекта"]),
    ("inputs", ["Вводные данные", "Исходные данные"]),
    ("outputs", ["Выходные данные", "Результирующие данные"]),
    ("results", ["Результаты проекта", "Результаты"]),
    ("outlook", ["Перспектива развития", "Roadmap", "Дальнейшее развитие"]),
    ("tech_stack", [
        "Используемый технологический стек",
        "Технологический стек",
        "Стек",
    ]),
    ("team", ["Участники команды проекта", "Команда проекта"]),
    ("tagline", ["Фраза проекта"]),
]

TITLE_TO_KEY: dict[str, str] = {
    title.lower(): key for key, titles in SECTION_DEFINITIONS for title in titles
}

BULLET_RE = re.compile(r"^[\s]*(?:[-•*·]|–)\s+(.+)$", re.MULTILINE)

METADATA_PATTERNS: dict[str, re.Pattern[str]] = {
    "client": re.compile(
        r"Заказчик\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE | re.MULTILINE
    ),
    "timeline": re.compile(
        r"Период\s+реализации\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE | re.MULTILINE
    ),
    "lead": re.compile(r"Тимлид\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE | re.MULTILINE),
}


class StructuredLandingParser:
    """Parse known landing section headers into structured contract fields."""

    def parse(self, text: str) -> ParsedStructuredLanding:
        text = text.replace("\u00a0", " ").replace("\r\n", "\n")
        sections = _split_sections(text)
        metadata = _parse_metadata(text)

        title = _parse_title(text)
        essence_text = sections.get("essence", "")
        modules = parse_modules(essence_text)

        stack_text = sections.get("tech_stack", "")
        stack_grouped = parse_stack_section(stack_text)

        team_text = sections.get("team", "")
        team = parse_team_section(team_text)

        section_lengths = {k: len(v) for k, v in sections.items()}

        return ParsedStructuredLanding(
            title=title,
            client=metadata.get("client"),
            timeline=metadata.get("timeline"),
            lead=metadata.get("lead"),
            essence=essence_text.strip(),
            tasks=_parse_bullets(sections.get("tasks", "")),
            purpose=_parse_bullets(sections.get("purpose", "")),
            inputs=_parse_bullets(sections.get("inputs", "")),
            outputs=_parse_bullets(sections.get("outputs", "")),
            results=_parse_bullets(sections.get("results", "")),
            outlook=_parse_bullets(sections.get("outlook", "")),
            tech_stack_grouped=stack_grouped,
            team=team,
            modules=modules,
            tagline=sections.get("tagline", "").strip() or title,
            section_lengths=section_lengths,
        )


def _split_sections(text: str) -> dict[str, str]:
    """Split document by known section headers (longest title match first)."""
    all_titles = sorted(
        (title, key) for key, titles in SECTION_DEFINITIONS for title in titles
    )
    all_titles.sort(key=lambda x: len(x[0]), reverse=True)

    header_positions: list[tuple[int, int, str, str]] = []
    for title, key in all_titles:
        pattern = re.compile(
            rf"(?:^|\n)\s*(?:#{{0,3}}\s*)?{re.escape(title)}\s*\n",
            re.IGNORECASE | re.MULTILINE,
        )
        for match in pattern.finditer(text):
            header_positions.append((match.start(), match.end(), key, title))

    header_positions.sort(key=lambda x: x[0])

    seen_starts: set[int] = set()
    unique: list[tuple[int, int, str]] = []
    for start, end, key, _title in header_positions:
        if start in seen_starts:
            continue
        seen_starts.add(start)
        unique.append((start, end, key))

    sections: dict[str, str] = {}
    for i, (_start, end, key) in enumerate(unique):
        body_start = end
        body_end = unique[i + 1][0] if i + 1 < len(unique) else len(text)
        body = text[body_start:body_end].strip()
        if key not in sections or len(body) > len(sections[key]):
            sections[key] = body

    return sections


def _parse_metadata(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, pattern in METADATA_PATTERNS.items():
        match = pattern.search(text)
        if match:
            value = match.group(1).strip()
            if key == "client":
                value = value.split("\n")[0].strip()
            result[key] = value
    return result


def _parse_title(text: str) -> str | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    first = lines[0]
    if re.match(r"^заказчик\s*:", first, re.IGNORECASE):
        return None
    if len(first) < 120 and not first.endswith(":"):
        return first
    return None


def _parse_bullets(section_text: str) -> list[str]:
    if not section_text.strip():
        return []

    bullets = BULLET_RE.findall(section_text)
    if bullets:
        seen: set[str] = set()
        out: list[str] = []
        for item in bullets:
            line = item.strip()
            if line and line not in seen:
                seen.add(line)
                out.append(line)
        return out

    lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]
    return lines
