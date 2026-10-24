from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.landing_contract import LandingBlock
from app.services.analysis.contract_builder import ContractBuilderService
from tests.fixtures.export_contract_fixture import make_wow_indlab_fixture

HEADER = {
    "title": "Новый заголовок",
    "timeline": "Март — май 2026",
    "lead": "Иван Петров",
    "quote": "Короткое описание проекта",
}


def test_patch_contract_passes_header_fields_to_builder() -> None:
    project_id, contract, _ = make_wow_indlab_fixture()
    calls: list[dict] = []

    class FakeBuilder:
        async def update_contract(self, pid, blocks=None, **fields):
            calls.append(fields)
            return contract

    touch = AsyncMock()
    with patch("app.api.v1.contracts.get_contract_builder", return_value=FakeBuilder()), patch(
        "app.api.v1.contracts._project_repo.touch", touch
    ):
        response = TestClient(app).patch(f"/api/v1/projects/{project_id}/contract", json=HEADER)

    assert response.status_code == 200
    assert {key: calls[0][key] for key in HEADER} == HEADER
    touch.assert_awaited_once_with(project_id)


def test_update_contract_writes_header_fields() -> None:
    project_id, contract, _ = make_wow_indlab_fixture()
    saved: list = []

    class Repo:
        async def get_contract(self, pid):
            return contract

        async def save_contract(self, c):
            saved.append(c)

    stub = SimpleNamespace(_repo=Repo(), _completeness_gate=SimpleNamespace(evaluate=lambda c: None))
    updated = asyncio.run(ContractBuilderService.update_contract(stub, project_id, None, **HEADER))

    assert updated is not None and saved
    for key, value in HEADER.items():
        assert getattr(updated, key) == value


def test_hand_edited_stack_drops_parsed_grouping() -> None:
    project_id, contract, _ = make_wow_indlab_fixture()
    contract.blocks = [b for b in contract.blocks if b.key != "tech_stack"] + [
        LandingBlock(key="tech_stack", title="Стек", content="", bullets=["Python"])
    ]
    contract.fidelity.tech_stack_grouped = {"AI": ["Python"]}

    class Repo:
        async def get_contract(self, pid):
            return contract

        async def save_contract(self, c):
            pass

    stub = SimpleNamespace(_repo=Repo(), _completeness_gate=SimpleNamespace(evaluate=lambda c: None))
    same = [b.model_copy() for b in contract.blocks]
    asyncio.run(ContractBuilderService.update_contract(stub, project_id, same))
    assert contract.fidelity.tech_stack_grouped == {"AI": ["Python"]}

    edited = [b.model_copy(update={"bullets": ["Python", "Rust"]}) if b.key == "tech_stack" else b for b in same]
    asyncio.run(ContractBuilderService.update_contract(stub, project_id, edited))
    assert contract.fidelity.tech_stack_grouped == {}
