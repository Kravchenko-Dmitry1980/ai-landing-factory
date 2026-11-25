"""A demo stays in the studio until publication, then plays on the intern link only."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import auth as auth_api
from app.api.v1 import demos as demos_api
from app.core.auth import LoginThrottle
from app.core.dependencies import get_account_repository, get_contract_repository, get_database
from app.core.security import hash_password
from app.main import app
from app.schemas.landing_contract import LandingBlock, LandingContract

PASSWORD = "correct-horse-1"
PAGE = "<!doctype html><html lang=\"ru\"><body><h1>Страница</h1></body></html>"


def _mp4(marker: bytes = b"A") -> bytes:
    body = b"ftypisom" + b"\x00" * 8 + marker
    return len(body).to_bytes(4, "big") + body


def _jpeg() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * 16


@pytest.fixture
def editor(real_auth, monkeypatch) -> TestClient:
    with get_database().write() as conn:
        for table in ("sessions", "invites", "demos", "publications", "users"):
            conn.execute(f"DELETE FROM {table}")
    monkeypatch.setattr(auth_api, "_throttle", LoginThrottle())
    accounts = get_account_repository()
    accounts.create_user(login="hr", name="Анна Редактор", role="editor", password_hash=hash_password(PASSWORD))
    accounts.create_user(login="reader", name="Читатель", role="viewer", password_hash=hash_password(PASSWORD))
    client = TestClient(app)
    assert client.post("/api/v1/auth/login", json={"login": "hr", "password": PASSWORD}).status_code == 200
    return client


@pytest.fixture
def reader(editor) -> TestClient:
    client = TestClient(app)
    assert client.post("/api/v1/auth/login", json={"login": "reader", "password": PASSWORD}).status_code == 200
    return client


def save_contract(title: str) -> LandingContract:
    contract = LandingContract(
        project_id=uuid4(),
        title=title,
        blocks=[LandingBlock(key="essence", title="Суть проекта", content="Описание")],
        updated_at=datetime.now(timezone.utc),
    )
    asyncio.run(get_contract_repository().save_contract(contract))
    return contract


def publish(client: TestClient, contract: LandingContract):
    return client.post(
        f"/api/v1/projects/{contract.project_id}/publication",
        json={"html": PAGE, "theme": "night", "contract_version": contract.version, "summary": "Коротко"},
    )


def put_demo(client: TestClient, contract: LandingContract, video: bytes, poster: bytes | None = None):
    files = {"video": ("demo.mp4", video, "video/mp4")}
    if poster is not None:
        files["poster"] = ("cover.jpg", poster, "image/jpeg")
    return client.put(f"/api/v1/projects/{contract.project_id}/demo", files=files)


def test_demo_reaches_the_intern_only_after_publication(editor, reader) -> None:
    contract = save_contract("Комус")
    assert put_demo(editor, contract, _mp4(b"new"), _jpeg()).status_code == 200
    draft = editor.get(f"/api/v1/projects/{contract.project_id}/demo").json()
    assert draft["has_draft"] and draft["has_poster"] and not draft["on_link"] and not draft["pending"]

    published = publish(editor, contract)
    assert published.status_code == 200, published.text
    token = published.json()["public_path"].removeprefix("/s/")
    meta = editor.get(f"/api/v1/public/landings/{token}/meta")
    assert meta.status_code == 200
    assert meta.json()["demo"] is True and meta.json()["poster"] is True and meta.json()["title"] == "Комус"
    video = editor.get(f"/api/v1/public/landings/{token}/demo")
    assert video.status_code == 200 and video.content == _mp4(b"new")
    assert video.headers["content-type"].startswith("video/mp4")
    page = editor.get(f"/api/v1/public/landings/{token}")
    assert page.status_code == 200 and "<video" not in page.text and page.text == PAGE

    card = reader.get("/api/v1/library").json()["hits"][0]["card"]
    assert card["has_demo"] is True

    replaced = put_demo(editor, contract, _mp4(b"old"))
    assert replaced.status_code == 200
    assert editor.get(f"/api/v1/public/landings/{token}/demo").content == _mp4(b"new")
    pending = editor.get(f"/api/v1/projects/{contract.project_id}/demo").json()
    assert pending["pending"] and pending["on_link"] and pending["has_poster"]

    contract.version += 1
    asyncio.run(get_contract_repository().save_contract(contract))
    assert publish(editor, contract).status_code == 200
    assert editor.get(f"/api/v1/public/landings/{token}/demo").content == _mp4(b"old")

    assert editor.delete(f"/api/v1/projects/{contract.project_id}/demo").status_code == 200
    assert editor.get(f"/api/v1/public/landings/{token}/demo").content == _mp4(b"old")
    contract.version += 1
    asyncio.run(get_contract_repository().save_contract(contract))
    again = publish(editor, contract)
    assert again.json()["public_path"] == f"/s/{token}"
    assert editor.get(f"/api/v1/public/landings/{token}/meta").json()["demo"] is False
    assert editor.get(f"/api/v1/public/landings/{token}/demo").status_code == 404
    assert reader.get("/api/v1/library").json()["hits"][0]["card"]["has_demo"] is False


def test_withdrawing_closes_the_demo(editor) -> None:
    contract = save_contract("Закрытый ролик")
    assert put_demo(editor, contract, _mp4()).status_code == 200
    published = publish(editor, contract).json()
    token = published["public_path"].removeprefix("/s/")
    assert editor.delete(f"/api/v1/projects/{contract.project_id}/publication").status_code == 200
    assert editor.get(f"/api/v1/public/landings/{token}/meta").status_code == 404
    assert editor.get(f"/api/v1/public/landings/{token}/demo").status_code == 404


def test_viewers_cannot_change_a_demo(editor, reader) -> None:
    contract = save_contract("Только просмотр")
    assert put_demo(reader, contract, _mp4()).status_code == 403
    assert reader.get(f"/api/v1/projects/{contract.project_id}/demo").status_code == 403


def test_rejects_a_file_that_is_not_mp4(editor) -> None:
    contract = save_contract("Не ролик")
    response = editor.put(
        f"/api/v1/projects/{contract.project_id}/demo",
        files={"video": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 422
    assert "MP4" in response.json()["detail"]


def test_rejects_a_video_over_the_limit(editor, monkeypatch) -> None:
    monkeypatch.setattr(demos_api, "MAX_VIDEO_BYTES", 20)
    contract = save_contract("Слишком большой")
    response = editor.put(
        f"/api/v1/projects/{contract.project_id}/demo",
        files={"video": ("demo.mp4", _mp4() + b"x" * 40, "video/mp4")},
    )
    assert response.status_code == 413
