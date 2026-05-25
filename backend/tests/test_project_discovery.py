"""Tests for project discovery and runtime resolution."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.config import Settings
from app.models.domain import utc_now
from app.repositories.project_repository import ProjectRepository
from app.services.diagnostics.last_project_tracker import write_last_project
from app.services.diagnostics.project_discovery import (
    ProjectDiscoveryError,
    get_backend_url_from_runtime,
    get_project_id_from_runtime,
    resolve_project_id,
)


@pytest.fixture
def runtime_root(tmp_path: Path) -> Path:
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    (runtime / "ports.json").write_text(
        json.dumps({"backend_url": "http://127.0.0.1:8010"}),
        encoding="utf-8",
    )
    return tmp_path


def test_get_backend_url_from_runtime(runtime_root: Path) -> None:
    assert get_backend_url_from_runtime(runtime_root) == "http://127.0.0.1:8010"


def test_get_backend_url_fallback(tmp_path: Path) -> None:
    assert get_backend_url_from_runtime(tmp_path) == "http://127.0.0.1:8001"


def test_get_project_id_from_runtime(runtime_root: Path) -> None:
    pid = str(uuid4())
    write_last_project(
        runtime_root,
        project_id=pid,
        project_name="Demo",
        source="upload",
    )
    assert get_project_id_from_runtime(runtime_root) == pid


@pytest.mark.asyncio
async def test_list_projects_newest_first(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    settings = Settings(data_dir=data_dir)
    repo = ProjectRepository(settings)

    older = await repo.create("Older", None)
    newer = await repo.create("Newer", None)
    await repo.touch(newer.id)

    items = await repo.list_projects(limit=1, sort="updated_desc")
    assert len(items) == 1
    assert items[0].id == newer.id
    assert items[0].name == "Newer"
    assert older.id != items[0].id


def test_resolve_explicit_project_id(monkeypatch, runtime_root: Path) -> None:
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    resolved = resolve_project_id(
        project_id="55a98f90-73fc-4d26-a477-3c974a0cbeed",
        base_url="http://127.0.0.1:8010",
        runtime_root=runtime_root,
    )
    assert resolved.project_id == "55a98f90-73fc-4d26-a477-3c974a0cbeed"
    assert resolved.source == "explicit"


def test_resolve_current_reads_runtime(monkeypatch, runtime_root: Path) -> None:
    pid = str(uuid4())
    write_last_project(runtime_root, project_id=pid, project_name="X", source="upload")
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    resolved = resolve_project_id(
        current=True,
        base_url="http://127.0.0.1:8010",
        runtime_root=runtime_root,
    )
    assert resolved.project_id == pid
    assert resolved.source == "current"


def test_resolve_latest_via_api(monkeypatch, runtime_root: Path, tmp_path: Path) -> None:
    latest_id = str(uuid4())

    class _FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return [{"id": latest_id, "name": "Latest"}]

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, params=None):
            return _FakeResponse()

    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    monkeypatch.setattr("app.services.diagnostics.project_discovery.httpx.Client", _FakeClient)

    resolved = resolve_project_id(
        latest=True,
        base_url="http://127.0.0.1:8010",
        runtime_root=runtime_root,
        data_dir=tmp_path / "data",
    )
    assert resolved.project_id == latest_id
    assert resolved.source == "latest"
    assert resolved.project_name == "Latest"


def test_resolve_missing_mode_raises(monkeypatch, runtime_root: Path) -> None:
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    with pytest.raises(ProjectDiscoveryError, match="--latest"):
        resolve_project_id(base_url="http://127.0.0.1:8010", runtime_root=runtime_root)


def test_backend_unavailable(monkeypatch, runtime_root: Path) -> None:
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: False,
    )
    with pytest.raises(ProjectDiscoveryError, match="start_dev"):
        resolve_project_id(
            latest=True,
            base_url="http://127.0.0.1:8010",
            runtime_root=runtime_root,
        )


def test_filesystem_latest_fallback(tmp_path: Path) -> None:
    from app.services.diagnostics.project_discovery import _latest_from_filesystem

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    pid_old = str(uuid4())
    pid_new = str(uuid4())
    older = "2020-01-01T00:00:00+00:00"
    now = "2026-05-25T12:00:00+00:00"
    index = {
        pid_old: {"id": pid_old, "name": "A", "created_at": older, "updated_at": older},
        pid_new: {"id": pid_new, "name": "B", "created_at": now, "updated_at": now},
    }
    (data_dir / "projects.json").write_text(json.dumps(index), encoding="utf-8")
    assert _latest_from_filesystem(data_dir) == pid_new
