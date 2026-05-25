from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ProjectRecord:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str | None = None
    created_at: datetime = field(default_factory=utc_now)
