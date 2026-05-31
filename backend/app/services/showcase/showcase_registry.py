"""JSON-backed registry for showcases (Stage P.6).

Each showcase is stored as a single JSON file under
``<data_dir>/showcases/{showcase_id}.json``. This keeps the registry easy to
debug, migrate and delete without introducing a database or new dependencies.

The registry is intentionally synchronous (plain :mod:`pathlib` + :mod:`json`);
payloads are tiny and writes are atomic via a temp-file + ``os.replace``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings, settings as default_settings
from app.services.showcase.showcase_safety import sanitize_url
from app.services.showcase.showcase_schema import (
    ShowcaseConfig,
    ShowcaseCreateRequest,
    ShowcaseLayout,
    ShowcaseMode,
    ShowcaseProject,
    ShowcaseProjectCreateRequest,
    ShowcaseProjectUpdateRequest,
    ShowcaseSummary,
    ShowcaseTheme,
    ShowcaseUpdateRequest,
)

logger = logging.getLogger(__name__)

_MAX_TAGS = 10
_MAX_TAG_LEN = 40
_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


class ShowcaseNotFoundError(LookupError):
    """Raised when a showcase id does not exist in the registry."""


class ShowcaseProjectNotFoundError(LookupError):
    """Raised when a project id does not exist inside a showcase."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


def _sanitize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    cleaned: list[str] = []
    for raw in tags:
        if raw is None:
            continue
        tag = str(raw).strip()[:_MAX_TAG_LEN]
        if tag:
            cleaned.append(tag)
        if len(cleaned) >= _MAX_TAGS:
            break
    return cleaned


class ShowcaseRegistry:
    """Read/write showcase configs as individual JSON files."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        base_dir: Path | None = None,
    ) -> None:
        self._settings = settings or default_settings
        self._explicit_dir = Path(base_dir) if base_dir is not None else None

    # ----------------------------------------------------------------- paths

    @property
    def _dir(self) -> Path:
        if self._explicit_dir is not None:
            return self._explicit_dir
        return self._settings.data_dir / "showcases"

    def _path(self, showcase_id: str) -> Path:
        if not _ID_RE.match(showcase_id):
            raise ShowcaseNotFoundError(f"invalid showcase id: {showcase_id!r}")
        return self._dir / f"{showcase_id}.json"

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------ read/write

    def _read(self, showcase_id: str) -> ShowcaseConfig:
        path = self._path(showcase_id)
        if not path.is_file():
            raise ShowcaseNotFoundError(showcase_id)
        raw = path.read_text(encoding="utf-8")
        config = ShowcaseConfig.model_validate_json(raw)
        # Defensive: always present projects in stable order.
        config.projects.sort(key=lambda p: p.order_index)
        return config

    def _write(self, config: ShowcaseConfig) -> None:
        if not config.id:
            raise ValueError("ShowcaseConfig.id is required to persist")
        self._ensure_dir()
        path = self._path(config.id)
        tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
        tmp.write_text(
            config.model_dump_json(indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, path)

    # --------------------------------------------------------------- queries

    def list_showcases(self) -> list[ShowcaseConfig]:
        if not self._dir.exists():
            return []
        configs: list[ShowcaseConfig] = []
        for path in self._dir.glob("*.json"):
            try:
                config = ShowcaseConfig.model_validate_json(
                    path.read_text(encoding="utf-8")
                )
            except (ValueError, OSError) as exc:
                logger.warning("showcase: skipping unreadable file %s: %s", path, exc)
                continue
            config.projects.sort(key=lambda p: p.order_index)
            configs.append(config)
        configs.sort(key=lambda c: c.updated_at or "", reverse=True)
        return configs

    def list_summaries(self) -> list[ShowcaseSummary]:
        return [
            ShowcaseSummary(
                id=str(c.id),
                title=c.title,
                project_count=len(c.projects),
                updated_at=c.updated_at,
                created_at=c.created_at,
            )
            for c in self.list_showcases()
        ]

    def get_showcase(self, showcase_id: str) -> ShowcaseConfig:
        return self._read(showcase_id)

    # -------------------------------------------------------------- mutations

    def create_showcase(self, request: ShowcaseCreateRequest) -> ShowcaseConfig:
        now = _utc_now_iso()
        config = ShowcaseConfig(
            id=_new_id(),
            title=request.title.strip(),
            subtitle=(request.subtitle or None),
            organization=(request.organization or None),
            layout=request.layout,
            mode=request.mode,
            theme=request.theme,
            projects=[],
            created_at=now,
            updated_at=now,
        )
        self._write(config)
        logger.info("showcase: created %s (%s)", config.id, config.title)
        return config

    def update_showcase(
        self, showcase_id: str, request: ShowcaseUpdateRequest
    ) -> ShowcaseConfig:
        config = self._read(showcase_id)
        if request.title is not None:
            config.title = request.title.strip()
        if request.subtitle is not None:
            config.subtitle = request.subtitle.strip() or None
        if request.organization is not None:
            config.organization = request.organization.strip() or None
        if request.layout is not None:
            config.layout = request.layout
        if request.mode is not None:
            config.mode = request.mode
        if request.theme is not None:
            config.theme = request.theme
        config.updated_at = _utc_now_iso()
        self._write(config)
        return config

    def delete_showcase(self, showcase_id: str) -> bool:
        path = self._path(showcase_id)
        if not path.is_file():
            return False
        path.unlink()
        logger.info("showcase: deleted %s", showcase_id)
        return True

    # ---------------------------------------------------------- project CRUD

    def add_project(
        self, showcase_id: str, request: ShowcaseProjectCreateRequest
    ) -> ShowcaseConfig:
        config = self._read(showcase_id)
        next_index = (
            max((p.order_index for p in config.projects), default=-1) + 1
        )
        project = ShowcaseProject(
            id=_new_id(),
            title=request.title.strip(),
            description=(request.description or "").strip(),
            landing_url=sanitize_url(request.landing_url),
            demo_url=sanitize_url(request.demo_url),
            demo_label=(request.demo_label or None),
            category=(request.category or None),
            tags=_sanitize_tags(request.tags),
            accent=(request.accent or None),
            source_project_id=(request.source_project_id or None),
            order_index=next_index,
        )
        config.projects.append(project)
        config.updated_at = _utc_now_iso()
        self._write(config)
        return config

    def update_project(
        self,
        showcase_id: str,
        project_id: str,
        request: ShowcaseProjectUpdateRequest,
    ) -> ShowcaseConfig:
        config = self._read(showcase_id)
        project = self._find_project(config, project_id)
        fields = request.model_dump(exclude_unset=True)
        if "title" in fields and fields["title"] is not None:
            project.title = str(fields["title"]).strip()
        if "description" in fields:
            project.description = (fields["description"] or "").strip()
        if "landing_url" in fields:
            project.landing_url = sanitize_url(fields["landing_url"])
        if "demo_url" in fields:
            project.demo_url = sanitize_url(fields["demo_url"])
        if "demo_label" in fields:
            project.demo_label = (fields["demo_label"] or None)
        if "category" in fields:
            project.category = (fields["category"] or None)
        if "tags" in fields:
            project.tags = _sanitize_tags(fields["tags"])
        if "accent" in fields:
            project.accent = (fields["accent"] or None)
        if "source_project_id" in fields:
            project.source_project_id = (fields["source_project_id"] or None)
        config.updated_at = _utc_now_iso()
        self._write(config)
        return config

    def delete_project(self, showcase_id: str, project_id: str) -> ShowcaseConfig:
        config = self._read(showcase_id)
        before = len(config.projects)
        config.projects = [p for p in config.projects if p.id != project_id]
        if len(config.projects) == before:
            raise ShowcaseProjectNotFoundError(project_id)
        self._reindex(config)
        config.updated_at = _utc_now_iso()
        self._write(config)
        return config

    def reorder_projects(
        self, showcase_id: str, ordered_ids: list[str]
    ) -> ShowcaseConfig:
        config = self._read(showcase_id)
        by_id = {p.id: p for p in config.projects}
        seen: set[str] = set()
        reordered: list[ShowcaseProject] = []
        for pid in ordered_ids:
            project = by_id.get(pid)
            if project and pid not in seen:
                reordered.append(project)
                seen.add(pid)
        # Keep any project not mentioned in ordered_ids (defensive append).
        for project in config.projects:
            if project.id not in seen:
                reordered.append(project)
        config.projects = reordered
        self._reindex(config)
        config.updated_at = _utc_now_iso()
        self._write(config)
        return config

    # --------------------------------------------------------------- helpers

    @staticmethod
    def _find_project(config: ShowcaseConfig, project_id: str) -> ShowcaseProject:
        for project in config.projects:
            if project.id == project_id:
                return project
        raise ShowcaseProjectNotFoundError(project_id)

    @staticmethod
    def _reindex(config: ShowcaseConfig) -> None:
        for index, project in enumerate(config.projects):
            project.order_index = index


# Module-level default instance used by the API layer.
_registry = ShowcaseRegistry()


def get_showcase_registry() -> ShowcaseRegistry:
    return _registry
