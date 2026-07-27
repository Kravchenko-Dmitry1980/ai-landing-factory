"""Regression tests for WOW bundle asset path resolution (Docker + dev)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.export import wow_bundle_exporter
from app.services.export.wow_bundle_exporter import (
    DEFAULT_ASSETS_DIR,
    resolve_wow_assets_dir,
)


def _write_fake_wow_assets(assets_dir: Path) -> None:
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "wow-app.js").write_text(
        "cat-assistant wow-hero-mascot wow-hero-mascot-rig wow-bundle-cat-mascot-v3",
        encoding="utf-8",
    )


def test_resolve_wow_assets_dir_prefers_explicit(tmp_path: Path) -> None:
    explicit = tmp_path / "custom" / "assets"
    _write_fake_wow_assets(explicit)
    assert resolve_wow_assets_dir(explicit) == explicit.resolve()


def test_resolve_wow_assets_dir_finds_docker_layout(tmp_path: Path, monkeypatch) -> None:
    docker_assets = tmp_path / "app" / "frontend" / "dist-wow" / "assets"
    _write_fake_wow_assets(docker_assets)

    monkeypatch.setattr(
        wow_bundle_exporter.settings,
        "backend_wow_assets_dir_env",
        "",
    )
    monkeypatch.setattr(
        wow_bundle_exporter,
        "_candidate_wow_assets_dirs",
        lambda: [docker_assets],
    )

    assert resolve_wow_assets_dir() == docker_assets.resolve()


def test_resolve_wow_assets_dir_honors_env_override(tmp_path: Path, monkeypatch) -> None:
    override = tmp_path / "override-assets"
    _write_fake_wow_assets(override)

    monkeypatch.setattr(
        wow_bundle_exporter.settings,
        "backend_wow_assets_dir_env",
        str(override),
    )

    assert resolve_wow_assets_dir() == override.resolve()


def test_resolve_wow_assets_dir_falls_back_to_default_when_missing(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        wow_bundle_exporter,
        "_candidate_wow_assets_dirs",
        lambda: [Path("/nonexistent/wow/assets")],
    )
    assert resolve_wow_assets_dir() == DEFAULT_ASSETS_DIR.resolve()


def test_dockerfile_declares_wow_bundle_build() -> None:
    dockerfile = (
        Path(__file__).resolve().parents[2]
        / "deploy"
        / "docker"
        / "backend.Dockerfile"
    )
    text = dockerfile.read_text(encoding="utf-8")
    assert "build:wow-bundle" in text
    assert "/app/frontend/dist-wow" in text
