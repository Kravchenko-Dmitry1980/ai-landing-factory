import asyncio
import logging
from pathlib import Path
from uuid import UUID

from app.models.domain import utc_now
from app.repositories.file_store import FileStore
from app.schemas.extraction import ExtractionResult, FileExtraction
from app.schemas.upload import FileKind
from app.services.extraction.base import DocumentExtractor, FileExtractor
from app.services.extraction.docx_extractor import DocxExtractor
from app.services.extraction.pdf_extractor import PdfExtractor
from app.services.extraction.pptx_extractor import PptxExtractor
from app.services.extraction.stub_extractor import extract_text_file, fallback_extract_file
from app.services.extraction.utils import build_payload_from_extractions, normalize_extension

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = {"txt", "md"}


class ExtractionDispatcher:
    """Routes a file path to the appropriate FileExtractor."""

    def __init__(self, extractors: list[FileExtractor] | None = None) -> None:
        self._extractors = extractors or [
            DocxExtractor(),
            PdfExtractor(),
            PptxExtractor(),
        ]

    def extract_file(self, path: Path, filename: str | None = None) -> FileExtraction:
        if not path.exists():
            return FileExtraction(
                filename=filename or path.name,
                file_type="missing",
                extracted_text="",
                warnings=["File not found on disk"],
                errors=[str(path)],
            )

        ext = normalize_extension(path)
        if ext in TEXT_EXTENSIONS:
            record = extract_text_file(path, filename)
            record.metadata["source_path"] = str(path.resolve())
            return record

        for extractor in self._extractors:
            if extractor.supports(path):
                record = extractor.extract(path, filename)
                record.metadata["source_path"] = str(path.resolve())
                return record

        record = fallback_extract_file(path, filename)
        record.metadata["source_path"] = str(path.resolve())
        return record


class DispatcherExtractionService(DocumentExtractor):
    """Project-level extraction using dispatcher + payload builder."""

    EXTRACTOR_VERSION = "dispatcher-0.2"

    def __init__(self, file_store: FileStore, dispatcher: ExtractionDispatcher | None = None) -> None:
        self._files = file_store
        self._dispatcher = dispatcher or ExtractionDispatcher()

    async def extract(self, project_id: UUID) -> ExtractionResult:
        uploads = await self._files.list_files(project_id)
        file_records: list[FileExtraction] = []

        for meta in uploads:
            path = self._files.resolve_path(project_id, meta.stored_name)
            record = await asyncio.to_thread(
                self._dispatcher.extract_file,
                path,
                meta.original_name,
            )
            if meta.kind in (FileKind.IMAGE, FileKind.SCREENSHOT) and not record.extracted_text:
                record.warnings.append("Image/screenshot: no OCR (text not extracted)")
            file_records.append(record)

        payload = build_payload_from_extractions(file_records, uploads)
        logger.info(
            "Dispatcher extraction completed for %s (%d files)",
            project_id,
            len(file_records),
        )
        return ExtractionResult(
            project_id=project_id,
            payload=payload,
            files=file_records,
            source_file_ids=[f.id for f in uploads],
            extracted_at=utc_now(),
            extractor_version=self.EXTRACTOR_VERSION,
        )
