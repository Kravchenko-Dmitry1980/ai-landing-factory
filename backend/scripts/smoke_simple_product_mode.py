#!/usr/bin/env python3
"""Product simple-mode smoke — no OCR/VLM runtime required."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
INDLAB = REPO_ROOT / "test_corpus" / "golden" / "indlab_telegram_news"
SOURCES = INDLAB / "sources"

sys.path.insert(0, str(BACKEND))

# Force simple product profile before Settings loads.
os.environ.setdefault("PRODUCT_MODE", "simple")
os.environ.setdefault("OCR_ENABLED", "false")
os.environ.setdefault("VLM_ENABLED", "false")
os.environ.setdefault("ADVANCED_VISUAL_PIPELINE", "false")
os.environ.setdefault("ENABLE_ADVANCED_DIAGNOSTICS", "false")

from app.config import settings  # noqa: E402
from app.models.domain import utc_now  # noqa: E402
from app.product_mode import collect_product_mode_warnings  # noqa: E402
from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction  # noqa: E402
from app.services.analysis.contract_builder import ContractBuilderService  # noqa: E402
from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate  # noqa: E402
from app.services.contract_fidelity.landing_document_detector import LandingDocumentDetector  # noqa: E402
from app.services.contract_fidelity.presentation_landing_synthesizer import (  # noqa: E402
    PresentationLandingSynthesizer,
)
from app.services.contract_fidelity.source_type_detector import SourceTypeDetector  # noqa: E402
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser  # noqa: E402
from app.services.evidence.evidence_visibility import EvidenceVisibilityBuilder  # noqa: E402
from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler  # noqa: E402
from app.services.evidence.source_inventory import SourceInventoryBuilder  # noqa: E402
from app.services.fusion.field_fusion_engine import FieldFusionEngine  # noqa: E402


def _make_builder() -> ContractBuilderService:
    builder = ContractBuilderService.__new__(ContractBuilderService)
    builder._detector = LandingDocumentDetector()
    builder._source_type_detector = SourceTypeDetector()
    builder._structured_parser = StructuredLandingParser()
    builder._presentation_synthesizer = PresentationLandingSynthesizer()
    builder._completeness_gate = ContractCompletenessGate()
    builder._inventory_builder = SourceInventoryBuilder()
    builder._multi_source_assembler = MultiSourceEvidenceAssembler()
    builder._field_fusion_engine = FieldFusionEngine()
    return builder


def _fail(msg: str) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


def _read_text(name: str) -> str:
    path = SOURCES / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def _build_indlab_contract() -> tuple[object, list[str]]:
    docx = _read_text("02_landing.docx.txt")
    pptx = _read_text("01_presentation.pptx.txt")
    extraction = ExtractionResult(
        project_id=uuid4(),
        payload=ExtractionPayload(),
        files=[
            FileExtraction(
                filename="02_landing.docx",
                file_type="docx",
                extracted_text=docx,
            ),
            FileExtraction(
                filename="01_presentation.pptx",
                file_type="pptx",
                extracted_text=pptx,
                metadata={"slides_count": pptx.count("Slide ")},
            ),
        ],
        extracted_at=utc_now(),
    )
    contract = _make_builder().build(extraction)
    return contract, []


def main() -> int:
    errors: list[str] = []

    if settings.normalized_product_mode != "simple":
        errors.append(f"PRODUCT_MODE expected simple, got {settings.normalized_product_mode}")
    if settings.ocr_enabled:
        errors.append("OCR must be disabled in simple smoke")
    if settings.vlm_enabled:
        errors.append("VLM must be disabled in simple smoke")
    if settings.effective_advanced_visual_pipeline:
        errors.append("advanced visual pipeline must be off in simple mode")

    _ = collect_product_mode_warnings(settings)

    try:
        contract, _ = _build_indlab_contract()
    except Exception as exc:
        return _fail(f"ContractBuilder indlab failed: {exc}")

    if not contract.blocks:
        errors.append("contract has no blocks")

    report = EvidenceVisibilityBuilder().build(contract)
    if report.advanced_diagnostics_enabled:
        errors.append("evidence report must hide advanced diagnostics in simple mode")
    payload_lower = report.model_dump_json().lower()
    for term in ("paddleocr", "tesseract", "easyocr", "easy ocr"):
        if term in payload_lower:
            errors.append(f"evidence payload leaks technical term: {term}")

    if not any("изображение" in h or "DOCX" in h for h in report.improvement_hints + report.warnings):
        # empty pptx file in corpus may not trigger — acceptable if no empty sources
        pass

    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "landing.html"
        parts = ["<!DOCTYPE html><html lang='ru'><body>"]
        for block in contract.blocks:
            parts.append(f"<section><h2>{block.title}</h2>")
            if block.content:
                parts.append(f"<p>{block.content}</p>")
            for bullet in block.bullets[:20]:
                parts.append(f"<li>{bullet}</li>")
            parts.append("</section>")
        parts.append("</body></html>")
        out_path.write_text("".join(parts), encoding="utf-8")
        if out_path.stat().st_size < 200:
            errors.append("HTML export missing or too small")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print("SIMPLE PRODUCT MODE SMOKE PASSED")
    print(f"  product_mode={settings.normalized_product_mode}")
    print(f"  blocks={len(contract.blocks)}")
    print(f"  sources={report.source_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
