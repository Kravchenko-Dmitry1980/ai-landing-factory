import json
import logging
import re

from app.schemas.extraction import ExtractionResult
from app.services.llm.base import LLMClient

logger = logging.getLogger(__name__)

KEYWORDS = (
    "проект",
    "цель",
    "задач",
    "результат",
    "команда",
    "стек",
    "архитектур",
    "клиент",
    "срок",
)


class MockLLMClient(LLMClient):
    """
    Deterministic mock for local dev/tests.
    Structures text from ExtractionResult without inventing facts.
    """

    def __init__(self, extraction: ExtractionResult | None = None) -> None:
        self._extraction = extraction

    def set_extraction(self, extraction: ExtractionResult) -> None:
        self._extraction = extraction

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
    ) -> dict:
        del system_prompt, schema_name
        if self._extraction is None:
            return _empty_llm_output(["no_extraction_context"])

        return _build_from_extraction(self._extraction, user_prompt)


def _empty_llm_output(missing: list[str]) -> dict:
    return {
        "title": None,
        "client": None,
        "timeline": None,
        "lead": None,
        "essence": None,
        "tasks": [],
        "purpose": None,
        "inputs": [],
        "outputs": [],
        "results": [],
        "roadmap": None,
        "stack": [],
        "team": [],
        "quote": None,
        "confidence": {
            "title": 0.0,
            "client": 0.0,
            "team": 0.0,
            "stack": 0.0,
            "results": 0.0,
        },
        "missing_fields": missing,
        "assumptions": [],
        "source_trace": [],
    }


def _build_from_extraction(extraction: ExtractionResult, user_prompt: str) -> dict:
    combined = "\n".join(
        f.extracted_text for f in extraction.files if f.extracted_text.strip()
    )
    if not combined.strip():
        combined = "\n".join(extraction.payload.raw_notes)

    lines = [ln.strip() for ln in combined.splitlines() if ln.strip()]
    bullets = [ln.lstrip("-•* ").strip() for ln in lines if re.match(r"^[\s]*[-•*]", ln)]

    essence = next((ln for ln in lines if len(ln) > 20), None)
    client = _find_labeled(combined, ("клиент", "заказчик", "customer"))
    timeline = _find_labeled(combined, ("срок", "timeline", "период"))
    title = lines[0][:120] if lines else None

    trace = []
    if essence and extraction.files:
        trace.append(
            {
                "field": "essence",
                "filename": extraction.files[0].filename,
                "evidence": essence[:200],
            }
        )

    missing: list[str] = []
    for field, val in (
        ("title", title),
        ("client", client),
        ("team", None),
        ("stack", None),
        ("results", bullets[2:3] if len(bullets) > 2 else None),
    ):
        if not val:
            missing.append(field)

    stack_items = _find_stack_lines(lines)
    team_items = _find_team_lines(lines)

    return {
        "title": title,
        "client": client,
        "timeline": timeline,
        "lead": None,
        "essence": essence,
        "tasks": bullets[:6] or extraction.payload.tasks,
        "purpose": extraction.payload.purpose,
        "inputs": extraction.payload.inputs or bullets[6:8],
        "outputs": extraction.payload.outputs,
        "results": bullets[3:6] or extraction.payload.results,
        "roadmap": extraction.payload.outlook,
        "stack": stack_items,
        "team": team_items,
        "quote": extraction.payload.tagline or (lines[0][:80] if lines else None),
        "confidence": {
            "title": 0.7 if title else 0.2,
            "client": 0.6 if client else 0.1,
            "team": 0.5 if team_items else 0.1,
            "stack": 0.5 if stack_items else 0.1,
            "results": 0.6 if bullets else 0.2,
        },
        "missing_fields": missing,
        "assumptions": ["mock provider: derived only from extracted_text"],
        "source_trace": trace,
    }


def _find_labeled(text: str, labels: tuple[str, ...]) -> str | None:
    for line in text.splitlines():
        low = line.lower()
        for label in labels:
            if label in low and ":" in line:
                return line.split(":", 1)[-1].strip()[:200]
    return None


def _find_stack_lines(lines: list[str]) -> list[dict]:
    items = []
    for ln in lines:
        low = ln.lower()
        if any(k in low for k in ("python", "fastapi", "react", "postgres", "docker", "stack", "стек")):
            items.append(ln)
    if items:
        return [{"category": "technologies", "items": items[:8]}]
    return []


def _find_team_lines(lines: list[str]) -> list[dict]:
    members = []
    for ln in lines:
        if re.search(r"(team|команда|lead|owner|разработчик)", ln, re.I):
            members.append({"role": "member", "name": "", "contribution": ln[:200]})
    return members[:6]
