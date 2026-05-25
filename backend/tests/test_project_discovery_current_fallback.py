"""Tests for --current discovery with safe fallback to latest user project."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.services.diagnostics.last_project_tracker import write_last_project
from app.services.diagnostics.project_discovery import (
    NO_CURRENT_USER_PROJECT_HINT,
    ProjectDiscoveryError,
    resolve_project_id,
)


def _install_fake_client(monkeypatch, handler) -> None:
    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, params=None):
            return handler(url, params)

    monkeypatch.setattr("app.services.diagnostics.project_discovery.httpx.Client", _FakeClient)


class _FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


@pytest.fixture
def runtime_root(tmp_path: Path) -> Path:
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    (runtime / "ports.json").write_text(
        json.dumps({"backend_url": "http://127.0.0.1:8010"}),
        encoding="utf-8",
    )
    return tmp_path


def _materials(source_count: int, filename: str = "deck.pptx") -> dict:
    if source_count <= 0:
        return {"source_count": 0, "evidence_count": 0, "sources": []}
    return {
        "source_count": source_count,
        "evidence_count": 3,
        "sources": [{"filename": filename}],
    }


def test_current_valid_user_project(runtime_root: Path, monkeypatch) -> None:
    current_id = str(uuid4())

    def handler(url: str, params=None):
        if url.endswith(f"/projects/{current_id}"):
            return _FakeResponse({"id": current_id, "name": "Current user deck"})
        if "evidence-report" in url:
            return _FakeResponse(_materials(1))
        return _FakeResponse({}, status_code=404)

    write_last_project(runtime_root, project_id=current_id, project_name="Current", source="upload")
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    _install_fake_client(monkeypatch, handler)

    resolved = resolve_project_id(
        current=True,
        base_url="http://127.0.0.1:8010",
        runtime_root=runtime_root,
    )
    assert resolved.project_id == current_id
    assert resolved.discovery_mode == "current"
    assert resolved.rejected_current is None
    assert resolved.source_count == 1


def test_current_empty_project_falls_back_to_latest(runtime_root: Path, monkeypatch) -> None:
    current_id = str(uuid4())
    latest_id = str(uuid4())

    def handler(url: str, params=None):
        if url.endswith("/api/v1/projects") and "evidence-report" not in url:
            return _FakeResponse([{"id": latest_id, "name": "Indlab live multifile"}])
        if url.endswith(f"/projects/{current_id}"):
            return _FakeResponse({"id": current_id, "name": "Empty draft"})
        if current_id in url and "evidence-report" in url:
            return _FakeResponse(_materials(0))
        if latest_id in url and "evidence-report" in url:
            return _FakeResponse(_materials(2, "02_landing.docx"))
        if latest_id in url and url.endswith(f"/projects/{latest_id}"):
            return _FakeResponse({"id": latest_id, "name": "Indlab live multifile"})
        return _FakeResponse({}, status_code=404)

    write_last_project(runtime_root, project_id=current_id, project_name="Empty", source="upload")
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    _install_fake_client(monkeypatch, handler)

    resolved = resolve_project_id(
        current=True,
        base_url="http://127.0.0.1:8010",
        runtime_root=runtime_root,
        data_dir=runtime_root / "data",
    )
    assert resolved.discovery_mode == "fallback_from_current"
    assert resolved.project_id == latest_id
    assert resolved.rejected_current is not None
    assert resolved.rejected_current.project_id == current_id
    assert resolved.source_count == 2


def test_current_technical_project_falls_back(runtime_root: Path, monkeypatch) -> None:
    current_id = str(uuid4())
    latest_id = str(uuid4())

    def handler(url: str, params=None):
        if url.endswith("/api/v1/projects") and "evidence-report" not in url:
            return _FakeResponse([{"id": latest_id, "name": "Indlab live multifile"}])
        if url.endswith(f"/projects/{current_id}"):
            return _FakeResponse({"id": current_id, "name": "CORS dynamic port test"})
        if current_id in url and "evidence-report" in url:
            return _FakeResponse(_materials(0))
        if latest_id in url and "evidence-report" in url:
            return _FakeResponse(_materials(1))
        if latest_id in url and url.endswith(f"/projects/{latest_id}"):
            return _FakeResponse({"id": latest_id, "name": "Indlab live multifile"})
        return _FakeResponse({}, status_code=404)

    write_last_project(runtime_root, project_id=current_id, project_name="CORS", source="test")
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    _install_fake_client(monkeypatch, handler)

    resolved = resolve_project_id(
        current=True,
        base_url="http://127.0.0.1:8010",
        runtime_root=runtime_root,
        data_dir=runtime_root / "data",
    )
    assert resolved.discovery_mode == "fallback_from_current"
    assert resolved.project_id == latest_id


def test_current_missing_falls_back_to_latest(runtime_root: Path, monkeypatch) -> None:
    latest_id = str(uuid4())

    def handler(url: str, params=None):
        if url.endswith("/api/v1/projects") and "evidence-report" not in url:
            return _FakeResponse([{"id": latest_id, "name": "Indlab live multifile"}])
        if latest_id in url and "evidence-report" in url:
            return _FakeResponse(_materials(2))
        if latest_id in url and url.endswith(f"/projects/{latest_id}"):
            return _FakeResponse({"id": latest_id, "name": "Indlab live multifile"})
        return _FakeResponse({}, status_code=404)

    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    _install_fake_client(monkeypatch, handler)

    resolved = resolve_project_id(
        current=True,
        base_url="http://127.0.0.1:8010",
        runtime_root=runtime_root,
        data_dir=runtime_root / "data",
    )
    assert resolved.discovery_mode == "latest"
    assert resolved.project_id == latest_id
    assert any("last_project.json" in line for line in resolved.warnings)


def test_current_invalid_uuid_falls_back(runtime_root: Path, monkeypatch) -> None:
    current_id = str(uuid4())
    latest_id = str(uuid4())

    def handler(url: str, params=None):
        if url.endswith("/api/v1/projects") and "evidence-report" not in url:
            return _FakeResponse([{"id": latest_id, "name": "Indlab live multifile"}])
        if url.endswith(f"/projects/{current_id}"):
            return _FakeResponse({}, status_code=404)
        if latest_id in url and "evidence-report" in url:
            return _FakeResponse(_materials(2))
        if latest_id in url and url.endswith(f"/projects/{latest_id}"):
            return _FakeResponse({"id": latest_id, "name": "Indlab live multifile"})
        return _FakeResponse({}, status_code=404)

    write_last_project(runtime_root, project_id=current_id, project_name="Missing", source="upload")
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    _install_fake_client(monkeypatch, handler)

    resolved = resolve_project_id(
        current=True,
        base_url="http://127.0.0.1:8010",
        runtime_root=runtime_root,
        data_dir=runtime_root / "data",
    )
    assert resolved.discovery_mode == "fallback_from_current"
    assert resolved.project_id == latest_id


def test_current_and_latest_user_missing_raises(runtime_root: Path, monkeypatch) -> None:
    current_id = str(uuid4())
    cors_id = str(uuid4())

    def handler(url: str, params=None):
        if url.endswith("/api/v1/projects") and "evidence-report" not in url:
            return _FakeResponse([{"id": cors_id, "name": "CORS dynamic port test"}])
        if url.endswith(f"/projects/{current_id}"):
            return _FakeResponse({"id": current_id, "name": "Empty draft"})
        if "evidence-report" in url:
            return _FakeResponse(_materials(0))
        return _FakeResponse({}, status_code=404)

    write_last_project(runtime_root, project_id=current_id, project_name="Empty", source="upload")
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    _install_fake_client(monkeypatch, handler)

    with pytest.raises(ProjectDiscoveryError, match=NO_CURRENT_USER_PROJECT_HINT):
        resolve_project_id(
            current=True,
            base_url="http://127.0.0.1:8010",
            runtime_root=runtime_root,
            data_dir=runtime_root / "data",
        )
