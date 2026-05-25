"""Tests for StructuredLandingParser on endocrinology fixture."""

from pathlib import Path

import pytest

from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser

FIXTURE = Path(__file__).parent / "fixtures" / "endocrinology_landing.txt"


@pytest.fixture
def parsed():
    text = FIXTURE.read_text(encoding="utf-8")
    return StructuredLandingParser().parse(text)


def test_title(parsed) -> None:
    assert parsed.title == "Эндокринология+"


def test_metadata(parsed) -> None:
    assert parsed.client and "Древаль" in parsed.client
    assert parsed.timeline and "2026" in parsed.timeline
    assert parsed.lead and "Кравченко" in parsed.lead


def test_essence_length(parsed) -> None:
    assert len(parsed.essence) > 200


def test_modules(parsed) -> None:
    names = [m.name for m in parsed.modules]
    assert "GlaucoLogic" in names
    assert "Copilot врача" in names
    assert "VitaCalc" in names


def test_tasks(parsed) -> None:
    assert len(parsed.tasks) >= 8


def test_purpose(parsed) -> None:
    assert len(parsed.purpose) >= 5


def test_inputs(parsed) -> None:
    assert len(parsed.inputs) >= 5


def test_outputs(parsed) -> None:
    assert len(parsed.outputs) >= 7


def test_results(parsed) -> None:
    assert len(parsed.results) >= 8


def test_outlook(parsed) -> None:
    assert len(parsed.outlook) >= 6


def test_tech_stack(parsed) -> None:
    cats = set(parsed.tech_stack_grouped.keys())
    assert "AI / LLM" in cats
    assert "Backend / API" in cats
    assert "Frontend" in cats
    assert "Data Layer" in cats


def test_team(parsed) -> None:
    assert len(parsed.team) >= 15
