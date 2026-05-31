"""Unit tests for showcase landing candidate URL builders (Stage P.6.2)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.domain import ProjectRecord
from app.schemas.landing_contract import ContractStatus, LandingContract
from app.services.showcase.showcase_landing_candidates import (
    build_landing_candidate,
    candidate_title_from_contract,
    export_html_url_for_project,
    is_valid_project_id,
    preview_url_for_project,
)
from app.services.showcase.showcase_safety import sanitize_url


def _record(name: str = "Demo", description: str | None = None) -> ProjectRecord:
    now = datetime.now(timezone.utc)
    return ProjectRecord(
        id=uuid4(),
        name=name,
        description=description,
        created_at=now,
        updated_at=now,
    )


def _contract(project_id, **kwargs) -> LandingContract:
    return LandingContract(
        project_id=project_id,
        status=ContractStatus.READY,
        updated_at=datetime.now(timezone.utc),
        **kwargs,
    )


def test_preview_url_for_project() -> None:
    pid = "abc-123"
    assert preview_url_for_project(pid) == f"/preview/{pid}"


def test_export_html_url_for_project() -> None:
    pid = "abc-123"
    assert export_html_url_for_project(pid) == f"/api/v1/projects/{pid}/export/html"


def test_landing_url_defaults_to_preview_url() -> None:
    record = _record()
    candidate = build_landing_candidate(record)
    assert candidate is not None
    assert candidate.landing_url == candidate.preview_url
    assert candidate.landing_url == preview_url_for_project(str(record.id))


def test_candidate_includes_preview_and_export_urls() -> None:
    record = _record("Endo")
    candidate = build_landing_candidate(record, has_landing=True)
    assert candidate is not None
    assert candidate.preview_url == f"/preview/{record.id}"
    assert candidate.export_html_url == f"/api/v1/projects/{record.id}/export/html"
    assert candidate.export_available is True


def test_candidate_title_from_contract() -> None:
    record = _record("Fallback name")
    contract = _contract(record.id, title="Эндокринология+", client="УИИ")
    candidate = build_landing_candidate(record, contract=contract)
    assert candidate is not None
    assert candidate.title == "Эндокринология+"
    assert candidate.client == "УИИ"
    assert candidate_title_from_contract(record, contract) == "Эндокринология+"


def test_candidate_description_from_contract_lead() -> None:
    record = _record()
    contract = _contract(record.id, lead="Лид-абзац")
    candidate = build_landing_candidate(record, contract=contract)
    assert candidate is not None
    assert candidate.description == "Лид-абзац"


def test_invalid_project_id_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _record()
    monkeypatch.setattr(
        "app.services.showcase.showcase_landing_candidates.is_valid_project_id",
        lambda _pid: False,
    )
    assert build_landing_candidate(record) is None


@pytest.mark.parametrize("preview_path", ["/preview/demo-id", "/preview/550e8400-e29b"])
def test_relative_preview_url_allowed_by_sanitize_url(preview_path: str) -> None:
    assert sanitize_url(preview_path) == preview_path


def test_missing_contract_uses_record_name_and_description() -> None:
    record = _record("Registry title", description="From registry")
    candidate = build_landing_candidate(record)
    assert candidate is not None
    assert candidate.title == "Registry title"
    assert candidate.description == "From registry"
    assert candidate.export_available is False
