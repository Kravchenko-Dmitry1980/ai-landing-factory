"""Validate LandingContract completeness after structured or heuristic build."""

from __future__ import annotations

from app.schemas.fidelity import ContractCompletenessReport, FidelityMetadata
from app.schemas.landing_contract import LandingContract

REQUIRED_THRESHOLDS = {
    "essence_chars": 200,
    "tasks": 5,
    "purpose": 3,
    "inputs": 3,
    "outputs": 3,
    "results": 3,
    "outlook": 3,
    "team": 3,
    "modules": 1,
}


class ContractCompletenessGate:
    """Score contract quality and flag missing/weak fields."""

    def evaluate(self, contract: LandingContract) -> ContractCompletenessReport:
        blocks = {b.key: b for b in contract.blocks}
        missing: list[str] = []
        weak: list[str] = []
        warnings: list[str] = []
        checks_passed = 0
        total_checks = 11

        if not contract.title:
            missing.append("title")
        else:
            checks_passed += 1

        essence = blocks.get("essence")
        essence_len = len(essence.content) if essence else 0
        if essence_len <= REQUIRED_THRESHOLDS["essence_chars"]:
            weak.append("essence")
            missing.append("essence")
        else:
            checks_passed += 1

        for key, min_count in (
            ("tasks", REQUIRED_THRESHOLDS["tasks"]),
            ("purpose", REQUIRED_THRESHOLDS["purpose"]),
            ("inputs", REQUIRED_THRESHOLDS["inputs"]),
            ("outputs", REQUIRED_THRESHOLDS["outputs"]),
            ("results", REQUIRED_THRESHOLDS["results"]),
            ("outlook", REQUIRED_THRESHOLDS["outlook"]),
        ):
            block = blocks.get(key)
            count = _list_count(block)
            if count < min_count:
                missing.append(key)
                if count > 0:
                    weak.append(key)
            else:
                checks_passed += 1

        stack = blocks.get("tech_stack")
        stack_ok = bool(stack and (stack.bullets or stack.content.strip()))
        fidelity = contract.fidelity
        if fidelity and fidelity.tech_stack_grouped:
            stack_ok = True
        if not stack_ok:
            missing.append("tech_stack")
        else:
            checks_passed += 1

        team_count = _team_count(contract)
        if team_count < REQUIRED_THRESHOLDS["team"]:
            missing.append("team")
            if team_count > 0:
                weak.append("team")
        else:
            checks_passed += 1

        modules_count = len(fidelity.modules) if fidelity else 0
        if modules_count < REQUIRED_THRESHOLDS["modules"]:
            missing.append("modules")
        else:
            checks_passed += 1

        score = int(round(checks_passed / total_checks * 100))
        complete = score >= 70
        export_incomplete = score < 70

        if not complete:
            warnings.append(
                f"Contract completeness {score}/100 — review: {', '.join(missing[:6])}"
            )

        recommended = "ready"
        if score < 70:
            recommended = "reparse_or_review"
        elif weak:
            recommended = "review_weak_fields"

        return ContractCompletenessReport(
            score=score,
            missing_fields=missing,
            weak_fields=weak,
            warnings=warnings,
            recommended_action=recommended,
            complete=complete,
            export_incomplete=export_incomplete,
        )


def _list_count(block) -> int:
    if not block:
        return 0
    if block.bullets:
        return len(block.bullets)
    if block.content.strip():
        lines = [ln for ln in block.content.splitlines() if ln.strip()]
        return len(lines)
    return 0


def _team_count(contract: LandingContract) -> int:
    fidelity: FidelityMetadata | None = contract.fidelity
    if fidelity and fidelity.team_structured:
        return len(fidelity.team_structured)
    team_block = next((b for b in contract.blocks if b.key == "team"), None)
    if not team_block:
        return 0
    if team_block.bullets:
        return sum(1 for b in team_block.bullets if not b.strip().startswith("·"))
    return _list_count(team_block)
