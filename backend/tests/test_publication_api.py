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
from app.services.library.index import customer_key, detect_topics, topic_words_in
from app.services.library.search import FieldWords, name_forms, query_terms, stem, words

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
    cards = [hit["card"] for hit in library["hits"]]
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
    assert reader.get("/api/v1/library").json() == {
        "total": 0,
        "query": "",
        "direct_total": 0,
        "related_total": 0,
        "terms": 0,
        "hits": [],
    }
    assert reader.get(f"/api/v1/library/{slug}").status_code == 404
    assert reader.get(f"/api/v1/library/{slug}/html").status_code == 404

    again = publish(editor, contract).json()
    assert again["slug"] == slug and again["status"] == "published" and again["version"] == 2


def test_library_search_finds_titles_customers_and_surnames_in_other_forms(editor, reader) -> None:
    publish(editor, save_contract("Контроль кассовых операций", client="Банк Восток", lead="Петрова Анна"))
    publish(editor, save_contract("Чат-бот для абитуриентов", client="Приёмная комиссия", essence="Отвечает на вопросы о поступлении"))

    def hits(query: str) -> list[dict]:
        page = reader.get("/api/v1/library", params={"q": query}).json()
        assert page["total"] == 2
        return page["hits"]

    def found(query: str) -> list[str]:
        return [hit["card"]["title"] for hit in hits(query) if not hit["similar_topic"]]

    assert found("контроля") == ["Контроль кассовых операций"]
    assert found("Петровой") == ["Контроль кассовых операций"]
    assert found("банк") == ["Контроль кассовых операций"]
    assert found("поступление") == ["Чат-бот для абитуриентов"]
    assert found("чат комиссия") == ["Чат-бот для абитуриентов"]
    assert found("контроль абитуриентов") == []
    assert len(found("")) == 2
    assert hits("Петровой")[0]["reasons"] == ["участник: Петрова Анна"]
    assert hits("банк")[0]["reasons"] == ["заказчик"]
    assert hits("контроля")[0]["reasons"] == ["в названии"]


def test_a_similar_topic_finds_landings_that_never_use_the_words(editor, reader) -> None:
    publish(editor, save_contract("Пустые полки в магазине", essence="Камера замечает пустые полки, детекция товаров по изображению"))
    publish(editor, save_contract("Помощник эндокринолога", essence="Подсказывает врачу питание пациента"))

    page = reader.get("/api/v1/library", params={"q": "видеонаблюдение"}).json()
    assert [(h["card"]["title"], h["reasons"], h["similar_topic"]) for h in page["hits"]] == [
        ("Пустые полки в магазине", ["похожая тема: Компьютерное зрение"], True)
    ]
    topic = reader.get("/api/v1/library", params={"q": "медицина"}).json()["hits"]
    assert [(h["card"]["title"], h["reasons"]) for h in topic] == [("Помощник эндокринолога", ["тема: Медицина и здоровье"])]


def test_shelves_group_landings_by_topic_and_the_newest_come_first(editor, reader) -> None:
    publish(editor, save_contract("Пустые полки в магазине", essence="Камера замечает пустые полки, детекция товаров"))
    publish(editor, save_contract("Очереди на кассе по видео", client="Сеть магазинов", essence="Камера считает людей, распознавание лиц не нужно"))
    publish(editor, save_contract("Помощник эндокринолога", essence="Подсказывает врачу питание пациента"))

    shelves = reader.get("/api/v1/library/_shelves").json()
    assert shelves["total"] == 3
    assert [c["title"] for c in shelves["fresh"]] == ["Помощник эндокринолога", "Очереди на кассе по видео", "Пустые полки в магазине"]
    by_key = {shelf["key"]: shelf for shelf in shelves["shelves"]}
    assert shelves["shelves"][0]["key"] == "vision"
    assert [c["title"] for c in by_key["vision"]["cards"]] == ["Очереди на кассе по видео", "Пустые полки в магазине"]
    # One medicine landing: it stays in "Новые проекты" and the topic buttons, without a carousel of one.
    assert "medicine" not in by_key
    assert {"key": "medicine", "label": "Медицина и здоровье", "count": 1} in shelves["topics"]
    assert {"key": "vision", "label": "Компьютерное зрение", "count": 2} in shelves["topics"]
    assert shelves["fresh"][0]["topics"][0] == {"key": "medicine", "label": "Медицина и здоровье"}


def test_similar_landings_say_what_they_share(editor, reader) -> None:
    first = publish(editor, save_contract("Пустые полки в магазине", client="Сеть «Пример»", essence="Камера замечает пустые полки, детекция товаров")).json()
    publish(editor, save_contract("Очереди на кассе по видео", essence="Камера считает людей у кассы, детекция по изображению"))
    publish(editor, save_contract("Скидки для покупателей", client="Сеть «Пример»", essence="Рассылка персональных предложений"))
    publish(editor, save_contract("Помощник эндокринолога", essence="Подсказывает врачу питание пациента"))

    similar = reader.get(f"/api/v1/library/{first['slug']}/similar").json()
    reasons = {item["card"]["title"]: item["reason"] for item in similar}
    assert reasons["Скидки для покупателей"] == "общий заказчик: Сеть «Пример»"
    assert reasons["Очереди на кассе по видео"] == "общая тема: Компьютерное зрение"
    assert "Помощник эндокринолога" not in reasons
    assert reader.get("/api/v1/library/no-such-landing/similar").status_code == 404


def test_words_every_project_uses_do_not_make_landings_similar(editor, reader) -> None:
    first = publish(editor, save_contract("Учёт склада", essence="Система для проекта: результат работы команды")).json()
    publish(editor, save_contract("Запись к врачу", essence="Система для проекта: результат работы команды"))
    assert reader.get(f"/api/v1/library/{first['slug']}/similar").json() == []


def test_library_routes_never_hide_a_landing_address(editor, reader) -> None:
    assert publish(editor, save_contract("Shelves")).json()["slug"] == "shelves"
    assert reader.get("/api/v1/library/shelves").json()["title"] == "Shelves"
    assert reader.get("/api/v1/library/_shelves").json()["total"] == 1


def test_short_words_and_surnames_do_not_match_everything(editor, reader) -> None:
    publish(editor, save_contract("Учёт склада", lead="Иванов Пётр", essence="Склад и транспорт"))
    publish(editor, save_contract("Помощник ИИ для врача", lead="Петрова Анна", essence="Подсказывает врачу питание пациента"))

    def found(query: str) -> list[str]:
        page = reader.get("/api/v1/library", params={"q": query}).json()
        return [hit["card"]["title"] for hit in page["hits"] if not hit["similar_topic"]]

    # The stemmer would cut "ИИ" to "и" and find both landings.
    assert found("ИИ") == ["Помощник ИИ для врача"]
    # "Петровой" → Петрова, never Пётр; "Иванову" → Иванов.
    assert found("Петровой") == ["Помощник ИИ для врача"]
    assert found("Иванову") == ["Учёт склада"]
    # Prepositions and look-alike words point at no topic.
    page = reader.get("/api/v1/library", params={"q": "про статус"}).json()
    assert page["hits"] == []


def test_queries_without_words_and_too_long_queries(editor, reader) -> None:
    publish(editor, save_contract("Учёт склада"))
    nothing = reader.get("/api/v1/library", params={"q": "?!"}).json()
    assert nothing["terms"] == 0 and nothing["hits"] == [] and nothing["total"] == 1
    long = reader.get("/api/v1/library", params={"q": "склад " + "x" * 400})
    assert long.status_code == 200 and len(long.json()["query"]) == 200


def test_search_counts_matches_before_the_limit(editor, reader) -> None:
    for n in range(3):
        publish(editor, save_contract(f"Склад номер {n}"))
    page = reader.get("/api/v1/library", params={"q": "склад", "limit": 2}).json()
    assert page["direct_total"] == 3 and len(page["hits"]) == 2


def test_landings_without_a_shelf_still_reach_the_front_page(editor, reader, monkeypatch) -> None:
    from app.services.library import index as library_index_module

    monkeypatch.setattr(library_index_module, "FRESH_COUNT", 1)
    publish(editor, save_contract("Учёт склада"))
    publish(editor, save_contract("Запись к врачу"))
    shelves = reader.get("/api/v1/library/_shelves").json()
    assert [c["title"] for c in shelves["fresh"]] == ["Запись к врачу"]
    assert [(s["label"], [c["title"] for c in s["cards"]]) for s in shelves["shelves"]] == [
        ("Другие проекты", ["Учёт склада"])
    ]


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
    # Other forms of a word share a stem; one-letter words carry no meaning; short words stay whole.
    assert [t.word for t in query_terms("Контроля и контроль ИИ")] == ["контроля", "контроль", "ии"]
    assert stem("ии") == "ии" and stem("уии") == "уии"
    assert stem("контроля") == stem("контроль")
    field = FieldWords(words("Контроль кассовых операций"))
    assert all(field.matches(t) for t in query_terms("контроля конт касса"))
    assert not any(field.matches(t) for t in query_terms("чат"))
    assert name_forms("петровой") == ("петровой", "петров")
    assert name_forms("кус") == ("кус",)


def test_topics_need_two_words_or_one_in_the_title() -> None:
    from collections import Counter

    def topics(title: str, text: str) -> tuple[str, ...]:
        title_words = words(title)
        return detect_topics(Counter(title_words + words(text)), set(title_words))

    assert topics("Проект", "камера и детекция") == ("vision",)
    assert topics("Проект", "одна камера") == ()
    assert topics("Камера на входе", "") == ("vision",)
    # "обучение модели" is training, not education; "курс валют" is not a course.
    assert topics("Проект", "обучение модели, курс валют") == ()
    # Short topic stems match only whole words or the topic word itself as a prefix.
    assert {key for key, _ in topic_words_in("видеонаблюдение")} == {"vision"}
    assert topic_words_in("видел") == set() and topic_words_in("статус") == set()
    assert topic_words_in("ботаника") == set() and {k for k, _ in topic_words_in("ботов")} == {"texts"}


def test_customer_names_ignore_the_legal_form() -> None:
    assert customer_key("ООО «Пример»") == customer_key("Пример") != ""
    assert customer_key('ООО "ИНДЛАБ"') == customer_key("ООО «Индлаб»")
