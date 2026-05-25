"""Persist last touched project for CLI --current discovery."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)

LAST_PROJECT_FILE = "last_project.json"


def repo_runtime_dir(runtime_root: Path) -> Path:
    return runtime_root / ".runtime"


def read_ports(runtime_root: Path) -> dict[str, Any]:
    path = repo_runtime_dir(runtime_root) / "ports.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_last_project(
    runtime_root: Path,
    *,
    project_id: UUID | str,
    project_name: str,
    source: str,
    backend_url: str | None = None,
    frontend_url: str | None = None,
) -> None:
    """Write .runtime/last_project.json (gitignored)."""
    ports = read_ports(runtime_root)
    backend = (backend_url or ports.get("backend_url") or "http://127.0.0.1:8001").rstrip("/")
    frontend = (frontend_url or ports.get("frontend_url") or "http://localhost:3000").rstrip("/")
    pid = str(project_id)
    now = datetime.now(timezone.utc).isoformat()

    runtime_dir = repo_runtime_dir(runtime_root)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    path = runtime_dir / LAST_PROJECT_FILE

    existing: dict[str, Any] = {}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}

    payload = {
        "project_id": pid,
        "project_name": project_name,
        "backend_url": backend,
        "frontend_url": frontend,
        "editor_url": f"{frontend}/editor/{pid}",
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
        "source": source,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Updated last project tracker: %s (%s)", pid, source)
