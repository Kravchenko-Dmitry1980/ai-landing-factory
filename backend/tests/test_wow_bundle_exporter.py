"""Tests for the Interactive WOW Bundle exporter (Stage P.7.2)."""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.export import wow_bundle_exporter
from app.services.export.wow_bundle_data import build_wow_bundle_data
from app.services.export.wow_bundle_exporter import (
    WowBundleExportOptions,
    build_wow_bundle_zip,
    build_wow_bundle_zip_with_meta,
    validate_cat_mascot_png,
)
from tests.fixtures.export_contract_fixture import (
    make_wow_indlab_fixture,
    patch_repo_with_fixture,
)


@pytest.fixture
def fake_assets(tmp_path: Path) -> Path:
    """A fake dist-wow/assets directory with placeholder bundle files."""
    assets = tmp_path / "assets"
    assets.mkdir(parents=True)
    (assets / "wow-app.js").write_text(
        "/*wow*/console.log('wow'); "
        "cat-assistant wow-hero-mascot wow-hero-mascot-rig wow-bundle-cat-mascot-v2",
        encoding="utf-8",
    )
    (assets / "wow-app.css").write_text(".wow{color:#fff}", encoding="utf-8")
    wow_dir = assets / "wow"
    wow_dir.mkdir(parents=True)
    (wow_dir / "cat-assistant.png").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 200)
    return assets


def _zip_names(data: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return zf.namelist()


def _zip_read(data: bytes, name: str) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return zf.read(name).decode("utf-8")


def test_zip_contains_index_html(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    assert "index.html" in _zip_names(data)


def test_zip_contains_wow_app_js(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    assert "assets/wow-app.js" in _zip_names(data)


def test_zip_contains_cat_mascot_png(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    names = _zip_names(data)
    assert "assets/wow/cat-assistant.png" in names
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        cat = zf.read("assets/wow/cat-assistant.png")
        assert len(cat) > 100
        assert cat.startswith(b"\x89PNG") or cat.startswith(b"\xff\xd8\xff")


def test_zip_js_contains_cat_mascot_markers(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    js = _zip_read(data, "assets/wow-app.js")
    assert "cat-assistant" in js
    assert "wow-hero-mascot" in js
    assert "wow-bundle-cat-mascot-v2" in js
    assert "wow-hero-mascot-rig" in js
    assert "PhoneStage" not in js
    assert "function Assistant" not in js


def test_zip_has_no_preview_mockup_assets(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    for name in _zip_names(data):
        lowered = name.lower()
        if lowered == "assets/wow/cat-assistant.png":
            continue
        for part in ("landing-preview", "screenshot", "hero-preview", "mockup"):
            assert part not in lowered, f"unexpected preview asset in ZIP: {name!r}"


def test_wide_landing_screenshot_png_is_rejected() -> None:
    # IHDR chunk with 1920x1080 dimensions inside a minimal PNG shell.
    wide_png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        + (1920).to_bytes(4, "big")
        + (1080).to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
    )
    with pytest.raises(ValueError, match="landing screenshot"):
        validate_cat_mascot_png(wide_png)


def test_stale_robot_bundle_is_rejected(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    assets.mkdir(parents=True)
    (assets / "wow-app.js").write_text(
        "PhoneStage function Assistant cat-assistant wow-hero-mascot wow-hero-mascot-rig wow-bundle-cat-mascot-v2",
        encoding="utf-8",
    )
    wow_dir = assets / "wow"
    wow_dir.mkdir(parents=True)
    (wow_dir / "cat-assistant.png").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 200)
    _, contract, _ = make_wow_indlab_fixture()
    with pytest.raises(ValueError, match="stale robot"):
        build_wow_bundle_zip(contract, assets_dir=assets)


def test_missing_cat_asset_fails(tmp_path: Path, monkeypatch) -> None:
    assets = tmp_path / "assets"
    assets.mkdir(parents=True)
    (assets / "wow-app.js").write_text(
        "cat-assistant wow-hero-mascot wow-hero-mascot-rig wow-bundle-cat-mascot-v2",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        wow_bundle_exporter,
        "CAT_MASCOT_SOURCE",
        tmp_path / "missing-cat.png",
    )
    _, contract, _ = make_wow_indlab_fixture()
    with pytest.raises(FileNotFoundError, match="cat mascot"):
        build_wow_bundle_zip(contract, assets_dir=assets)


def test_zip_contains_wow_app_css_if_exists(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    assert "assets/wow-app.css" in _zip_names(data)


def test_zip_omits_css_when_missing(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    assets.mkdir(parents=True)
    (assets / "wow-app.js").write_text(
        "cat-assistant wow-hero-mascot wow-hero-mascot-rig wow-bundle-cat-mascot-v2",
        encoding="utf-8",
    )
    wow_dir = assets / "wow"
    wow_dir.mkdir(parents=True)
    (wow_dir / "cat-assistant.png").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 200)
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=assets)
    names = _zip_names(data)
    assert "assets/wow-app.css" not in names
    # index.html must not reference a CSS file that is not in the ZIP.
    assert "wow-app.css" not in _zip_read(data, "index.html")


def test_zip_contains_data_json(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    assert "data/landing-contract.json" in _zip_names(data)


def test_zip_contains_readme(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    assert "README_DEMO.txt" in _zip_names(data)


def test_index_html_has_no_external_cdn(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    html = _zip_read(data, "index.html")
    # No external <script src> / <link href> pointing at a remote origin.
    assert not re.search(r'src=["\']https?://', html)
    assert not re.search(r'href=["\']https?://', html)
    assert "cdn" not in html.lower()


def test_index_html_embeds_wow_data_json(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    html = _zip_read(data, "index.html")
    assert 'id="wow-data"' in html
    assert 'type="application/json"' in html
    # The embedded JSON must carry the project title.
    assert "Indlab" in html


def test_malicious_title_is_escaped(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    contract.title = "<script>alert('xss')</script>Indlab"
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    html = _zip_read(data, "index.html")
    # The raw breakout sequence must never appear unescaped.
    assert "<script>alert('xss')</script>" not in html
    assert "alert('xss')" not in html or "\\u003c" in html


def test_javascript_demo_url_rejected(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(
        contract,
        WowBundleExportOptions(demo_url="javascript:alert(1)"),
        assets_dir=fake_assets,
    )
    payload = json.loads(_zip_read(data, "data/landing-contract.json"))
    assert "demo_url" not in payload["links"]
    assert "javascript:" not in _zip_read(data, "index.html")


def test_zip_has_no_absolute_paths(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    data = build_wow_bundle_zip(contract, assets_dir=fake_assets)
    for name in _zip_names(data):
        normalized = name.replace("\\", "/")
        assert not normalized.startswith("/")
        assert ".." not in normalized.split("/")


def test_bundle_data_has_at_least_four_metrics() -> None:
    _, contract, _ = make_wow_indlab_fixture()
    payload = build_wow_bundle_data(contract)
    assert len(payload["metrics"]) >= 4


def test_bundle_data_has_pipeline() -> None:
    _, contract, _ = make_wow_indlab_fixture()
    payload = build_wow_bundle_data(contract)
    assert len(payload["pipeline"]) >= 1
    assert all("title" in stage for stage in payload["pipeline"])


def test_export_endpoint_returns_zip(fake_assets: Path, monkeypatch) -> None:
    project_id, contract, landing = make_wow_indlab_fixture()
    monkeypatch.setattr(wow_bundle_exporter, "DEFAULT_ASSETS_DIR", fake_assets)

    class _Repo:
        pass

    repo = _Repo()
    patch_repo_with_fixture(repo, project_id, contract, landing)

    with patch("app.api.v1.projects.get_contract_repository", return_value=repo):
        client = TestClient(app)
        res = client.get(f"/api/v1/projects/{project_id}/export/wow-bundle")

    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    assert "assets/wow-app.js" in _zip_names(res.content)
    assert "assets/wow/cat-assistant.png" in _zip_names(res.content)


def test_missing_frontend_build_gives_clear_error(tmp_path: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    missing = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError) as exc:
        build_wow_bundle_zip_with_meta(contract, assets_dir=missing)
    message = str(exc.value)
    assert "npm run build:wow-bundle" in message


def test_meta_reports_metric_and_pipeline_counts(fake_assets: Path) -> None:
    _, contract, _ = make_wow_indlab_fixture()
    result = build_wow_bundle_zip_with_meta(contract, assets_dir=fake_assets)
    assert result.metric_count >= 4
    assert result.pipeline_count >= 1
    assert result.has_css is True
    assert result.has_cat_mascot is True
