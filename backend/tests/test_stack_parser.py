"""Tests for stack_parser."""

from pathlib import Path

from app.services.contract_fidelity.stack_parser import parse_stack_section, stack_to_bullets
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser

FIXTURE = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"


def test_stack_categories() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = StructuredLandingParser().parse(text)
    grouped = parsed.tech_stack_grouped
    assert "AI / LLM" in grouped
    assert "OpenAI API" in grouped["AI / LLM"]
    assert "Python" in grouped.get("Backend / API", [])
    assert "React" in grouped.get("Frontend", [])


def test_stack_not_mixed_with_tasks() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = StructuredLandingParser().parse(text)
    task_set = set(parsed.tasks)
    for items in parsed.tech_stack_grouped.values():
        for item in items:
            assert item not in task_set or "pipeline" in item.lower()


def test_stack_to_bullets() -> None:
    grouped = {"AI / LLM": ["OpenAI API", "Qwen"], "Frontend": ["React"]}
    bullets = stack_to_bullets(grouped)
    assert any("AI / LLM" in b for b in bullets)
    assert any("React" in b for b in bullets)
