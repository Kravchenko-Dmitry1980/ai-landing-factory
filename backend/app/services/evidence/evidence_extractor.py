"""Extract EvidenceItem list from ExtractionResult."""

from __future__ import annotations

import re
import uuid

from app.schemas.evidence import EvidenceItem, SourceInventoryItem
from app.schemas.extraction import ExtractionResult, FileExtraction
from app.services.contract_fidelity.pptx_team_markers import (
    slide_title_has_team_marker,
    text_has_team_markers,
)
from app.services.evidence.evidence_normalizer import (
    extract_dates,
    extract_keywords,
    normalize_text,
)
from app.services.evidence.field_candidates import classify_field_candidates
from app.services.evidence.people_extractor import extract_people_from_text
from app.services.evidence.technology_dictionary import extract_technologies

SLIDE_SPLIT_RE = re.compile(r"(?:^|\n)(Slide\s+\d+\s*:)", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6}\s+.+|[А-ЯЁA-Z][А-ЯЁA-Z\s\-]{3,50})$", re.MULTILINE)
PAGE_SPLIT_RE = re.compile(r"(?:^|\n)(Страница\s+\d+\s*:|Page\s+\d+\s*:)", re.IGNORECASE)


class EvidenceExtractor:
    """Turn each file into location-aware evidence items."""

    def extract(
        self,
        extraction: ExtractionResult,
        inventory: list[SourceInventoryItem],
    ) -> list[EvidenceItem]:
        inv_by_filename = {s.filename: s for s in inventory}
        items: list[EvidenceItem] = []
        for file_rec in extraction.files:
            text = (file_rec.extracted_text or "").strip()
            if not text:
                continue
            inv = inv_by_filename.get(file_rec.filename)
            source_id = inv.source_id if inv else f"src-{file_rec.filename}"
            items.extend(self._extract_file(source_id, file_rec, text))
        return items

    def _extract_file(
        self,
        source_id: str,
        file_rec: FileExtraction,
        text: str,
    ) -> list[EvidenceItem]:
        ft = file_rec.file_type
        if ft == "pptx" or SLIDE_SPLIT_RE.search(text):
            return self._extract_slides(source_id, file_rec, text)
        if ft == "pdf" or PAGE_SPLIT_RE.search(text):
            return self._extract_pages(source_id, file_rec, text)
        if ft in ("docx", "doc"):
            return self._extract_sections(source_id, file_rec, text)
        return self._extract_paragraphs(source_id, file_rec, text)

    def _extract_slides(
        self,
        source_id: str,
        file_rec: FileExtraction,
        text: str,
    ) -> list[EvidenceItem]:
        parts = SLIDE_SPLIT_RE.split(text)
        items: list[EvidenceItem] = []
        i = 1
        while i < len(parts):
            header = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            match = re.search(r"(\d+)", header)
            idx = int(match.group(1)) if match else len(items) + 1
            slide_text = f"{header}\n{body}".strip()
            title = _slide_title(slide_text)
            in_team = slide_title_has_team_marker(title, slide_text) or text_has_team_markers(
                slide_text
            )
            items.append(
                self._make_item(
                    source_id, file_rec, slide_text,
                    location_type="slide",
                    location_index=idx,
                    location_label=title,
                    section_hint=title if in_team else None,
                    in_team_section=in_team,
                )
            )
            i += 2
        if not items and text.strip():
            items.append(
                self._make_item(
                    source_id, file_rec, text,
                    location_type="slide", location_index=1,
                )
            )
        return items

    def _extract_pages(
        self,
        source_id: str,
        file_rec: FileExtraction,
        text: str,
    ) -> list[EvidenceItem]:
        parts = PAGE_SPLIT_RE.split(text)
        if len(parts) <= 1:
            return self._extract_paragraphs(source_id, file_rec, text, location_type="page")
        items: list[EvidenceItem] = []
        i = 1
        while i < len(parts):
            header = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            match = re.search(r"(\d+)", header)
            idx = int(match.group(1)) if match else len(items) + 1
            items.append(
                self._make_item(
                    source_id, file_rec, f"{header}\n{body}".strip(),
                    location_type="page", location_index=idx,
                )
            )
            i += 2
        return items

    def _extract_sections(
        self,
        source_id: str,
        file_rec: FileExtraction,
        text: str,
    ) -> list[EvidenceItem]:
        lines = text.splitlines()
        sections: list[tuple[str, list[str]]] = []
        current_title = ""
        current_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            is_heading = (
                stripped.startswith("#")
                or (len(stripped) < 80 and HEADING_RE.match(stripped + "\n"))
                or stripped.lower() in {
                    "суть проекта", "задачи проекта", "для чего",
                    "вводные данные", "выходные данные", "результаты проекта",
                    "перспектива развития", "используемый технологический стек",
                    "команда проекта",
                }
            )
            if is_heading and current_lines:
                sections.append((current_title, current_lines))
                current_title = stripped.lstrip("#").strip()
                current_lines = []
            elif is_heading:
                current_title = stripped.lstrip("#").strip()
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_title, current_lines))

        if not sections:
            return self._extract_paragraphs(source_id, file_rec, text, location_type="section")

        items: list[EvidenceItem] = []
        for idx, (title, body_lines) in enumerate(sections, start=1):
            body = "\n".join(body_lines).strip()
            if not body and not title:
                continue
            block = f"{title}\n{body}".strip() if title else body
            items.append(
                self._make_item(
                    source_id, file_rec, block,
                    location_type="section",
                    location_index=idx,
                    location_label=title or None,
                    section_hint=title or None,
                )
            )
        return items

    def _extract_paragraphs(
        self,
        source_id: str,
        file_rec: FileExtraction,
        text: str,
        *,
        location_type: str = "paragraph",
    ) -> list[EvidenceItem]:
        blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
        if len(blocks) <= 1 and len(text) > 400:
            blocks = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 40]
        items: list[EvidenceItem] = []
        for idx, block in enumerate(blocks, start=1):
            if len(block) < 15:
                continue
            items.append(
                self._make_item(
                    source_id, file_rec, block,
                    location_type=location_type,
                    location_index=idx,
                )
            )
        if not items and text.strip():
            items.append(
                self._make_item(
                    source_id, file_rec, text,
                    location_type=location_type, location_index=1,
                )
            )
        return items

    def _make_item(
        self,
        source_id: str,
        file_rec: FileExtraction,
        text: str,
        *,
        location_type: str,
        location_index: int | None,
        location_label: str | None = None,
        section_hint: str | None = None,
        in_team_section: bool = False,
    ) -> EvidenceItem:
        normalized = normalize_text(text)
        technologies = extract_technologies(text)
        people = [
            m.name
            for m in extract_people_from_text(
                text,
                source_ref=file_rec.filename,
                section_hint=section_hint or location_label or "",
                in_team_section=in_team_section,
            )
        ]
        dates = extract_dates(text)
        item = EvidenceItem(
            evidence_id=f"ev-{uuid.uuid4().hex[:10]}",
            source_id=source_id,
            filename=file_rec.filename,
            file_type=file_rec.file_type,
            location_type=location_type,
            location_index=location_index,
            location_label=location_label,
            text=text,
            normalized_text=normalized,
            section_hint=section_hint or location_label,
            confidence=0.5 + min(len(normalized) / 2000, 0.4),
            technologies=technologies,
            people=people,
            dates=dates,
            keywords=extract_keywords(text),
        )
        item.field_candidates = classify_field_candidates(item)
        return item


def _slide_title(slide_text: str) -> str | None:
    lines = [ln.strip() for ln in slide_text.splitlines() if ln.strip()]
    if lines and re.match(r"Slide\s+\d+", lines[0], re.IGNORECASE):
        lines = lines[1:]
    for line in lines:
        if line.lower() in ("проект:", "проект"):
            continue
        if len(line) > 8 and not line.lower().startswith("сроки"):
            return line[:120]
    return lines[0][:120] if lines else None
