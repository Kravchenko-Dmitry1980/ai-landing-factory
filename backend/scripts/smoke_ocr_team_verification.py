#!/usr/bin/env python3
"""Smoke: OCR team verification gate — unverified OCR names excluded from public export."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.models.domain import utc_now
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction
from app.schemas.landing_contract import ContractStatus, LandingContract
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
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.services.team_verification.trusted_roster_builder import load_expected_contract_team
from scripts.smoke_corpus import _load_simple_yaml, _read_snapshot_text, _resolve_source

CORPUS_ROOT = REPO_ROOT / "test_corpus" / "golden"
BAD_OCR_NAMES = [
    "Наденда Глазунова",
    "Денис Калюаный",
    "Александр Егорсв",
    "Татьяна Залоротец",
]


class _FakeRepo:
    def __init__(self, contract: LandingContract) -> None:
        self._contract = contract

    async def get_contract(self, _pid):
        return self._contract

    async def get_landing(self, _pid):
        return None


def _build_extraction(project: str) -> ExtractionResult:
    project_dir = CORPUS_ROOT / project / "sources"
    if not project_dir.is_dir():
        raise FileNotFoundError(f"Corpus project not found: {project_dir}")

    files: list[FileExtraction] = []
    for path in sorted(project_dir.iterdir()):
        resolved = _resolve_source(path)
        if not resolved:
            continue
        logical_name, file_type = resolved
        if path.suffix.lower() == ".txt" and ".pptx." in path.name.lower():
            text = _read_snapshot_text(path)
            files.append(
                FileExtraction(
                    filename=logical_name,
                    file_type=file_type,
                    extracted_text=text,
                )
            )
        elif path.suffix.lower() in (".txt", ".md"):
            files.append(
                FileExtraction(
                    filename=logical_name,
                    file_type=file_type,
                    extracted_text=path.read_text(encoding="utf-8", errors="replace"),
                )
            )

    return ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=files,
        extracted_at=utc_now(),
    )


def _make_builder() -> ContractBuilderService:
    builder = ContractBuilderService.__new__(ContractBuilderService)
    builder._detector = LandingDocumentDetector()
    builder._source_type_detector = SourceTypeDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._presentation_synthesizer = PresentationLandingSynthesizer()
    builder._completeness_gate = ContractCompletenessGate()
    builder._inventory_builder = SourceInventoryBuilder()
    builder._multi_source_assembler = MultiSourceEvidenceAssembler()
    from app.services.fusion.field_fusion_engine import FieldFusionEngine
    from app.services.ocr.ocr_enrichment import OcrEnrichmentService
    from app.services.orchestration.document_orchestrator import DocumentOrchestrator

    builder._field_fusion_engine = FieldFusionEngine()
    builder._document_orchestrator = DocumentOrchestrator()
    builder._ocr_enrichment = OcrEnrichmentService()
    return builder


def main() -> int:
    parser = argparse.ArgumentParser(description="OCR team verification smoke")
    parser.add_argument("--project", default="indlab_telegram_news")
    parser.add_argument("--engine", default="easyocr", help="Informational only")
    parser.add_argument(
        "--allow-review-candidates",
        action="store_true",
        help="Do not fail if review candidates exist",
    )
    parser.add_argument(
        "--require-verified-count",
        type=int,
        default=0,
        help="Minimum verified team members (0=disabled)",
    )
    args = parser.parse_args()

    extraction = _build_extraction(args.project)
    builder = _make_builder()
    contract = builder.build(extraction)

    fidelity = contract.fidelity
    report = fidelity.team_verification_report if fidelity else None
    errors: list[str] = []

    print(f"project: {args.project}")
    print(f"engine (info): {args.engine}")

    if report:
        print(
            f"verification: verified={report.metrics.verified_count} "
            f"review={report.metrics.needs_review_count} "
            f"rejected={report.metrics.rejected_count} "
            f"ocr={report.metrics.ocr_candidates}"
        )
        if report.review_candidates:
            print("review candidates:")
            for c in report.review_candidates[:10]:
                match = f" → {c.matched_trusted_name}" if c.matched_trusted_name else ""
                print(f"  - {c.raw_name}{match} ({c.verification_reason})")
    else:
        print("WARN: no team_verification_report on contract")

    if args.require_verified_count and report:
        if report.metrics.verified_count < args.require_verified_count:
            errors.append(
                f"verified_count {report.metrics.verified_count} "
                f"< required {args.require_verified_count}"
            )

    repo = _FakeRepo(contract)
    html = __import__("asyncio").run(StyledHtmlExporter(repo).to_html(contract.project_id))

    for bad in BAD_OCR_NAMES:
        if bad in html:
            errors.append(f"bad OCR name in public export: {bad}")

    expected_names = load_expected_contract_team(args.project)
    if expected_names:
        print(f"expected roster fragments: {expected_names}")

    if errors:
        print("FAIL:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("PASS: public export excludes unverified OCR names")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
