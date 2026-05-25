"""OCR messy team text parsing."""

from __future__ import annotations

from app.services.evidence.group_team_parser import parse_team_section_group_aware
from app.services.evidence.people_extractor import extract_people_from_text


OCR_TEAM_TEXT = """
Slide 25:
Команда проекта
Тимлид: Кравченко Дмитрий
Помощник тимлида: Смирнова Анна
Участники: Иванов Иван, Петров Петр
"""


def test_ocr_team_block_parsed() -> None:
    members = extract_people_from_text(
        OCR_TEAM_TEXT,
        source_ref="deck.pptx#ocr-slide-25",
        in_team_section=True,
    )
    names = {m.name for m in members}
    assert "Кравченко Дмитрий" in names
    assert len(names) >= 2


def test_group_line_ocr_text_distributed() -> None:
    text = (
        "Команда проекта\n"
        "Участники: Иванов Иван, Петров Петр, Сидорова Мария — разработка модулей"
    )
    blocks = parse_team_section_group_aware(text)
    assert blocks
    members = extract_people_from_text(text, in_team_section=True)
    assert len(members) >= 3
