#!/usr/bin/env python3
"""Smoke test for multi-source evidence assembly."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID, uuid4

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.models.domain import utc_now
from app.repositories.contract_repository import ContractRepository
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector
from app.services.contract_fidelity.presentation_landing_synthesizer import (
    PresentationLandingSynthesizer,
)
from app.services.contract_fidelity.source_type_detector import SourceTypeDetector
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser
from app.services.evidence.field_candidates import is_generic_title
from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
from app.services.evidence.source_inventory import SourceInventoryBuilder

FIXTURES = {
    "telegram_analytics": BACKEND / "tests" / "fixtures" / "telegram_analytics_presentation.txt",
}


def _builder() -> ContractBuilderService:
    from app.config import settings

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


def _extraction_from_text(path: Path, filename: str, file_type: str) -> ExtractionResult:
    text = path.read_text(encoding="utf-8")
    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename=filename,
                file_type=file_type,
                extracted_text=text,
                metadata={"slides_count": text.count("Slide ")},
            )
        ],
        extracted_at=utc_now(),
    )


def _checks(contract, errors: list[str]) -> bool:
    fidelity = contract.fidelity
    if not fidelity:
        errors.append("missing fidelity")
        return False

    if fidelity.source_count < 1:
        errors.append(f"source_count={fidelity.source_count}")
    if fidelity.evidence_count < fidelity.source_count:
        errors.append(
            f"evidence_count={fidelity.evidence_count} < source_count={fidelity.source_count}"
        )

    mode = fidelity.parser_mode
    if mode not in ("multi_source_assembly", "structured", "project_presentation"):
        errors.append(f"parser_mode={mode}")

    if contract.title and is_generic_title(contract.title):
        errors.append(f"generic title: {contract.title}")

    essence = next((b for b in contract.blocks if b.key == "essence"), None)
    if essence and essence.content.strip().lower().startswith("slide 1"):
        errors.append("essence is only Slide 1 dump")

    score = fidelity.completeness.score if fidelity.completeness else 0
    if score < 70 and mode == "multi_source_assembly":
        errors.append(f"completeness={score} < 70")

    return len(errors) == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke multi-source assembly")
    parser.add_argument("--project-id", type=str, default="")
    parser.add_argument("--files", nargs="*", default=[])
    parser.add_argument("--fixture", choices=sorted(FIXTURES.keys()), default="")
    args = parser.parse_args()

    errors: list[str] = []
    builder = _builder()

    if args.fixture:
        path = FIXTURES[args.fixture]
        extraction = _extraction_from_text(path, "fixture.pptx", "pptx")
        contract = builder.build(extraction)
        print(json.dumps({
            "mode": contract.fidelity.parser_mode if contract.fidelity else None,
            "title": contract.title,
            "completeness": contract.fidelity.completeness.score if contract.fidelity and contract.fidelity.completeness else 0,
            "evidence_count": contract.fidelity.evidence_count if contract.fidelity else 0,
        }, ensure_ascii=False, indent=2))
        ok = _checks(contract, errors)
    elif args.project_id:
        import asyncio
        from app.config import settings

        repo = ContractRepository(settings)
        pid = UUID(args.project_id)
        extraction = asyncio.run(repo.get_extraction(pid))
        if not extraction:
            print(f"No extraction for {pid}", file=sys.stderr)
            return 1
        contract = builder.build(extraction)
        ok = _checks(contract, errors)
        print(f"project={pid} mode={contract.fidelity.parser_mode} completeness={contract.fidelity.completeness.score}")
    elif args.files:
        files = []
        for fp in args.files:
            path = Path(fp)
            ext = path.suffix.lower().lstrip(".")
            ft = ext if ext in ("pptx", "docx", "pdf", "txt", "md") else "other"
            files.append(
                FileExtraction(
                    filename=path.name,
                    file_type=ft,
                    extracted_text=path.read_text(encoding="utf-8", errors="replace"),
                    metadata={},
                )
            )
        extraction = ExtractionResult(
            project_id=uuid4(),
            payload=ExtractionPayload(),
            files=files,
            extracted_at=utc_now(),
        )
        contract = builder.build(extraction)
        ok = _checks(contract, errors)
    else:
        parser.print_help()
        return 1

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print("OK: multi-source smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
