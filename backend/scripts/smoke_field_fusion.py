#!/usr/bin/env python3
"""Smoke test for field-level multi-source fusion."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
CORPUS = REPO / "test_corpus" / "golden"

sys.path.insert(0, str(BACKEND))

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector
from app.services.contract_fidelity.presentation_landing_synthesizer import (
    PresentationLandingSynthesizer,
)
from app.services.contract_fidelity.source_type_detector import SourceTypeDetector
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser
from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
from app.services.evidence.source_inventory import SourceInventoryBuilder
from scripts.smoke_corpus import _load_project_sources, _load_simple_yaml

PROJECTS = {
    "indlab_telegram_news": CORPUS / "indlab_telegram_news",
    "endocrinology": CORPUS / "endocrinology",
    "ksk_it_barrier": CORPUS / "ksk_it_barrier",
}


def _builder() -> ContractBuilderService:
    from app.config import settings
    from app.repositories.contract_repository import ContractRepository

    repo = ContractRepository(settings)
    b = ContractBuilderService(repo)
    b._detector = LandingDocumentDetector()
    b._source_type_detector = SourceTypeDetector()
    b._structured_parser = StructuredLandingParser()
    b._presentation_synthesizer = PresentationLandingSynthesizer()
    b._completeness_gate = ContractCompletenessGate()
    b._inventory_builder = SourceInventoryBuilder()
    b._multi_source_assembler = MultiSourceEvidenceAssembler()
    return b


def _run_project(name: str, project_dir: Path) -> list[str]:
    errors: list[str] = []
    expected_path = project_dir / "expected_contract.yml"
    expected = _load_simple_yaml(expected_path) if expected_path.exists() else {}

    files = _load_project_sources(project_dir)
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=files,
        extracted_at=utc_now(),
    )
    contract = _builder().build(extraction)
    fidelity = contract.fidelity
    if not fidelity:
        errors.append("missing fidelity")
        return errors

    source_count = fidelity.source_count or len(files)
    if source_count >= 2 and fidelity.parser_mode != "field_level_fusion":
        errors.append(f"expected field_level_fusion, got {fidelity.parser_mode}")

    if source_count == 1 and fidelity.parser_mode == "field_level_fusion":
        errors.append("single-source project should not use field_level_fusion")

    forbidden = expected.get("forbidden_team_names") or []
    team_names = " ".join(m.name for m in fidelity.team_structured).lower()
    for bad in forbidden:
        if bad.lower() in team_names:
            errors.append(f"forbidden team name present: {bad}")

    min_team = expected.get("min_team")
    if min_team is not None and len(fidelity.team_structured) < int(min_team):
        errors.append(f"team count {len(fidelity.team_structured)} < {min_team}")

    if fidelity.modules and len(fidelity.modules) > 15:
        errors.append(f"too many modules: {len(fidelity.modules)}")

    decisions = fidelity.field_decisions or {}
    if source_count >= 2:
        for key in ("title", "team", "modules", "tech_stack"):
            if key not in decisions:
                errors.append(f"missing fusion decision for {key}")

    title_need = expected.get("title_contains") or []
    if title_need and contract.title:
        if not any(part in contract.title for part in title_need):
            errors.append(f"title mismatch: {contract.title}")

    print(
        f"{name}: mode={fidelity.parser_mode} sources={source_count} "
        f"team={len(fidelity.team_structured)} modules={len(fidelity.modules)} "
        f"score={fidelity.completeness.score if fidelity.completeness else '?'}"
    )
    if decisions:
        for field in ("title", "team", "modules", "tech_stack"):
            if field in decisions:
                src = decisions[field].get("selected_sources", [])
                print(f"  {field} <- {src}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke field-level fusion")
    parser.add_argument("--project", choices=list(PROJECTS.keys()))
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    names = list(PROJECTS.keys()) if args.all else ([args.project] if args.project else [])
    if not names:
        parser.error("Specify --project or --all")

    all_errors: list[str] = []
    for name in names:
        project_dir = PROJECTS[name]
        if not project_dir.is_dir():
            all_errors.append(f"{name}: missing corpus dir")
            continue
        all_errors.extend(_run_project(name, project_dir))

    if all_errors:
        print("FAIL:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("OK: field fusion smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
