import json
import logging
from datetime import datetime
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

    @staticmethod
    def _parse_record(item: dict) -> ProjectRecord:
        created = datetime.fromisoformat(item["created_at"])
        updated_raw = item.get("updated_at") or item["created_at"]
        updated = datetime.fromisoformat(updated_raw)
        return ProjectRecord(
            id=UUID(item["id"]),
            name=item["name"],
            description=item.get("description"),
            created_at=created,
            updated_at=updated,
        )

    async def create(self, name: str, description: str | None) -> ProjectRecord:
        record = ProjectRecord(name=name, description=description, created_at=utc_now())
        record.updated_at = record.created_at
        data = await self._load()
        data[str(record.id)] = {
            "id": str(record.id),
            "name": record.name,
            "description": record.description,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }
        await self._save(data)
        return record

    async def touch(self, project_id: UUID) -> None:
        data = await self._load()
        key = str(project_id)
        if key not in data:
            return
        data[key]["updated_at"] = utc_now().isoformat()
        await self._save(data)

    async def get(self, project_id: UUID) -> ProjectRecord | None:
        data = await self._load()
        item = data.get(str(project_id))
        if not item:
            return None
        return self._parse_record(item)

    async def list_projects(
        self,
        *,
        limit: int = 50,
        sort: str = "updated_desc",
    ) -> list[ProjectRecord]:
        data = await self._load()
        records = [self._parse_record(item) for item in data.values()]
        reverse = sort in ("updated_desc", "created_desc")
        key_name = "updated_at" if "updated" in sort else "created_at"

        def _key(rec: ProjectRecord) -> datetime:
            return rec.updated_at if key_name == "updated_at" else rec.created_at

        records.sort(key=_key, reverse=reverse)
        if limit > 0:
            records = records[:limit]
        return records
