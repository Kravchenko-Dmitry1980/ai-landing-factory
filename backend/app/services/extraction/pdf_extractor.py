import logging
from pathlib import Path

from pypdf import PdfReader

from app.schemas.extraction import FileExtraction
from app.services.extraction.base import FileExtractor
from app.services.extraction.utils import file_type_label, normalize_extension

logger = logging.getLogger(__name__)


class PdfExtractor(FileExtractor):
    def supports(self, path: Path) -> bool:
        return normalize_extension(path) == "pdf"

    def extract(self, path: Path, filename: str | None = None) -> FileExtraction:
        name = filename or path.name
        warnings: list[str] = []
        errors: list[str] = []

        try:
            reader = PdfReader(str(path))
            page_texts: list[str] = []
            empty_pages: list[int] = []

            for idx, page in enumerate(reader.pages, start=1):
                try:
                    raw = page.extract_text() or ""
                except Exception as page_exc:
                    warnings.append(f"Page {idx} extraction error: {page_exc}")
                    raw = ""
                if not raw.strip():
                    empty_pages.append(idx)
                page_texts.append(raw.strip())

            if empty_pages:
                warnings.append(
                    f"Empty or unreadable pages: {', '.join(map(str, empty_pages))}"
                )

            text = "\n\n".join(t for t in page_texts if t)
            if not text.strip():
                warnings.append("PDF contains no extractable text")

            metadata = {"pages_count": len(reader.pages)}
            return FileExtraction(
                filename=name,
                file_type=file_type_label(path),
                extracted_text=text,
                metadata=metadata,
                warnings=warnings,
                errors=errors,
            )
        except Exception as exc:
            logger.exception("PDF extraction failed: %s", path)
            return FileExtraction(
                filename=name,
                file_type=file_type_label(path),
                extracted_text="",
                metadata={},
                warnings=["PDF extraction failed"],
                errors=[str(exc)],
            )
