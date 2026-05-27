#!/usr/bin/env python3
"""Runtime smoke: health API + simple product mode from backend .env and evidence API."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

import httpx

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
DEFAULT_PORTS = REPO_ROOT / ".runtime" / "ports.json"


def _read_backend_url(explicit: str) -> str:
    if explicit:
        return explicit.rstrip("/")
    if DEFAULT_PORTS.is_file():
        data = json.loads(DEFAULT_PORTS.read_text(encoding="utf-8-sig"))
        url = data.get("backend_url") or ""
        if url:
            return str(url).rstrip("/")
    return "http://127.0.0.1:8001"


def _parse_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.is_file():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        t = line.strip()
        if not t or t.startswith("#") or "=" not in t:
            continue
        key, val = t.split("=", 1)
        values[key.strip()] = val.strip()
    return values


def _env_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Product mode runtime smoke")
    parser.add_argument("--backend-url", default="")
    args = parser.parse_args()

    errors: list[str] = []
    backend_url = _read_backend_url(args.backend_url)
    env_path = BACKEND / ".env"
    env = _parse_env_file(env_path)

    if env.get("PRODUCT_MODE", "").lower() != "simple":
        errors.append(f"backend/.env PRODUCT_MODE must be simple, got {env.get('PRODUCT_MODE')!r}")
    for key in ("OCR_ENABLED", "VLM_ENABLED", "ADVANCED_VISUAL_PIPELINE"):
        if _env_bool(env.get(key), default=False):
            errors.append(f"backend/.env {key} must be false in simple mode")

    with httpx.Client(timeout=30.0, trust_env=False) as client:
        health = client.get(f"{backend_url}/health")
        if health.status_code != 200:
            errors.append(f"/health HTTP {health.status_code}")
        else:
            body = health.json()
            if body.get("status") != "ok":
                errors.append(f"/health unexpected body: {body}")

        # Evidence API reflects effective simple diagnostics (no project files needed).
        sys.path.insert(0, str(BACKEND))
        os.environ.setdefault("PRODUCT_MODE", env.get("PRODUCT_MODE", "simple"))
        os.environ.setdefault("OCR_ENABLED", env.get("OCR_ENABLED", "false"))
        os.environ.setdefault("VLM_ENABLED", env.get("VLM_ENABLED", "false"))
        os.environ.setdefault(
            "ADVANCED_VISUAL_PIPELINE",
            env.get("ADVANCED_VISUAL_PIPELINE", "false"),
        )
        os.environ.setdefault(
            "ENABLE_ADVANCED_DIAGNOSTICS",
            env.get("ENABLE_ADVANCED_DIAGNOSTICS", "false"),
        )

        from app.config import settings  # noqa: E402
        from app.services.analysis.contract_builder import ContractBuilderService  # noqa: E402
        from app.services.evidence.evidence_visibility import EvidenceVisibilityBuilder  # noqa: E402

        def _make_builder() -> ContractBuilderService:
            builder = ContractBuilderService.__new__(ContractBuilderService)
            from app.services.contract_fidelity.completeness_gate import ContractCompletenessGate
            from app.services.contract_fidelity.landing_document_detector import (
                LandingDocumentDetector,
            )
            from app.services.contract_fidelity.presentation_landing_synthesizer import (
                PresentationLandingSynthesizer,
            )
            from app.services.contract_fidelity.source_type_detector import SourceTypeDetector
            from app.services.contract_fidelity.structured_landing_parser import (
                StructuredLandingParser,
            )
            from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
            from app.services.evidence.source_inventory import SourceInventoryBuilder
            from app.services.fusion.field_fusion_engine import FieldFusionEngine

            builder._detector = LandingDocumentDetector()
            builder._source_type_detector = SourceTypeDetector()
            builder._structured_parser = StructuredLandingParser()
            builder._presentation_synthesizer = PresentationLandingSynthesizer()
            builder._completeness_gate = ContractCompletenessGate()
            builder._inventory_builder = SourceInventoryBuilder()
            builder._multi_source_assembler = MultiSourceEvidenceAssembler()
            builder._field_fusion_engine = FieldFusionEngine()
            return builder

        if settings.normalized_product_mode != "simple":
            errors.append(
                f"effective product_mode={settings.normalized_product_mode}, expected simple"
            )
        if settings.ocr_enabled:
            errors.append("effective OCR_ENABLED=true")
        if settings.vlm_enabled:
            errors.append("effective VLM_ENABLED=true")
        if settings.effective_advanced_visual_pipeline:
            errors.append("effective ADVANCED_VISUAL_PIPELINE=true")

        # Minimal contract for evidence visibility gate.
        from app.models.domain import utc_now  # noqa: E402
        from app.schemas.extraction import ExtractionPayload, ExtractionResult, FileExtraction  # noqa: E402
        extraction = ExtractionResult(
            project_id=uuid4(),
            payload=ExtractionPayload(),
            files=[
                FileExtraction(
                    filename="sample.docx",
                    file_type="docx",
                    extracted_text="Заголовок проекта\nСуть: тестовый лендинг.",
                )
            ],
            extracted_at=utc_now(),
        )
        contract = _make_builder().build(extraction)
        report = EvidenceVisibilityBuilder().build(contract)
        if report.advanced_diagnostics_enabled:
            errors.append("evidence report exposes advanced_diagnostics in simple mode")

        api = f"{backend_url}/api/v1"
        # Empty project returns 404 for evidence-report until upload/contract exists.
        create = client.post(
            f"{api}/projects",
            json={"name": "UAT product mode", "description": "smoke"},
        )
        if create.status_code != 201:
            errors.append(f"create project HTTP {create.status_code}")
        else:
            project_id = create.json()["id"]
            ev = client.get(f"{api}/projects/{project_id}/evidence-report")
            if ev.status_code == 404:
                pass
            elif ev.status_code != 200:
                errors.append(f"evidence-report HTTP {ev.status_code}")
            else:
                payload = ev.json()
                if payload.get("advanced_diagnostics_enabled"):
                    errors.append("live evidence-report has advanced_diagnostics_enabled=true")
                blob = json.dumps(payload, ensure_ascii=False).lower()
                for term in ("paddleocr", "tesseract", "easyocr", "vllm"):
                    if term in blob:
                        errors.append(f"evidence-report leaks term: {term}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print("OK: product mode runtime smoke passed")
    print(f"  backend_url={backend_url}")
    print(f"  PRODUCT_MODE=simple OCR/VLM off")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
