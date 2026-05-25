import json
import logging
from pathlib import Path
from uuid import UUID, uuid4

import aiofiles

from app.config import Settings
from app.schemas.upload import FileKind, UploadedFileMeta
from app.models.domain import utc_now

logger = logging.getLogger(__name__)

EXTENSION_KIND: dict[str, FileKind] = {
    ".pdf": FileKind.PDF,
    ".docx": FileKind.DOCX,
    ".pptx": FileKind.PPTX,
    ".png": FileKind.IMAGE,
    ".jpg": FileKind.IMAGE,
    ".jpeg": FileKind.IMAGE,
    ".webp": FileKind.IMAGE,
    ".gif": FileKind.IMAGE,
    ".txt": FileKind.TEXT,
    ".md": FileKind.TEXT,
}


class FileStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _project_dir(self, project_id: UUID) -> Path:
        path = self._settings.uploads_dir / str(project_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def resolve_path(self, project_id: UUID, stored_name: str) -> Path:
        return self._project_dir(project_id) / stored_name

    def _meta_path(self, project_id: UUID) -> Path:
        return self._project_dir(project_id) / "files.json"

    @staticmethod
    def detect_kind(filename: str) -> FileKind:
        ext = Path(filename).suffix.lower()
        if "screenshot" in filename.lower():
            return FileKind.SCREENSHOT
        return EXTENSION_KIND.get(ext, FileKind.OTHER)

    async def save_upload(
        self,
        project_id: UUID,
        filename: str,
        content: bytes,
        mime_type: str | None,
    ) -> UploadedFileMeta:
        file_id = uuid4()
        stored_name = f"{file_id}_{Path(filename).name}"
        dest = self._project_dir(project_id) / stored_name

        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)

        meta = UploadedFileMeta(
            id=file_id,
            project_id=project_id,
            original_name=filename,
            stored_name=stored_name,
            kind=self.detect_kind(filename),
            mime_type=mime_type,
            size_bytes=len(content),
            uploaded_at=utc_now(),
        )
        await self._append_meta(project_id, meta)
        logger.info("Saved upload %s for project %s", filename, project_id)
        return meta

    async def _append_meta(self, project_id: UUID, meta: UploadedFileMeta) -> None:
        existing = await self.list_files(project_id)
        existing.append(meta)
        payload = [m.model_dump(mode="json") for m in existing]
        async with aiofiles.open(self._meta_path(project_id), "w", encoding="utf-8") as f:
            await f.write(json.dumps(payload, ensure_ascii=False, indent=2))

    async def list_files(self, project_id: UUID) -> list[UploadedFileMeta]:
        path = self._meta_path(project_id)
        if not path.exists():
            return []
        async with aiofiles.open(path, encoding="utf-8") as f:
            raw = await f.read()
        data = json.loads(raw) if raw else []
        return [UploadedFileMeta.model_validate(item) for item in data]

    async def read_text_hint(self, project_id: UUID) -> str:
        """Best-effort text for stub extraction from stored files."""
        parts: list[str] = []
        for meta in await self.list_files(project_id):
            parts.append(f"[{meta.kind.value}] {meta.original_name}")
            if meta.kind == FileKind.TEXT:
                path = self._project_dir(project_id) / meta.stored_name
                async with aiofiles.open(path, encoding="utf-8", errors="ignore") as f:
                    parts.append(await f.read())
        return "\n".join(parts)
