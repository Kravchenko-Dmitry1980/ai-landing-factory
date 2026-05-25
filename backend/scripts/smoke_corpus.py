#!/usr/bin/env python3
"""Regression smoke: walk test_corpus/golden/* and validate expected_contract.yml."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
DEFAULT_CORPUS = REPO_ROOT / "test_corpus" / "golden"

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
from app.services.evidence.field_candidates import is_generic_title
from app.services.evidence.multi_source_assembler import MultiSourceEvidenceAssembler
from app.services.evidence.source_inventory import SourceInventoryBuilder
from app.services.extraction.dispatcher import ExtractionDispatcher

EXTRACTED_SUFFIXES = (".pptx.txt", ".docx.txt", ".pdf.txt")
PLAIN_TYPES = {".txt", ".md"}
BINARY_EXTS = {".pptx", ".docx", ".pdf", ".doc"}


def _load_simple_yaml(path: Path) -> dict:
    """Parse flat YAML (scalars + string lists) without external deps."""
    data: dict = {}
    current_list_key: str | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current_list_key:
            item = line.strip()[2:].strip().strip('"').strip("'")
            data.setdefault(current_list_key, []).append(item)
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val == "[]":
            data[key] = []
            current_list_key = None
            continue
        if not val:
            current_list_key = key
            data[key] = []
            continue
        if val.lower() in ("true", "false"):
            data[key] = val.lower() == "true"
        elif re.fullmatch(r"-?\d+", val):
            data[key] = int(val)
        else:
            data[key] = val.strip('"').strip("'")
    return data


def _resolve_source(path: Path) -> tuple[str, str] | None:
    """Map corpus file path → (logical filename, file_type)."""
    name = path.name
    lower = name.lower()
    for suffix, ft in ((".pptx.txt", "pptx"), (".docx.txt", "docx"), (".pdf.txt", "pdf")):
        if lower.endswith(suffix):
            logical = name[: -len(".txt")]
            return logical, ft
    if path.suffix.lower() in BINARY_EXTS:
        return name, path.suffix.lower().lstrip(".")
    if path.suffix.lower() in PLAIN_TYPES:
        return name, "txt"
    return None


def _is_snapshot(path: Path) -> bool:
    lower = path.name.lower()
    return any(lower.endswith(suffix) for suffix in EXTRACTED_SUFFIXES)


def _read_snapshot_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _file_extraction_from_text(
    logical_name: str,
    file_type: str,
    text: str,
) -> FileExtraction:
    meta: dict = {}
    if file_type == "pptx":
        meta["slides_count"] = text.count("Slide ")
    return FileExtraction(
        filename=logical_name,
        file_type=file_type,
        extracted_text=text,
        metadata=meta,
        warnings=[],
        errors=[],
    )


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


def _load_project_sources(project_dir: Path) -> list[FileExtraction]:
    sources_dir = project_dir / "sources"
    if not sources_dir.is_dir():
        raise FileNotFoundError(f"missing sources/: {sources_dir}")

    dispatcher = ExtractionDispatcher()
    grouped: dict[str, dict[str, object]] = {}
    standalone: list[tuple[str, str, Path]] = []

    for path in sorted(sources_dir.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.name.lower() == "readme.md":
            continue
        resolved = _resolve_source(path)
        if not resolved:
            print(f"  skip unsupported: {path.name}", file=sys.stderr)
            continue

        logical_name, file_type = resolved
        suffix = path.suffix.lower()

        if suffix in BINARY_EXTS:
            entry = grouped.setdefault(logical_name, {})
            entry["binary"] = path
            entry["file_type"] = file_type
            continue

        if _is_snapshot(path):
            entry = grouped.setdefault(logical_name, {})
            entry["snapshot"] = path
            entry["file_type"] = file_type
            continue

        if suffix in PLAIN_TYPES:
            standalone.append((logical_name, file_type, path))
            continue

        print(f"  skip unsupported: {path.name}", file=sys.stderr)

    records: list[FileExtraction] = []
    for logical_name in sorted(grouped):
        entry = grouped[logical_name]
        file_type = str(entry.get("file_type", "txt"))
        binary = entry.get("binary")
        snapshot = entry.get("snapshot")

        if isinstance(binary, Path):
            record = dispatcher.extract_file(binary, logical_name)
            if record.errors:
                raise ValueError(
                    f"extraction failed for {binary.name}: {', '.join(record.errors)}"
                )
            records.append(record)
            continue

        if isinstance(snapshot, Path):
            text = _read_snapshot_text(snapshot)
            records.append(_file_extraction_from_text(logical_name, file_type, text))
            continue

        raise FileNotFoundError(f"no binary or snapshot for {logical_name} in {sources_dir}")

    for logical_name, file_type, path in standalone:
        text = _read_snapshot_text(path)
        records.append(_file_extraction_from_text(logical_name, file_type, text))

    if not records:
        raise FileNotFoundError(f"no loadable sources in {sources_dir}")
    return records


def _validate_contract(contract, expected: dict, project_slug: str) -> list[str]:
    errors: list[str] = []
    fidelity = contract.fidelity

    mode = expected.get("expected_parser_mode")
    if mode and fidelity and fidelity.parser_mode != mode:
        errors.append(f"parser_mode: got {fidelity.parser_mode}, want {mode}")

    if expected.get("reject_generic_title", True):
        if not contract.title or is_generic_title(contract.title):
            errors.append(f"generic or empty title: {contract.title!r}")

    title_parts = expected.get("title_contains") or []
    if title_parts:
        title_lower = (contract.title or "").lower()
        if not any(part.lower() in title_lower for part in title_parts):
            errors.append(f"title {contract.title!r} missing any of {title_parts}")

    min_score = int(expected.get("min_completeness", 0))
    score = fidelity.completeness.score if fidelity and fidelity.completeness else 0
    if score < min_score:
        errors.append(f"completeness {score} < {min_score}")

    if expected.get("reject_essence_slide1_only", True):
        essence = next((b for b in contract.blocks if b.key == "essence"), None)
        if essence and essence.content.strip().lower().startswith("slide 1"):
            errors.append("essence is Slide 1 dump only")

    stack_flat: list[str] = []
    if fidelity and fidelity.tech_stack_grouped:
        stack_flat = [t for vals in fidelity.tech_stack_grouped.values() for t in vals]
    for tech in expected.get("must_have_stack") or []:
        if not any(tech.lower() in t.lower() for t in stack_flat):
            errors.append(f"stack missing: {tech}")

    module_names = [m.name for m in (fidelity.modules if fidelity else [])]
    min_modules = int(expected.get("min_modules", 0))
    if min_modules and len(module_names) < min_modules:
        errors.append(f"modules count {len(module_names)} < {min_modules}")
    for frag in expected.get("must_have_modules") or []:
        if not any(frag.lower() in n.lower() for n in module_names):
            errors.append(f"module missing fragment: {frag}")

    team_lines: list[str] = []
    if fidelity and fidelity.team_structured:
        team_lines = [m.name for m in fidelity.team_structured]
    team_block = next((b for b in contract.blocks if b.key == "team"), None)
    if team_block and team_block.bullets:
        team_lines.extend(team_block.bullets)
    for frag in expected.get("must_have_team") or []:
        blob = " ".join(team_lines).lower()
        if frag.lower() not in blob:
            errors.append(f"team missing fragment: {frag}")

    min_team = int(expected.get("min_team", 0))
    team_count = len(fidelity.team_structured) if fidelity and fidelity.team_structured else 0
    if min_team and team_count < min_team:
        errors.append(f"team count {team_count} < {min_team}")

    if not fidelity:
        errors.append("missing fidelity metadata")

    return errors


def _run_project(
    project_dir: Path,
    builder: ContractBuilderService,
) -> tuple[bool, list[str]]:
    slug = project_dir.name
    expected_path = project_dir / "expected_contract.yml"
    if not expected_path.is_file():
        return False, [f"missing {expected_path}"]

    try:
        expected = _load_simple_yaml(expected_path)
        files = _load_project_sources(project_dir)
        extraction = ExtractionResult(
            project_id=uuid4(),
            payload=ExtractionPayload(),
            files=files,
            extracted_at=utc_now(),
        )
        contract = builder.build(extraction)
        errors = _validate_contract(contract, expected, slug)
        if errors:
            return False, errors

        score = contract.fidelity.completeness.score if contract.fidelity and contract.fidelity.completeness else 0
        mode = contract.fidelity.parser_mode if contract.fidelity else "?"
        print(
            f"  OK {slug}: mode={mode} completeness={score} "
            f"title={(contract.title or '')[:60]!r} sources={len(files)}"
        )
        return True, []
    except Exception as exc:
        return False, [str(exc)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test_corpus golden projects")
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=DEFAULT_CORPUS,
        help="Directory with project subfolders (default: test_corpus/golden)",
    )
    parser.add_argument(
        "--project",
        type=str,
        default="",
        help="Run only this project slug (subfolder name)",
    )
    args = parser.parse_args()

    corpus_dir = args.corpus_dir.resolve()
    if not corpus_dir.is_dir():
        print(f"Corpus dir not found: {corpus_dir}", file=sys.stderr)
        return 1

    projects = sorted(
        p for p in corpus_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
    )
    if args.project:
        projects = [p for p in projects if p.name == args.project]
        if not projects:
            print(f"Project not found: {args.project}", file=sys.stderr)
            return 1

    print(f"Corpus: {corpus_dir} ({len(projects)} project(s))")
    builder = _builder()
    failed = 0

    for project_dir in projects:
        ok, errors = _run_project(project_dir, builder)
        if not ok:
            failed += 1
            print(f"  FAIL {project_dir.name}:", file=sys.stderr)
            for err in errors:
                print(f"    - {err}", file=sys.stderr)

    if failed:
        print(f"\n{failed} project(s) failed", file=sys.stderr)
        return 1
    print(f"\nAll {len(projects)} project(s) passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
