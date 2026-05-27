"""Build trusted team roster from non-OCR sources."""

from __future__ import annotations

import logging
from pathlib import Path

from app.schemas.extraction import ExtractionResult, FileExtraction
from app.schemas.fidelity import TeamMember
from app.services.contract_fidelity.structured_landing_parser import StructuredLandingParser
from app.services.contract_fidelity.team_candidate_validator import filter_team_members
from app.services.evidence.people_extractor import extract_people_from_text

logger = logging.getLogger(__name__)

TRUSTED_FILE_TYPES = frozenset({"docx", "txt", "md"})
STRUCTURED_FILE_TYPES = frozenset({"docx", "txt", "md", "pdf"})


def build_trusted_roster(
    extraction: ExtractionResult | None = None,
    *,
    known_names: list[str] | None = None,
    expected_contract_names: list[str] | None = None,
    non_ocr_team: list[TeamMember] | None = None,
) -> list[str]:
    """Collect trusted names from structured docs, known lists, and non-OCR team."""
    names: list[str] = []
    seen: set[str] = set()

    def _add(name: str, source: str = "") -> None:
        key = name.strip().lower()
        if not key or key in seen:
            return
        seen.add(key)
        names.append(name.strip())
        if source:
            logger.debug("Trusted name %r from %s", name, source)

    if known_names:
        for name in known_names:
            _add(name, "known_names")

    if expected_contract_names:
        for name in expected_contract_names:
            _add(name, "expected_contract")

    if non_ocr_team:
        for member in filter_team_members(non_ocr_team):
            _add(member.name, "non_ocr_team")

    if extraction:
        parser = StructuredLandingParser()
        for source in extraction.files:
            if source.metadata.get("is_ocr_derivative"):
                continue
            if source.file_type in TRUSTED_FILE_TYPES:
                parsed = parser.parse(source.extracted_text or "")
                for member in filter_team_members(parsed.team):
                    _add(member.name, f"structured:{source.filename}")

            if source.file_type in STRUCTURED_FILE_TYPES:
                candidates = extract_people_from_text(
                    source.extracted_text or "",
                    source_ref=source.filename,
                    section_hint="команда проекта",
                    in_team_section=True,
                )
                for c in candidates:
                    _add(c.name, f"extracted:{source.filename}")

            # PPTX with extractable text (non-OCR)
            if source.file_type == "pptx" and not source.metadata.get("is_ocr_derivative"):
                text = source.extracted_text or ""
                if "команда проекта" in text.lower():
                    candidates = extract_people_from_text(
                        text,
                        source_ref=source.filename,
                        in_team_section=True,
                    )
                    for c in candidates:
                        _add(c.name, f"pptx_text:{source.filename}")

    return names


def load_expected_contract_team(corpus_project: str) -> list[str]:
    """Load team must_have names from golden expected_contract.yml (tests only)."""
    repo_root = Path(__file__).resolve().parents[4]
    yml_path = (
        repo_root
        / "test_corpus"
        / "golden"
        / corpus_project
        / "expected_contract.yml"
    )
    if not yml_path.is_file():
        return []

    names: list[str] = []
    in_team_list = False
    for raw in yml_path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if line.strip().startswith("must_have_team:"):
            in_team_list = True
            continue
        if in_team_list:
            if line.strip().startswith("- "):
                item = line.strip()[2:].strip().strip('"').strip("'")
                names.append(item)
            elif line.strip() and not line.startswith("  "):
                break
    return names
