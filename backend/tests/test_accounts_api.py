from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import auth as auth_api
from app.core.auth import LoginThrottle
from app.core.dependencies import get_account_repository, get_database
from app.core.security import hash_password
from app.repositories.account_repository import LastAdminError
from app.main import app

PASSWORD = "correct-horse-1"


@pytest.fixture
def accounts(real_auth, monkeypatch):
    with get_database().write() as conn:
        for table in ("sessions", "invites", "publications", "users"):
            conn.execute(f"DELETE FROM {table}")
    monkeypatch.setattr(auth_api, "_throttle", LoginThrottle())
    return get_account_repository()


def make_user(accounts, login: str, role: str = "editor"):
    return accounts.create_user(login=login, name=f"Тест {login}", role=role, password_hash=hash_password(PASSWORD))


def signed_in(login: str, password: str = PASSWORD) -> TestClient:
    client = TestClient(app)
    response = client.post("/api/v1/auth/login", json={"login": login, "password": password})
    assert response.status_code == 200, response.text
    return client


def test_everything_but_sign_in_needs_a_session(accounts) -> None:
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    for path in ("/api/v1/auth/me", "/api/v1/projects", "/api/v1/library", "/api/v1/admin/users", "/api/v1/showcases"):
        assert client.get(path).status_code == 401, path


def test_login_sets_an_http_only_cookie_and_logout_ends_the_session(accounts) -> None:
    make_user(accounts, "hr.one")
    client = TestClient(app)

    response = client.post("/api/v1/auth/login", json={"login": "  HR.One ", "password": PASSWORD})
    assert response.status_code == 200
    assert response.json()["login"] == "hr.one"
    cookie = response.headers["set-cookie"]
    assert "lend_session=" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie
    assert "Secure" not in cookie  # plain http in tests; auto mode turns it on behind https
    assert client.get("/api/v1/auth/me").json()["name"] == "Тест hr.one"

    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_wrong_password_and_unknown_login_get_the_same_answer(accounts) -> None:
    make_user(accounts, "hr.two")
    client = TestClient(app)
    wrong = client.post("/api/v1/auth/login", json={"login": "hr.two", "password": "nope-nope"})
    unknown = client.post("/api/v1/auth/login", json={"login": "nobody", "password": "nope-nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_repeated_failures_lock_the_login_for_a_while(accounts) -> None:
    make_user(accounts, "hr.three")
    client = TestClient(app)
    for _ in range(10):
        assert client.post("/api/v1/auth/login", json={"login": "hr.three", "password": "bad-guess"}).status_code == 401
    locked = client.post("/api/v1/auth/login", json={"login": "hr.three", "password": PASSWORD})
    assert locked.status_code == 429


def test_roles_decide_what_an_account_reaches(accounts) -> None:
    make_user(accounts, "reader", role="viewer")
    make_user(accounts, "editor", role="editor")
    make_user(accounts, "boss", role="admin")

    viewer = signed_in("reader")
    assert viewer.get("/api/v1/library").status_code == 200
    assert viewer.get("/api/v1/projects").status_code == 403
    assert viewer.post("/api/v1/projects", json={"name": "x"}).status_code == 403

    editor = signed_in("editor")
    assert editor.get("/api/v1/projects").status_code == 200
    assert editor.get("/api/v1/admin/users").status_code == 403

    assert signed_in("boss").get("/api/v1/admin/users").status_code == 200


def test_invite_link_creates_an_account_once(accounts) -> None:
    make_user(accounts, "boss", role="admin")
    admin = signed_in("boss")
    created = admin.post("/api/v1/admin/invites", json={"role": "editor", "note": "Отдел кадров"})
    assert created.status_code == 201
    path = created.json()["path"]
    token = path.removeprefix("/invite/")
    assert len(admin.get("/api/v1/admin/invites").json()) == 1

    guest = TestClient(app)
    info = guest.get(f"/api/v1/auth/invites/{token}").json()
    assert info["kind"] == "account" and info["role"] == "editor" and info["created_by_name"] == "Тест boss"

    bad_login = guest.post(f"/api/v1/auth/invites/{token}/accept", json={"login": "не латиница", "name": "Мария Соколова", "password": PASSWORD})
    assert bad_login.status_code == 422
    short = guest.post(f"/api/v1/auth/invites/{token}/accept", json={"login": "m.sokolova", "name": "Мария Соколова", "password": "short"})
    assert short.status_code == 422

    accepted = guest.post(f"/api/v1/auth/invites/{token}/accept", json={"login": "M.Sokolova", "name": " Мария   Соколова ", "password": PASSWORD})
    assert accepted.status_code == 200
    assert accepted.json()["login"] == "m.sokolova" and accepted.json()["name"] == "Мария Соколова"
    assert guest.get("/api/v1/projects").status_code == 200  # signed in right away, as an editor

    assert TestClient(app).get(f"/api/v1/auth/invites/{token}").status_code == 404
    again = TestClient(app).post(f"/api/v1/auth/invites/{token}/accept", json={"login": "other", "name": "Другой Человек", "password": PASSWORD})
    assert again.status_code == 404
    assert admin.get("/api/v1/admin/invites").json() == []


def test_invite_with_a_taken_login_can_be_retried(accounts) -> None:
    make_user(accounts, "boss", role="admin")
    token = signed_in("boss").post("/api/v1/admin/invites", json={}).json()["path"].removeprefix("/invite/")
    guest = TestClient(app)
    taken = guest.post(f"/api/v1/auth/invites/{token}/accept", json={"login": "boss", "name": "Новый Сотрудник", "password": PASSWORD})
    assert taken.status_code == 409
    ok = guest.post(f"/api/v1/auth/invites/{token}/accept", json={"login": "new.person", "name": "Новый Сотрудник", "password": PASSWORD})
    assert ok.status_code == 200


def test_revoked_invite_stops_working(accounts) -> None:
    make_user(accounts, "boss", role="admin")
    admin = signed_in("boss")
    created = admin.post("/api/v1/admin/invites", json={}).json()
    assert admin.delete(f"/api/v1/admin/invites/{created['invite']['id']}").status_code == 204
    assert TestClient(app).get(f"/api/v1/auth/invites/{created['path'].removeprefix('/invite/')}").status_code == 404


def test_reset_link_replaces_the_password_and_ends_old_sessions(accounts) -> None:
    make_user(accounts, "boss", role="admin")
    worker = make_user(accounts, "worker")
    old_session = signed_in("worker")

    link = signed_in("boss").post(f"/api/v1/admin/users/{worker.id}/reset-link")
    assert link.status_code == 201
    token = link.json()["path"].removeprefix("/invite/")
    assert TestClient(app).get(f"/api/v1/auth/invites/{token}").json()["kind"] == "reset"

    fresh = TestClient(app)
    assert fresh.post(f"/api/v1/auth/invites/{token}/accept", json={"password": "brand-new-pass"}).status_code == 200
    assert old_session.get("/api/v1/auth/me").status_code == 401
    assert fresh.get("/api/v1/auth/me").json()["login"] == "worker"
    assert TestClient(app).post("/api/v1/auth/login", json={"login": "worker", "password": PASSWORD}).status_code == 401
    signed_in("worker", "brand-new-pass")


def test_switching_an_account_off_ends_its_sessions(accounts) -> None:
    make_user(accounts, "boss", role="admin")
    worker = make_user(accounts, "worker")
    session = signed_in("worker")
    response = signed_in("boss").patch(f"/api/v1/admin/users/{worker.id}", json={"is_active": False})
    assert response.status_code == 200 and response.json()["is_active"] is False
    assert session.get("/api/v1/auth/me").status_code == 401
    blocked = TestClient(app).post("/api/v1/auth/login", json={"login": "worker", "password": PASSWORD})
    assert blocked.status_code == 403


def test_admins_cannot_lock_themselves_or_everyone_out(accounts) -> None:
    boss = make_user(accounts, "boss", role="admin")
    other = make_user(accounts, "deputy", role="admin")
    admin = signed_in("boss")
    assert admin.patch(f"/api/v1/admin/users/{boss.id}", json={"role": "editor"}).status_code == 409
    assert admin.patch(f"/api/v1/admin/users/{other.id}", json={"role": "editor"}).status_code == 200
    with pytest.raises(LastAdminError):
        accounts.update_user(boss.id, is_active=False)


def test_changes_from_other_sites_are_refused(accounts) -> None:
    make_user(accounts, "hr.four")
    client = TestClient(app)
    foreign = client.post(
        "/api/v1/auth/login",
        json={"login": "hr.four", "password": PASSWORD},
        headers={"Origin": "https://evil.example"},
    )
    assert foreign.status_code == 403
    own = client.post(
        "/api/v1/auth/login",
        json={"login": "hr.four", "password": PASSWORD},
        headers={"Origin": "http://testserver"},
    )
    assert own.status_code == 200


def test_a_stranger_guessing_does_not_lock_the_owner_out_from_another_computer(accounts) -> None:
    make_user(accounts, "boss", role="admin")
    stranger = TestClient(app)
    for _ in range(10):
        stranger.post("/api/v1/auth/login", json={"login": "boss", "password": "guess-guess"}, headers={"X-Real-IP": "203.0.113.7"})
    assert stranger.post("/api/v1/auth/login", json={"login": "boss", "password": PASSWORD}, headers={"X-Real-IP": "203.0.113.7"}).status_code == 429
    owner = TestClient(app).post("/api/v1/auth/login", json={"login": "boss", "password": PASSWORD}, headers={"X-Real-IP": "198.51.100.2"})
    assert owner.status_code == 200


def test_own_site_on_another_port_is_not_a_foreign_site(accounts) -> None:
    make_user(accounts, "hr.five")
    response = TestClient(app).post(
        "/api/v1/auth/login",
        json={"login": "hr.five", "password": PASSWORD},
        headers={"Origin": "http://testserver:8080"},
    )
    assert response.status_code == 200


def test_data_dir_alone_moves_every_data_folder(tmp_path, monkeypatch) -> None:
    from app.config import Settings

    # conftest sets these for the whole suite; here only DATA_DIR is given, as on the server.
    for name in ("UPLOADS_DIR", "CONTRACTS_DIR", "EXTRACTIONS_DIR"):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(data_dir=tmp_path)
    assert (settings.uploads_dir, settings.contracts_dir, settings.extractions_dir) == (
        tmp_path / "uploads",
        tmp_path / "contracts",
        tmp_path / "extractions",
    )
    assert settings.database_path == tmp_path / "lend.sqlite3"


def test_readiness_touches_the_database_and_the_data_folder(accounts) -> None:
    response = TestClient(app).get("/health/ready")
    assert response.status_code == 200 and response.json() == {"status": "ready"}
