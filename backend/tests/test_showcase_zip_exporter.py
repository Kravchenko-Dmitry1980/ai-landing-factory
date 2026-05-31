"""Tests for portable VR/AR Showcase ZIP export (Stage P.5.2)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.showcase.showcase_schema import ShowcaseConfig, ShowcaseProject
from app.services.showcase.showcase_vendor import (
    DEFAULT_AFRAME_SRC,
    VENDOR_LICENSE,
    VENDOR_SOURCE,
    ZIP_AFRAME_ENTRY,
    ZIP_HTML_NAME,
    ZIP_LICENSE_ENTRY,
)
from app.services.showcase.showcase_zip_exporter import build_showcase_zip_with_meta


def _project(**overrides) -> ShowcaseProject:
    base = dict(
        id="p1",
        title="Проект",
        description="Описание.",
        demo_url="https://aistudio.google.com/",
        landing_url="/landings/p1",
    )
    base.update(overrides)
    return ShowcaseProject(**base)


def _config(projects: list[ShowcaseProject]) -> ShowcaseConfig:
    return ShowcaseConfig(title="ZIP Витрина", projects=projects)


def _read_zip(data: bytes) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(data))


@pytest.mark.skipif(not VENDOR_SOURCE.is_file(), reason="vendored runtime missing")
def test_zip_has_expected_files() -> None:
    result = build_showcase_zip_with_meta(_config([_project()]))
    with _read_zip(result.data) as archive:
        names = set(archive.namelist())
    assert names == {ZIP_HTML_NAME, ZIP_AFRAME_ENTRY, ZIP_LICENSE_ENTRY}


@pytest.mark.skipif(not VENDOR_SOURCE.is_file(), reason="vendored runtime missing")
def test_html_references_local_vendor_path() -> None:
    result = build_showcase_zip_with_meta(_config([_project()]))
    with _read_zip(result.data) as archive:
        html = archive.read(ZIP_HTML_NAME).decode("utf-8")
    assert f'src="{DEFAULT_AFRAME_SRC}"' in html
    assert "aframe.io/releases" not in html


@pytest.mark.skipif(not VENDOR_SOURCE.is_file(), reason="vendored runtime missing")
def test_zip_does_not_contain_absolute_paths() -> None:
    result = build_showcase_zip_with_meta(_config([_project()]))
    with _read_zip(result.data) as archive:
        for name in archive.namelist():
            normalized = name.replace("\\", "/")
            assert not normalized.startswith("/")
            assert ".." not in normalized.split("/")
            assert not (len(normalized) > 1 and normalized[1] == ":")


@pytest.mark.skipif(not VENDOR_SOURCE.is_file(), reason="vendored runtime missing")
def test_unsafe_project_text_escaped_in_zip_html() -> None:
    config = _config([_project(title="<script>alert('xss')</script>")])
    result = build_showcase_zip_with_meta(config)
    with _read_zip(result.data) as archive:
        html = archive.read(ZIP_HTML_NAME).decode("utf-8")
    assert "<script>alert('xss')</script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.skipif(not VENDOR_SOURCE.is_file(), reason="vendored runtime missing")
def test_unsafe_demo_url_removed_from_zip_html() -> None:
    config = _config([_project(demo_url="javascript:alert(1)", landing_url=None)])
    result = build_showcase_zip_with_meta(config)
    with _read_zip(result.data) as archive:
        html = archive.read(ZIP_HTML_NAME).decode("utf-8")
    assert "javascript:alert(1)" not in html
    assert any("demo_url rejected" in w for w in result.warnings)


def test_missing_vendor_runtime_raises_clear_error(tmp_path: Path) -> None:
    config = _config([_project()])
    fake_vendor = tmp_path / "missing" / "aframe.min.js"
    with patch(
        "app.services.showcase.showcase_zip_exporter.VENDOR_SOURCE",
        fake_vendor,
    ):
        with pytest.raises(FileNotFoundError, match="Vendored A-Frame assets missing"):
            build_showcase_zip_with_meta(config)


@pytest.mark.skipif(not VENDOR_SOURCE.is_file(), reason="vendored runtime missing")
def test_vendor_runtime_and_license_copied_into_zip() -> None:
    result = build_showcase_zip_with_meta(_config([_project()]))
    with _read_zip(result.data) as archive:
        runtime = archive.read(ZIP_AFRAME_ENTRY)
        license_text = archive.read(ZIP_LICENSE_ENTRY).decode("utf-8")
    assert len(runtime) == VENDOR_SOURCE.stat().st_size
    assert "MIT" in license_text
    assert "A-Frame 1.7.0" in license_text
    assert len(license_text) >= VENDOR_LICENSE.stat().st_size - 4
