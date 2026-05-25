import re
from pathlib import Path

from app.schemas.extraction import ExtractionPayload, FileExtraction
from app.schemas.upload import FileKind, UploadedFileMeta

MAX_RAW_NOTE_CHARS = 8000
ESSENCE_MAX_CHARS = 600

BULLET_RE = re.compile(r"^[\s]*(?:[-•*]|\d+[.)])\s+(.+)$", re.MULTILINE)
SECTION_RE = re.compile(
    r"^(?:#+\s*|[\d.]+\s+)?(суть|задач[аи]|цел[ьи]|команда|стек|результат|вводн|выходн|перспектив)",
    re.IGNORECASE | re.MULTILINE,
)


def normalize_extension(path: Path) -> str:
    return path.suffix.lower().lstrip(".")


def file_type_label(path: Path, kind: FileKind | None = None) -> str:
    if kind is not None:
        return kind.value
    ext = normalize_extension(path)
    return ext or "other"


def combine_plain_text(file_records: list[FileExtraction]) -> str:
    """Plain text only — used for essence/tasks heuristics."""
    return "\n\n".join(
        rec.extracted_text.strip()
        for rec in file_records
        if rec.extracted_text.strip()
    )


def aggregate_extracted_text(file_records: list[FileExtraction]) -> str:
    """Annotated merge for raw_notes / audit trail."""
    parts: list[str] = []
    for rec in file_records:
        if rec.extracted_text.strip():
            parts.append(f"--- {rec.filename} ---\n{rec.extracted_text.strip()}")
    return "\n\n".join(parts)


def _first_paragraph(text: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    return blocks[0] if blocks else text.strip()


def _bullet_lines(text: str, limit: int = 8) -> list[str]:
    items = BULLET_RE.findall(text)
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        line = item.strip()
        if line and line not in seen:
            seen.add(line)
            out.append(line)
        if len(out) >= limit:
            break
    return out


def build_payload_from_extractions(
    file_records: list[FileExtraction],
    uploads: list[UploadedFileMeta],
) -> ExtractionPayload:
    """
    Map aggregated extracted_text → ExtractionPayload (no LLM).
    """
    combined = combine_plain_text(file_records)
    annotated = aggregate_extracted_text(file_records)
    visual_assets = [
        m.original_name
        for m in uploads
        if m.kind in (FileKind.IMAGE, FileKind.SCREENSHOT)
    ]

    if not combined.strip():
        names = ", ".join(m.original_name for m in uploads) or "без файлов"
        return ExtractionPayload(
            client="Заказчик (уточнить)",
            goals=["Сформулировать цели на основе материалов"],
            essence=f"Материалы загружены ({names}), текст не извлечён",
            tasks=["Дополнить проект текстовыми материалами"],
            purpose="Презентовать проект заинтересованным сторонам",
            inputs=["Исходные материалы проекта"],
            outputs=["Лендинг проекта"],
            results=["Структурированное описание проекта"],
            presentation_style="minimal",
            visual_assets=visual_assets,
            raw_notes=[f"Файлы: {names}"],
        )

    essence_block = _first_paragraph(combined)
    essence = essence_block[:ESSENCE_MAX_CHARS]
    bullets = _bullet_lines(combined)
    first_line = combined.strip().splitlines()[0][:120] if combined.strip() else None

    return ExtractionPayload(
        client=None,
        goals=bullets[:3] if bullets else ["Достичь целей проекта из материалов"],
        essence=essence,
        tasks=bullets[:6] if bullets else ["Реализовать ключевые задачи проекта"],
        purpose=essence_block[:300] if len(essence_block) > 50 else "Презентация проекта и результатов",
        inputs=bullets[6:10] or ["Материалы и вводные из загруженных документов"],
        outputs=["Лендинг проекта", "Единый LandingContract"],
        results=bullets[3:6] or ["Описание результатов из материалов проекта"],
        tech_stack=[],
        team=[],
        outlook=essence_block[-400:] if len(essence_block) > 400 else None,
        tagline=first_line if first_line and len(first_line) < 100 else essence[:80],
        presentation_style="minimal",
        visual_assets=visual_assets,
        raw_notes=[(annotated or combined)[:MAX_RAW_NOTE_CHARS]],
    )
