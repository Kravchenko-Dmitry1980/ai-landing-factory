import logging
from pathlib import Path

from app.schemas.extraction import FileExtraction
from app.services.extraction.utils import file_type_label, normalize_extension

logger = logging.getLogger(__name__)


def extract_text_file(path: Path, filename: str | None = None) -> FileExtraction:
    """Plain text / markdown files."""
    name = filename or path.name
    warnings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            warnings.append("Text file is empty")
        return FileExtraction(
            filename=name,
            file_type=file_type_label(path),
            extracted_text=text,
            metadata={"chars_count": len(text)},
            warnings=warnings,
        )
    except Exception as exc:
        logger.exception("Text read failed: %s", path)
        return FileExtraction(
            filename=name,
            file_type=file_type_label(path),
            extracted_text="",
            metadata={},
            warnings=["Text file read failed"],
            errors=[str(exc)],
        )


def fallback_extract_file(path: Path, filename: str | None = None) -> FileExtraction:
    """
    Stub fallback for unknown or unsupported formats.
    Never raises — pipeline continues with warnings.
    """
    name = filename or path.name
    ext = normalize_extension(path)
    hint = f"[{ext or 'unknown'}] {name}"
    logger.info("Stub fallback for file: %s", name)
    return FileExtraction(
        filename=name,
        file_type=ext or "other",
        extracted_text="",
        metadata={"fallback": True, "stub": True},
        warnings=[f"No dedicated extractor for .{ext or 'unknown'}; filename preserved only"],
        errors=[],
    )
