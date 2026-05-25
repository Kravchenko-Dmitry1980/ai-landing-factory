import json
import logging
import re
from typing import Any

from pydantic import ValidationError

from app.schemas.enrichment import ConfidenceScores, SourceTraceItem
from app.schemas.landing import LLMContractOutput, StackCategory, TeamMember
from app.services.analysis.source_trace import normalize_source_trace

logger = logging.getLogger(__name__)


def repair_json_text(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)
    return text


def parse_llm_json(raw: str | dict) -> dict:
    if isinstance(raw, dict):
        return raw
    repaired = repair_json_text(str(raw))
    return json.loads(repaired)


def validate_llm_output(data: dict) -> LLMContractOutput:
    return LLMContractOutput.model_validate(data)


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _normalize_team(team: list[Any]) -> list[str]:
    lines: list[str] = []
    for item in team or []:
        if isinstance(item, str) and item.strip():
            lines.append(item.strip())
        elif isinstance(item, dict):
            m = TeamMember.model_validate(item)
            part = " — ".join(x for x in (m.name, m.role, m.contribution) if x)
            if part.strip():
                lines.append(part.strip())
        elif isinstance(item, TeamMember):
            part = " — ".join(x for x in (item.name, item.role, item.contribution) if x)
            if part.strip():
                lines.append(part.strip())
    return lines


def _normalize_stack(stack: list[Any]) -> tuple[list[str], list[StackCategory]]:
    flat: list[str] = []
    categories: list[StackCategory] = []
    for item in stack or []:
        if isinstance(item, str) and item.strip():
            flat.append(item.strip())
        elif isinstance(item, dict):
            try:
                cat = StackCategory.model_validate(item)
                categories.append(cat)
                flat.extend(cat.items)
            except ValidationError:
                flat.append(str(item))
        elif isinstance(item, StackCategory):
            categories.append(item)
            flat.extend(item.items)
    if not categories and flat:
        categories = [StackCategory(category="technologies", items=flat)]
    return flat, categories


def normalize_llm_output(data: dict) -> LLMContractOutput:
    try:
        parsed = parse_llm_json(data)
        output = validate_llm_output(parsed)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("LLM output validation failed: %s", exc)
        raise

    team_lines = _normalize_team(output.team)
    stack_flat, _ = _normalize_stack(output.stack)

    return LLMContractOutput(
        title=_clean_str(output.title),
        client=_clean_str(output.client),
        timeline=_clean_str(output.timeline),
        lead=_clean_str(output.lead),
        essence=_clean_str(output.essence),
        tasks=output.tasks,
        purpose=_clean_str(output.purpose),
        inputs=output.inputs,
        outputs=output.outputs,
        results=output.results,
        roadmap=_clean_str(output.roadmap),
        stack=stack_flat,
        team=team_lines,
        quote=_clean_str(output.quote),
        confidence=output.confidence,
        missing_fields=list(dict.fromkeys(output.missing_fields)),
        assumptions=output.assumptions,
        source_trace=normalize_source_trace(output.source_trace),
    )


def collect_missing_fields(output: LLMContractOutput) -> list[str]:
    missing = list(output.missing_fields)
    checks = {
        "title": output.title,
        "client": output.client,
        "timeline": output.timeline,
        "lead": output.lead,
        "essence": output.essence,
        "tasks": output.tasks,
        "purpose": output.purpose,
        "inputs": output.inputs,
        "outputs": output.outputs,
        "results": output.results,
        "roadmap": output.roadmap,
        "stack": output.stack,
        "team": output.team,
        "quote": output.quote,
    }
    for field, val in checks.items():
        if field in missing:
            continue
        if val is None or val == [] or val == "":
            missing.append(field)
    return list(dict.fromkeys(missing))
