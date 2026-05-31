"""Tests for the showcase registry storage service (Stage P.6).

All tests use a temp storage directory; nothing writes to the real
``backend/data/showcases`` tree.
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter
from app.services.showcase.showcase_registry import (
    ShowcaseNotFoundError,
    ShowcaseProjectNotFoundError,
    ShowcaseRegistry,
)
from app.services.showcase.showcase_schema import (
    ShowcaseCreateRequest,
    ShowcaseLayout,
    ShowcaseProjectCreateRequest,
    ShowcaseProjectUpdateRequest,
    ShowcaseTheme,
    ShowcaseUpdateRequest,
)
from app.services.showcase.showcase_vendor import VENDOR_SOURCE
from app.services.showcase.showcase_zip_exporter import build_showcase_zip_with_meta


@pytest.fixture()
def registry(tmp_path: Path) -> ShowcaseRegistry:
    return ShowcaseRegistry(base_dir=tmp_path / "showcases")


def _create(registry: ShowcaseRegistry, title: str = "Витрина"):
    return registry.create_showcase(ShowcaseCreateRequest(title=title))


def test_create_showcase(registry: ShowcaseRegistry) -> None:
    config = _create(registry, "Витрина AI")
    assert config.id
    assert config.title == "Витрина AI"
    assert config.created_at and config.updated_at
    assert config.projects == []


def test_list_showcases(registry: ShowcaseRegistry) -> None:
    _create(registry, "A")
    _create(registry, "B")
    summaries = registry.list_summaries()
    assert len(summaries) == 2
    assert {s.title for s in summaries} == {"A", "B"}


def test_get_showcase(registry: ShowcaseRegistry) -> None:
    config = _create(registry)
    fetched = registry.get_showcase(config.id)  # type: ignore[arg-type]
    assert fetched.id == config.id


def test_get_missing_raises(registry: ShowcaseRegistry) -> None:
    with pytest.raises(ShowcaseNotFoundError):
        registry.get_showcase("does-not-exist")


def test_update_showcase_settings(registry: ShowcaseRegistry) -> None:
    config = _create(registry)
    updated = registry.update_showcase(
        config.id,  # type: ignore[arg-type]
        ShowcaseUpdateRequest(
            title="Новое имя",
            layout=ShowcaseLayout.CIRCLE_BOOTHS,
            theme=ShowcaseTheme.TECH,
        ),
    )
    assert updated.title == "Новое имя"
    assert updated.layout == ShowcaseLayout.CIRCLE_BOOTHS
    assert updated.theme == ShowcaseTheme.TECH
    assert updated.updated_at >= config.updated_at  # type: ignore[operator]


def test_delete_showcase(registry: ShowcaseRegistry) -> None:
    config = _create(registry)
    assert registry.delete_showcase(config.id) is True  # type: ignore[arg-type]
    assert registry.delete_showcase(config.id) is False  # type: ignore[arg-type]
    assert registry.list_summaries() == []


def test_add_project(registry: ShowcaseRegistry) -> None:
    config = _create(registry)
    updated = registry.add_project(
        config.id,  # type: ignore[arg-type]
        ShowcaseProjectCreateRequest(
            title="Эндокринология+",
            demo_url="https://aistudio.google.com/",
            tags=["health", "ai"],
        ),
    )
    assert len(updated.projects) == 1
    project = updated.projects[0]
    assert project.title == "Эндокринология+"
    assert project.demo_url == "https://aistudio.google.com/"
    assert project.order_index == 0
    assert project.id


def test_update_project(registry: ShowcaseRegistry) -> None:
    config = _create(registry)
    config = registry.add_project(
        config.id, ShowcaseProjectCreateRequest(title="P1")  # type: ignore[arg-type]
    )
    pid = config.projects[0].id
    updated = registry.update_project(
        config.id,  # type: ignore[arg-type]
        pid,
        ShowcaseProjectUpdateRequest(title="P1-edited", category="Demo"),
    )
    assert updated.projects[0].title == "P1-edited"
    assert updated.projects[0].category == "Demo"


def test_update_missing_project_raises(registry: ShowcaseRegistry) -> None:
    config = _create(registry)
    with pytest.raises(ShowcaseProjectNotFoundError):
        registry.update_project(
            config.id,  # type: ignore[arg-type]
            "nope",
            ShowcaseProjectUpdateRequest(title="x"),
        )


def test_delete_project(registry: ShowcaseRegistry) -> None:
    config = _create(registry)
    config = registry.add_project(config.id, ShowcaseProjectCreateRequest(title="A"))  # type: ignore[arg-type]
    config = registry.add_project(config.id, ShowcaseProjectCreateRequest(title="B"))  # type: ignore[arg-type]
    pid = config.projects[0].id
    updated = registry.delete_project(config.id, pid)  # type: ignore[arg-type]
    assert len(updated.projects) == 1
    assert updated.projects[0].title == "B"
    assert updated.projects[0].order_index == 0


def test_reorder_projects(registry: ShowcaseRegistry) -> None:
    config = _create(registry)
    for title in ("A", "B", "C"):
        config = registry.add_project(
            config.id, ShowcaseProjectCreateRequest(title=title)  # type: ignore[arg-type]
        )
    ids = [p.id for p in config.projects]
    reordered = registry.reorder_projects(config.id, [ids[2], ids[0], ids[1]])  # type: ignore[arg-type]
    assert [p.title for p in reordered.projects] == ["C", "A", "B"]
    assert [p.order_index for p in reordered.projects] == [0, 1, 2]


def test_invalid_url_sanitized_to_none(registry: ShowcaseRegistry) -> None:
    config = _create(registry)
    updated = registry.add_project(
        config.id,  # type: ignore[arg-type]
        ShowcaseProjectCreateRequest(
            title="bad", demo_url="javascript:alert(1)", landing_url="/safe/path"
        ),
    )
    project = updated.projects[0]
    assert project.demo_url is None
    assert project.landing_url == "/safe/path"


def test_tags_capped(registry: ShowcaseRegistry) -> None:
    config = _create(registry)
    updated = registry.add_project(
        config.id,  # type: ignore[arg-type]
        ShowcaseProjectCreateRequest(
            title="t",
            tags=[f"tag{i}" for i in range(20)] + ["x" * 80],
        ),
    )
    tags = updated.projects[0].tags
    assert len(tags) <= 10
    assert all(len(tag) <= 40 for tag in tags)


def test_export_html_from_saved_showcase(registry: ShowcaseRegistry) -> None:
    config = _create(registry, "Экспорт")
    config = registry.add_project(
        config.id,  # type: ignore[arg-type]
        ShowcaseProjectCreateRequest(title="Проект", demo_url="https://aistudio.google.com/"),
    )
    saved = registry.get_showcase(config.id)  # type: ignore[arg-type]
    result = ShowcaseHtmlExporter().export(saved)
    assert result.html.startswith("<!DOCTYPE html>")
    assert result.project_count == 1
    assert "Проект" in result.html


@pytest.mark.skipif(not VENDOR_SOURCE.is_file(), reason="vendored runtime missing")
def test_export_zip_from_saved_showcase(registry: ShowcaseRegistry) -> None:
    config = _create(registry, "ZIP")
    for title in ("A", "B", "C"):
        config = registry.add_project(
            config.id, ShowcaseProjectCreateRequest(title=title)  # type: ignore[arg-type]
        )
    saved = registry.get_showcase(config.id)  # type: ignore[arg-type]
    result = build_showcase_zip_with_meta(saved)
    assert result.project_count == 3
    with zipfile.ZipFile(BytesIO(result.data)) as archive:
        names = set(archive.namelist())
    assert "showcase.html" in names
    assert "vendor/aframe/aframe.min.js" in names


def test_storage_writes_to_temp_dir_not_real_data(
    registry: ShowcaseRegistry, tmp_path: Path
) -> None:
    config = _create(registry)
    expected = tmp_path / "showcases" / f"{config.id}.json"
    assert expected.is_file()
