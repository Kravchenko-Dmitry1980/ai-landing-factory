"""Resolve project_id and backend_url for live diagnostic CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.services.diagnostics.last_project_tracker import (
    LAST_PROJECT_FILE,
    repo_runtime_dir,
)

DEFAULT_BACKEND_URL = "http://127.0.0.1:8001"
BACKEND_UNAVAILABLE_HINT = "Backend unavailable. Run .\\scripts\\start_dev.ps1"


@dataclass
class ResolvedProject:
    project_id: str
    backend_url: str
    source: str
    project_name: str | None = None


class ProjectDiscoveryError(Exception):
    """User-facing project resolution failure."""


def default_runtime_root() -> Path:
    """Repo root (Lend/) from backend package layout."""
    return Path(__file__).resolve().parents[4]


def get_backend_url_from_runtime(runtime_root: Path | None = None) -> str:
    root = runtime_root or default_runtime_root()
    path = repo_runtime_dir(root) / "ports.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            url = data.get("backend_url")
            if url:
                return str(url).rstrip("/")
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_BACKEND_URL


def get_project_id_from_runtime(runtime_root: Path | None = None) -> str | None:
    root = runtime_root or default_runtime_root()
    path = repo_runtime_dir(root) / LAST_PROJECT_FILE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        pid = data.get("project_id")
        return str(pid) if pid else None
    except (json.JSONDecodeError, OSError):
        return None


def check_backend_available(backend_url: str, timeout: float = 5.0) -> bool:
    base = backend_url.rstrip("/")
    probe_urls = (
        f"{base}/api/v1/projects/privacy",
        f"{base}/docs",
        f"{base}/api/v1/projects?limit=1",
    )
    try:
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            for url in probe_urls:
                try:
                    resp = client.get(url)
                    if resp.status_code < 500:
                        return True
                except httpx.HTTPError:
                    continue
    except httpx.HTTPError:
        return False
    return False


def get_latest_project_id(
    base_url: str,
    *,
    data_dir: Path | None = None,
    timeout: float = 30.0,
) -> tuple[str, str | None]:
    """Return (project_id, project_name) from API or filesystem fallback."""
    api = f"{base_url.rstrip('/')}/api/v1/projects"
    try:
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            resp = client.get(api, params={"limit": 1, "sort": "updated_desc"})
            if resp.status_code == 200:
                items = resp.json()
                if items:
                    item = items[0]
                    return str(item["id"]), item.get("name")
    except httpx.HTTPError:
        pass

    if data_dir is not None:
        pid = _latest_from_filesystem(data_dir)
        if pid:
            return pid, None

    raise ProjectDiscoveryError("No projects found. Create a project via UI upload first.")


def _latest_from_filesystem(data_dir: Path) -> str | None:
    index = data_dir / "projects.json"
    if not index.is_file():
        return None
    try:
        raw = json.loads(index.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not raw:
        return None

    def _sort_key(item: dict[str, Any]) -> datetime:
        for field in ("updated_at", "created_at"):
            value = item.get(field)
            if value:
                try:
                    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue
        return datetime.min.replace(tzinfo=timezone.utc)

    best_id = max(raw.items(), key=lambda kv: _sort_key(kv[1]))[0]
    return best_id


def resolve_project_id(
    *,
    project_id: str | None = None,
    latest: bool = False,
    current: bool = False,
    base_url: str | None = None,
    runtime_root: Path | None = None,
    data_dir: Path | None = None,
) -> ResolvedProject:
    root = runtime_root or default_runtime_root()
    backend = (base_url or get_backend_url_from_runtime(root)).rstrip("/")

    if not check_backend_available(backend):
        raise ProjectDiscoveryError(BACKEND_UNAVAILABLE_HINT)

    if project_id:
        return ResolvedProject(
            project_id=project_id.strip(),
            backend_url=backend,
            source="explicit",
        )

    if latest:
        pid, name = get_latest_project_id(backend, data_dir=data_dir)
        return ResolvedProject(
            project_id=pid,
            backend_url=backend,
            source="latest",
            project_name=name,
        )

    if current:
        runtime_pid = get_project_id_from_runtime(root)
        if runtime_pid:
            return ResolvedProject(
                project_id=runtime_pid,
                backend_url=backend,
                source="current",
            )
        pid, name = get_latest_project_id(backend, data_dir=data_dir)
        return ResolvedProject(
            project_id=pid,
            backend_url=backend,
            source="latest_fallback",
            project_name=name,
        )

    raise ProjectDiscoveryError(
        "Укажите --project-id UUID, --latest или --current. "
        "Пример: python scripts/check_live_project_verdict.py --latest"
    )
