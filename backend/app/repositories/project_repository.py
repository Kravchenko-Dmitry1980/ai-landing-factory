import json
import logging
from uuid import UUID

import aiofiles

from app.config import Settings
from app.models.domain import ProjectRecord, utc_now

logger = logging.getLogger(__name__)


class ProjectRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._index_path = settings.data_dir / "projects.json"

    async def _load(self) -> dict[str, dict]:
        if not self._index_path.exists():
            return {}
        async with aiofiles.open(self._index_path, encoding="utf-8") as f:
            raw = await f.read()
        return json.loads(raw) if raw else {}

    async def _save(self, data: dict[str, dict]) -> None:
        self._settings.data_dir.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(self._index_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))

    async def create(self, name: str, description: str | None) -> ProjectRecord:
        record = ProjectRecord(name=name, description=description, created_at=utc_now())
        data = await self._load()
        data[str(record.id)] = {
            "id": str(record.id),
            "name": record.name,
            "description": record.description,
            "created_at": record.created_at.isoformat(),
        }
        await self._save(data)
        return record

    async def get(self, project_id: UUID) -> ProjectRecord | None:
        data = await self._load()
        item = data.get(str(project_id))
        if not item:
            return None
        from datetime import datetime

        return ProjectRecord(
            id=UUID(item["id"]),
            name=item["name"],
            description=item.get("description"),
            created_at=datetime.fromisoformat(item["created_at"]),
        )
