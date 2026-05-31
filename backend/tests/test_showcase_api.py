"""API tests for the Showcase Registry endpoints (Stage P.6).

The module-level registry is swapped for a temp-dir instance so the test
suite never writes to the real ``backend/data/showcases`` tree.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.services.showcase.showcase_registry as registry_module
from app.main import app
from app.services.showcase.showcase_registry import ShowcaseRegistry
from app.services.showcase.showcase_vendor import VENDOR_SOURCE

API = "/api/v1/showcases"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    temp_registry = ShowcaseRegistry(base_dir=tmp_path / "showcases")
    monkeypatch.setattr(registry_module, "_registry", temp_registry)
    return TestClient(app)


def _create(client: TestClient, title: str = "Витрина AI") -> dict:
    res = client.post(API, json={"title": title})
    assert res.status_code == 201, res.text
    return res.json()


def test_create_and_get_showcase(client: TestClient) -> None:
    created = _create(client)
    sid = created["id"]
    assert created["title"] == "Витрина AI"

    got = client.get(f"{API}/{sid}")
    assert got.status_code == 200
    assert got.json()["id"] == sid


def test_list_showcases(client: TestClient) -> None:
    _create(client, "A")
    _create(client, "B")
    res = client.get(API)
    assert res.status_code == 200
    titles = {item["title"] for item in res.json()}
    assert titles == {"A", "B"}


def test_project_crud(client: TestClient) -> None:
    sid = _create(client)["id"]

    # add
    res = client.post(
        f"{API}/{sid}/projects",
        json={"title": "Эндокринология+", "demo_url": "https://aistudio.google.com/"},
    )
    assert res.status_code == 200, res.text
    config = res.json()
    assert len(config["projects"]) == 1
    pid = config["projects"][0]["id"]

    # update
    res = client.patch(
        f"{API}/{sid}/projects/{pid}",
        json={"category": "Health"},
    )
    assert res.status_code == 200
    assert res.json()["projects"][0]["category"] == "Health"

    # second project + reorder
    res = client.post(f"{API}/{sid}/projects", json={"title": "Second"})
    pid2 = res.json()["projects"][1]["id"]
    res = client.post(
        f"{API}/{sid}/projects/reorder", json={"ordered_ids": [pid2, pid]}
    )
    assert [p["title"] for p in res.json()["projects"]] == ["Second", "Эндокринология+"]

    # delete
    res = client.delete(f"{API}/{sid}/projects/{pid}")
    assert res.status_code == 200
    assert len(res.json()["projects"]) == 1


def test_update_and_delete_showcase(client: TestClient) -> None:
    sid = _create(client)["id"]
    res = client.patch(f"{API}/{sid}", json={"theme": "tech", "title": "Renamed"})
    assert res.status_code == 200
    assert res.json()["theme"] == "tech"
    assert res.json()["title"] == "Renamed"

    res = client.delete(f"{API}/{sid}")
    assert res.status_code == 200
    assert res.json() == {"deleted": True}
    assert client.get(f"{API}/{sid}").status_code == 404


def test_export_html_returns_text(client: TestClient) -> None:
    sid = _create(client, "Экспорт")["id"]
    client.post(
        f"{API}/{sid}/projects",
        json={"title": "Проект", "demo_url": "https://aistudio.google.com/"},
    )
    res = client.post(f"{API}/{sid}/export-html")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["html"].startswith("<!DOCTYPE html>")
    assert body["project_count"] == 1


@pytest.mark.skipif(not VENDOR_SOURCE.is_file(), reason="vendored runtime missing")
def test_export_zip_returns_application_zip(client: TestClient) -> None:
    sid = _create(client, "ZIP")["id"]
    client.post(f"{API}/{sid}/projects", json={"title": "Проект"})
    res = client.post(f"{API}/{sid}/export-zip")
    assert res.status_code == 200, res.text
    assert res.headers["content-type"] == "application/zip"
    assert res.content[:2] == b"PK"


def test_landing_candidates_endpoint(client: TestClient) -> None:
    res = client.get("/api/v1/showcase/landing-candidates")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_missing_showcase_404(client: TestClient) -> None:
    assert client.get(f"{API}/missing-id").status_code == 404
