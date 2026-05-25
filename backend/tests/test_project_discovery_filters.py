"""Tests for user-project filtering in project discovery."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.services.diagnostics.project_discovery import (
    ProjectDiscoveryError,
    ProjectMaterialSummary,
    is_technical_project_name,
    is_user_project_candidate,
    resolve_project_id,
)


def test_cors_dynamic_port_test_name_is_technical() -> None:
    assert is_technical_project_name("CORS dynamic port test") is True


def test_real_project_name_is_not_technical() -> None:
    assert is_technical_project_name("Proekt-Intellektualnyj-agregator") is False
    assert is_technical_project_name("Latest user deck") is False


def test_cors_empty_project_rejected() -> None:
    summary = ProjectMaterialSummary(
        project_id="x",
        project_name="CORS dynamic port test",
        source_count=0,
    )
    assert is_user_project_candidate(summary) is False


def test_empty_non_technical_project_rejected() -> None:
    summary = ProjectMaterialSummary(
        project_id="x",
        project_name="Empty draft",
        source_count=0,
    )
    assert is_user_project_candidate(summary) is False


def test_real_project_with_source_accepted() -> None:
    summary = ProjectMaterialSummary(
        project_id="x",
        project_name="Indlab",
        source_count=1,
        filenames=["project.pptx"],
    )
    assert is_user_project_candidate(summary) is True


def test_latest_skips_technical_and_picks_user_project(monkeypatch, tmp_path) -> None:
    cors_id = str(uuid4())
    real_id = str(uuid4())

    class _FakeResponse:
        def __init__(self, payload, status_code: int = 200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, params=None):
            if url.endswith("/api/v1/projects"):
                return _FakeResponse(
                    [
                        {"id": cors_id, "name": "CORS dynamic port test"},
                        {"id": real_id, "name": "Indlab presentation"},
                    ]
                )
            if url.endswith(f"/projects/{cors_id}"):
                return _FakeResponse({"id": cors_id, "name": "CORS dynamic port test"})
            if url.endswith(f"/projects/{real_id}"):
                return _FakeResponse({"id": real_id, "name": "Indlab presentation"})
            if cors_id in url and "evidence-report" in url:
                return _FakeResponse({"source_count": 0, "evidence_count": 0, "sources": []})
            if real_id in url and "evidence-report" in url:
                return _FakeResponse(
                    {
                        "source_count": 1,
                        "evidence_count": 5,
                        "sources": [{"filename": "deck.pptx"}],
                    }
                )
            if "/contract" in url:
                return _FakeResponse({}, status_code=404)
            return _FakeResponse({}, status_code=404)

    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    (runtime / "ports.json").write_text(
        json.dumps({"backend_url": "http://127.0.0.1:8010"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    monkeypatch.setattr("app.services.diagnostics.project_discovery.httpx.Client", _FakeClient)

    resolved = resolve_project_id(
        latest=True,
        base_url="http://127.0.0.1:8010",
        runtime_root=tmp_path,
        data_dir=tmp_path / "data",
    )
    assert resolved.project_id == real_id
    assert resolved.source_count == 1
    assert resolved.filenames == ["deck.pptx"]
    assert len(resolved.skipped_projects) == 1
    assert resolved.skipped_projects[0].name == "CORS dynamic port test"


def test_latest_any_picks_raw_newest(monkeypatch, tmp_path) -> None:
    cors_id = str(uuid4())

    class _FakeResponse:
        def __init__(self, payload, status_code: int = 200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, params=None):
            if url.endswith("/api/v1/projects"):
                return _FakeResponse([{"id": cors_id, "name": "CORS dynamic port test"}])
            if "evidence-report" in url:
                return _FakeResponse({"source_count": 0, "evidence_count": 0, "sources": []})
            if "/contract" in url:
                return _FakeResponse({}, status_code=404)
            return _FakeResponse({}, status_code=404)

    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    (runtime / "ports.json").write_text(
        json.dumps({"backend_url": "http://127.0.0.1:8010"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    monkeypatch.setattr("app.services.diagnostics.project_discovery.httpx.Client", _FakeClient)

    resolved = resolve_project_id(
        latest_any=True,
        base_url="http://127.0.0.1:8010",
        runtime_root=tmp_path,
        data_dir=tmp_path / "data",
    )
    assert resolved.project_id == cors_id
    assert resolved.source == "latest_any"
    assert resolved.skipped_projects == []


def test_current_uses_runtime_file(monkeypatch, runtime_root, tmp_path) -> None:
    from app.services.diagnostics.last_project_tracker import write_last_project

    pid = str(uuid4())

    class _FakeResponse:
        def __init__(self, payload, status_code: int = 200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, params=None):
            if url.endswith(f"/projects/{pid}"):
                return _FakeResponse({"id": pid, "name": "Current"})
            if "evidence-report" in url:
                return _FakeResponse(
                    {
                        "source_count": 1,
                        "evidence_count": 1,
                        "sources": [{"filename": "a.pptx"}],
                    }
                )
            return _FakeResponse({}, status_code=404)

    write_last_project(runtime_root, project_id=pid, project_name="Current", source="upload")
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    monkeypatch.setattr("app.services.diagnostics.project_discovery.httpx.Client", _FakeClient)
    resolved = resolve_project_id(
        current=True,
        base_url="http://127.0.0.1:8010",
        runtime_root=runtime_root,
        data_dir=tmp_path / "data",
    )
    assert resolved.project_id == pid
    assert resolved.discovery_mode == "current"


def test_explicit_project_id_allows_technical_project(monkeypatch, runtime_root) -> None:
    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    pid = str(uuid4())
    resolved = resolve_project_id(
        project_id=pid,
        base_url="http://127.0.0.1:8010",
        runtime_root=runtime_root,
    )
    assert resolved.project_id == pid
    assert resolved.source == "explicit"


def test_latest_raises_when_only_technical_projects(monkeypatch, tmp_path) -> None:
    cors_id = str(uuid4())

    class _FakeResponse:
        def __init__(self, payload, status_code: int = 200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, params=None):
            if url.endswith("/api/v1/projects"):
                return _FakeResponse([{"id": cors_id, "name": "CORS dynamic port test"}])
            if "evidence-report" in url:
                return _FakeResponse({"source_count": 0, "evidence_count": 0, "sources": []})
            return _FakeResponse({}, status_code=404)

    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    (runtime / "ports.json").write_text(
        json.dumps({"backend_url": "http://127.0.0.1:8010"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "app.services.diagnostics.project_discovery.check_backend_available",
        lambda _url: True,
    )
    monkeypatch.setattr("app.services.diagnostics.project_discovery.httpx.Client", _FakeClient)

    with pytest.raises(ProjectDiscoveryError, match="No user project with uploaded sources"):
        resolve_project_id(
            latest=True,
            base_url="http://127.0.0.1:8010",
            runtime_root=tmp_path,
            data_dir=tmp_path / "data",
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
