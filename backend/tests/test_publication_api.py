from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import auth as auth_api
from app.core.auth import LoginThrottle
from app.core.dependencies import get_account_repository, get_contract_repository, get_database
from app.core.security import hash_password
from app.main import app
from app.schemas.fidelity import TeamMember
from app.schemas.landing_contract import LandingBlock, LandingContract
from app.services.library import metadata
from app.services.library.metadata import publication_meta, slugify
from app.services.library.search import query_terms, score, words

PASSWORD = "correct-horse-1"
PAGE = "<!doctype html><html lang=\"ru\"><body><h1>Страница</h1></body></html>"


@pytest.fixture
def editor(real_auth, monkeypatch) -> TestClient:
    with get_database().write() as conn:
        for table in ("sessions", "invites", "publications", "users"):
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


def save_contract(title: str, *, client: str = "", lead: str = "", essence: str = "") -> LandingContract:
    contract = LandingContract(
        project_id=uuid4(),
        title=title,
        client=client,
        lead=lead,
        blocks=[LandingBlock(key="essence", title="Суть проекта", content=essence)],
        updated_at=datetime.now(timezone.utc),
    )
    asyncio.run(get_contract_repository().save_contract(contract))
    return contract


def publish(client: TestClient, contract: LandingContract, html: str = PAGE, **extra):
    body = {"html": html, "theme": "night", "contract_version": contract.version, "summary": "Коротко о проекте"} | extra
    return client.post(f"/api/v1/projects/{contract.project_id}/publication", json=body)


def test_publishing_puts_the_landing_into_the_library(editor, reader) -> None:
    contract = save_contract("Контроль кассовых операций", client="ООО «Пример»", lead="Петрова Анна")
    assert editor.get(f"/api/v1/projects/{contract.project_id}/publication").json() is None

    response = publish(editor, contract)
    assert response.status_code == 200, response.text
    info = response.json()
    assert info["slug"] == "kontrol-kassovyh-operatsiy" and info["path"] == "/p/kontrol-kassovyh-operatsiy"
    assert info["status"] == "published" and info["version"] == 1 and info["published_by_name"] == "Анна Редактор"

    library = reader.get("/api/v1/library").json()
    cards = library["cards"]
    assert library["total"] == 1 and [c["slug"] for c in cards] == ["kontrol-kassovyh-operatsiy"]
    assert cards[0]["customer"] == "ООО «Пример»" and cards[0]["people"] == ["Петрова Анна"]

    page = reader.get("/api/v1/library/kontrol-kassovyh-operatsiy/html")
    assert page.status_code == 200 and page.text == PAGE
    assert page.headers["content-security-policy"].startswith("sandbox;")
    assert page.headers["x-content-type-options"] == "nosniff"


def test_viewers_cannot_publish(editor, reader) -> None:
    contract = save_contract("Проект для чтения")
    assert publish(reader, contract).status_code == 403


def test_republishing_keeps_the_address_and_counts_versions(editor) -> None:
    contract = save_contract("Цифровой двойник цеха")
    first = publish(editor, contract).json()
    contract.title = "Новое название двойника"
    contract.version += 1
    asyncio.run(get_contract_repository().save_contract(contract))
    second = publish(editor, contract).json()
    assert second["slug"] == first["slug"] == "tsifrovoy-dvoynik-tseha"
    assert second["version"] == 2 and second["title"] == "Новое название двойника"
    assert second["first_published_at"] == first["first_published_at"]


def test_same_titles_get_different_addresses(editor) -> None:
    one = publish(editor, save_contract("Чат-бот приёмной комиссии")).json()["slug"]
    two = publish(editor, save_contract("Чат-бот приёмной комиссии")).json()["slug"]
    assert (one, two) == ("chat-bot-priemnoy-komissii", "chat-bot-priemnoy-komissii-2")


def test_publishing_a_stale_render_is_refused(editor) -> None:
    contract = save_contract("Устаревшая версия")
    response = publish(editor, contract, contract_version=contract.version - 1)
    assert response.status_code == 409


def test_pages_with_scripts_or_without_a_doctype_are_refused(editor) -> None:
    contract = save_contract("Проверка страницы")
    assert publish(editor, contract, html="<!doctype html><script>alert(1)</script>").status_code == 422
    assert publish(editor, contract, html="<p>кусок</p>").status_code == 422


def test_withdrawn_landing_disappears_and_comes_back_at_the_same_address(editor, reader) -> None:
    contract = save_contract("Снятый с публикации")
    slug = publish(editor, contract).json()["slug"]
    withdrawn = editor.delete(f"/api/v1/projects/{contract.project_id}/publication")
    assert withdrawn.status_code == 200 and withdrawn.json()["status"] == "withdrawn"
    assert reader.get("/api/v1/library").json() == {"total": 0, "cards": []}
    assert reader.get(f"/api/v1/library/{slug}").status_code == 404
    assert reader.get(f"/api/v1/library/{slug}/html").status_code == 404

    again = publish(editor, contract).json()
    assert again["slug"] == slug and again["status"] == "published" and again["version"] == 2


def test_library_search_finds_titles_customers_and_surnames_in_other_forms(editor, reader) -> None:
    publish(editor, save_contract("Контроль кассовых операций", client="Банк Восток", lead="Петрова Анна"))
    publish(editor, save_contract("Чат-бот для абитуриентов", client="Приёмная комиссия", essence="Отвечает на вопросы о поступлении"))

    def found(query: str) -> list[str]:
        page = reader.get("/api/v1/library", params={"q": query}).json()
        assert page["total"] == 2
        return [card["title"] for card in page["cards"]]

    assert found("контроля") == ["Контроль кассовых операций"]
    assert found("Петровой") == ["Контроль кассовых операций"]
    assert found("банк") == ["Контроль кассовых операций"]
    assert found("поступление") == ["Чат-бот для абитуриентов"]
    assert found("чат комиссия") == ["Чат-бот для абитуриентов"]
    assert found("контроль абитуриентов") == []
    assert len(found("")) == 2


def test_stale_edit_of_the_contract_answers_409_and_keeps_the_newer_text(editor) -> None:
    contract = save_contract("Общий лендинг")
    url = f"/api/v1/projects/{contract.project_id}/contract"
    first = editor.patch(url, json={"title": "Правка первого", "expected_version": contract.version})
    assert first.status_code == 200 and first.json()["version"] == contract.version + 1

    stale = editor.patch(url, json={"title": "Правка второго", "expected_version": contract.version})
    assert stale.status_code == 409
    assert asyncio.run(get_contract_repository().get_contract(contract.project_id)).title == "Правка первого"


def test_meta_takes_only_names_that_the_page_shows(monkeypatch) -> None:
    contract = LandingContract(
        project_id=uuid4(),
        title="  ",
        lead="Орлов Пётр",
        blocks=[
            LandingBlock(key="team", title="Команда", content="", bullets=["Скрытый Участник — роль"]),
            LandingBlock(key="tasks", title="Задачи", content="Разметка ёлок", bullets=["Детекция YOLO"]),
        ],
        updated_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(
        metadata,
        "publishable_team",
        lambda block, fidelity: [TeamMember(name="Соколова Мария"), TeamMember(name="Орлов Пётр")],
    )
    meta = publication_meta(contract, "  Итог  ")
    assert meta.title == "Проект" and meta.summary == "Итог"
    assert meta.people == ["Соколова Мария", "Орлов Пётр"]
    assert "скрытый" not in meta.body_text and "елок" in meta.body_text and "yolo" in meta.body_text


def test_slug_and_search_helpers() -> None:
    assert slugify("Контроль кассы: v2.0!") == "kontrol-kassy-v2-0"
    assert slugify("!!!") == "lend"
    assert words("Ёлка, YOLO-v8") == ["елка", "yolo", "v8"]
    assert query_terms("Иванову и Иванову") == ["ивано"]
    assert query_terms("куса сайт") == ["кус", "сайт"]
    assert score(query_terms("Куса"), [(2.0, ["кус", "николай"])]) == 2.0
    assert score(query_terms("Иванову"), [(2.0, ["иванов"])]) == 2.0
    assert score(query_terms("кассы банк"), [(3.0, ["касса"]), (1.0, ["банка"])]) == 4.0
    assert score(query_terms("кассы чат"), [(3.0, ["касса"])]) == 0.0
