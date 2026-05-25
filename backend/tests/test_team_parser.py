"""Tests for team_parser."""

from pathlib import Path

from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser
from app.services.contract_fidelity.team_parser import parse_team_section

FIXTURE = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"


def test_team_count() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    sections = _team_section_text(text)
    members = parse_team_section(sections)
    assert len(members) >= 15
    assert any("Кравченко" in m.name for m in members)
    assert any(m.role for m in members)
    assert any(m.contributions for m in members)


def _team_section_text(text: str) -> str:
    parser = StructuredLandingParser()
    sections = parser.parse(text)
    # re-split to get raw team block
    from app.services.contract_fidelity.structured_landing_parser import _split_sections

    raw = _split_sections(text.replace("\u00a0", " ").replace("\r\n", "\n"))
    return raw.get("team", "")
