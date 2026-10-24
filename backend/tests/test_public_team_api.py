from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.fidelity import TeamMember
from app.schemas.landing_contract import LandingBlock
from app.services.export import public_team
from tests.fixtures.export_contract_fixture import make_wow_indlab_fixture


def test_public_team_returns_404_without_contract() -> None:
    class Repo:
        async def get_contract(self, pid):
            return None

    with patch("app.api.v1.contracts.get_contract_repository", return_value=Repo()):
        response = TestClient(app).get(f"/api/v1/projects/{uuid4()}/public-team")
    assert response.status_code == 404


def test_public_team_goes_through_the_export_guard() -> None:
    project_id, contract, _ = make_wow_indlab_fixture()
    seen: dict = {}

    def fake_guard(members, report, mode, accepted):
        seen["members"] = [m.name for m in members]
        return [m for m in members if m.name != "Сомнительный Кандидат"], []

    contract.fidelity.team_structured = [
        TeamMember(name="Иванов Иван", role="Тимлид", project_area="", contributions=[]),
        TeamMember(name="Сомнительный Кандидат", role="", project_area="", contributions=["OCR"]),
    ]

    class Repo:
        async def get_contract(self, pid):
            return contract

    with patch("app.api.v1.contracts.get_contract_repository", return_value=Repo()), patch.object(
        public_team, "guard_team_for_export", fake_guard
    ):
        response = TestClient(app).get(f"/api/v1/projects/{project_id}/public-team")

    assert response.status_code == 200
    assert seen["members"] == ["Иванов Иван", "Сомнительный Кандидат"]
    assert [m["name"] for m in response.json()] == ["Иванов Иван"]


def test_team_block_fallback_skips_contribution_lines() -> None:
    members = public_team.members_from_team_bullets(
        ["Иванов Иван — Тимлид", "  · Руководил проектом", "Петрова Анна — Аналитик"]
    )
    assert [(m.name, m.role) for m in members] == [("Иванов Иван", "Тимлид"), ("Петрова Анна", "Аналитик")]


def test_publishable_team_uses_block_when_structured_is_empty() -> None:
    block = LandingBlock(key="team", title="Команда", content="", bullets=["Иванов Иван — Тимлид"])
    team = public_team.publishable_team(block, None)
    assert [m.name for m in team] == ["Иванов Иван"]
