"""Gap analysis for assembled contract fields."""

from __future__ import annotations

from app.schemas.evidence import FieldEvidence
from app.services.evidence.field_candidates import is_generic_title

FIELD_MINIMUMS = {
    "title": {"non_generic": True},
    "essence": {"min_chars": 300},
    "tasks": {"min_items": 4},
    "purpose": {"min_items": 3},
    "inputs": {"min_items": 3},
    "outputs": {"min_items": 3},
    "results": {"min_items": 3},
    "outlook": {"min_items": 2},
    "tech_stack": {"min_items": 3},
    "modules": {"min_items": 3},
    "team": {"min_items": 1, "optional_if_no_evidence": True},
}


class GapAnalyzer:
    """Classify fields as missing, weak, or strong after assembly."""

    def analyze(
        self,
        assembled: dict[str, object],
        field_evidence: dict[str, FieldEvidence],
        *,
        team_evidence_exists: bool,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        missing: list[str] = []
        weak: list[str] = []
        strong: list[str] = []
        warnings: list[str] = []

        for field_name, rules in FIELD_MINIMUMS.items():
            value = assembled.get(field_name)
            ev = field_evidence.get(field_name)
            if field_name == "title":
                title = str(value or "").strip()
                if not title or is_generic_title(title):
                    missing.append("title")
                    if title:
                        weak.append("title")
                else:
                    strong.append("title")
                continue

            if field_name == "essence":
                text = str(value or "")
                if len(text) < rules["min_chars"]:
                    missing.append("essence")
                    if text:
                        weak.append("essence")
                else:
                    strong.append("essence")
                continue

            if field_name == "tech_stack":
                stack = value if isinstance(value, dict) else {}
                count = sum(len(v) for v in stack.values()) if stack else 0
                if count < rules["min_items"]:
                    missing.append("tech_stack")
                else:
                    strong.append("tech_stack")
                continue

            if field_name == "team":
                team = value if isinstance(value, list) else []
                if not team:
                    if team_evidence_exists:
                        missing.append("team")
                    continue
                if len(team) < rules["min_items"]:
                    weak.append("team")
                else:
                    strong.append("team")
                continue

            items = value if isinstance(value, list) else []
            min_items = rules.get("min_items", 1)
            if len(items) < min_items:
                missing.append(field_name)
                if items:
                    weak.append(field_name)
            else:
                strong.append(field_name)

            if ev and ev.coverage == "weak" and field_name not in weak:
                weak.append(field_name)

        if missing:
            warnings.append(f"Missing fields: {', '.join(missing[:8])}")

        return missing, weak, strong, warnings
