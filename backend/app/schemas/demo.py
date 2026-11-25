from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DemoInfo(BaseModel):
    """What the studio shows about the project's demo video."""

    has_draft: bool
    has_poster: bool
    # The intern link currently plays a video.
    on_link: bool
    # The link does not yet match the demo chosen in the studio.
    pending: bool
    updated_at: datetime | None = None


class PublicDemoMeta(BaseModel):
    """Enough for the share page to decide whether to show a player. No library data."""

    demo: bool
    poster: bool
    title: str
