"""Build field candidates from parser-level LandingContract outputs."""

from __future__ import annotations

from typing import Any

from app.schemas.evidence import SourceInventoryItem
from app.schemas.fidelity import LandingModule, TeamMember
from app.schemas.fusion import FieldCandidate
from app.schemas.landing_contract import LandingContract
from app.services.fusion.fusion_config import PARSER_MODE_PRIORITY, ROLE_PRIORITY


class FieldCandidateBuilder:
    """Extract per-field candidates from contract parser outputs."""

    def build_from_contracts(
        self,
        candidates: dict[str, LandingContract],
        inventory: list[SourceInventoryItem],
    ) -> dict[str, list[FieldCandidate]]:
        role_by_file = {item.filename: item.source_role for item in inventory}
        type_by_file = {item.filename: item.detected_source_type for item in inventory}
        primary_files = [f for f, r in role_by_file.items() if r == "primary_project_doc"]
        default_file = primary_files[0] if primary_files else (inventory[0].filename if inventory else "")

        by_field: dict[str, list[FieldCandidate]] = {}
        for parser_key, contract in candidates.items():
            parser_mode = contract.fidelity.parser_mode if contract.fidelity else parser_key
            traces = {}
            if contract.fidelity and contract.fidelity.field_sources:
                for trace in contract.fidelity.field_sources:
                    traces[trace.field_name] = trace.source_filename

            field_values = self._extract_field_values(contract)
            for field_name, value in field_values.items():
                if self._is_empty(value):
                    continue
                filename = traces.get(field_name) or self._guess_filename(
                    field_name, parser_mode, inventory, default_file
                )
                source_role = role_by_file.get(filename, self._role_for_parser(parser_mode))
                if field_name == "title" and any(
                    item.source_role == "primary_project_doc" for item in inventory
                ):
                    for item in inventory:
                        if item.source_role == "primary_project_doc":
                            filename = item.filename
                            source_role = item.source_role
                            break
                candidate = FieldCandidate(
                    field_name=field_name,
                    value=value,
                    source_id=parser_key,
                    filename=filename,
                    source_role=source_role,
                    source_type=type_by_file.get(filename, "unknown"),
                    parser_mode=parser_mode,
                    confidence=self._confidence_for(field_name, parser_mode, source_role),
                    evidence_count=self._evidence_count(contract, field_name),
                    reason=f"from {parser_mode}",
                    priority=PARSER_MODE_PRIORITY.get(parser_mode, 40)
                    + ROLE_PRIORITY.get(source_role, 30),
                )
                by_field.setdefault(field_name, []).append(candidate)
        return by_field

    def _extract_field_values(self, contract: LandingContract) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if contract.title:
            values["title"] = contract.title
        if contract.client:
            values["client"] = contract.client
        if contract.timeline:
            values["timeline"] = contract.timeline
        if contract.lead:
            values["lead"] = contract.lead
        if contract.quote:
            values["quote"] = contract.quote

        for block in contract.blocks:
            if block.key == "essence" and block.content:
                values["essence"] = block.content
            elif block.key in (
                "tasks",
                "purpose",
                "inputs",
                "outputs",
                "results",
                "outlook",
            ):
                if block.bullets:
                    values[block.key] = list(block.bullets)

        fidelity = contract.fidelity
        if fidelity:
            if fidelity.tech_stack_grouped:
                values["tech_stack"] = fidelity.tech_stack_grouped
            if fidelity.team_structured:
                values["team"] = fidelity.team_structured
            if fidelity.modules:
                values["modules"] = fidelity.modules
        return values

    def _guess_filename(
        self,
        field_name: str,
        parser_mode: str,
        inventory: list[SourceInventoryItem],
        default_file: str,
    ) -> str:
        if field_name in ("title", "team", "client", "timeline", "lead", "quote"):
            for item in inventory:
                if item.source_role == "primary_project_doc":
                    return item.filename
            for item in inventory:
                if item.file_type in ("docx", "txt") and item.source_role != "module_presentation":
                    return item.filename
        if field_name in ("modules", "tech_stack", "tasks"):
            for item in inventory:
                if item.file_type == "pptx":
                    return item.filename
        if parser_mode == "project_presentation":
            for item in inventory:
                if item.file_type == "pptx":
                    return item.filename
        return default_file

    def _role_for_parser(self, parser_mode: str) -> str:
        if parser_mode == "structured":
            return "primary_project_doc"
        if parser_mode == "project_presentation":
            return "supporting_presentation"
        return "unknown"

    def _confidence_for(self, field_name: str, parser_mode: str, source_role: str) -> float:
        base = PARSER_MODE_PRIORITY.get(parser_mode, 40) / 100.0
        role = ROLE_PRIORITY.get(source_role, 30) / 100.0
        if field_name == "team" and source_role == "primary_project_doc":
            return 0.98
        if field_name == "modules" and source_role in ("module_presentation", "supporting_presentation"):
            return 0.9
        return round(min(base + role * 0.3, 1.0), 3)

    def _evidence_count(self, contract: LandingContract, field_name: str) -> int:
        fidelity = contract.fidelity
        if not fidelity or not fidelity.field_sources:
            return 0
        return sum(1 for t in fidelity.field_sources if t.field_name == field_name)

    def _is_empty(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        if isinstance(value, (list, dict)):
            return len(value) == 0
        return False
