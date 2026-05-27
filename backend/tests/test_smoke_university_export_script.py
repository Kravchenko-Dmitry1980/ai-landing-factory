"""Tests for smoke_university_export validation helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "smoke_university_export.py"


def _load_script():
    import sys

    spec = importlib.util.spec_from_file_location("smoke_university_export", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["smoke_university_export"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def smoke_mod():
    return _load_script()


def test_script_file_exists() -> None:
    assert SCRIPT_PATH.is_file()


def test_validate_offline_passes_university_sample(smoke_mod) -> None:
    html = """
    <!DOCTYPE html><html lang="ru"><head><title>Fixture</title><style>
    :root {
      --alf-bg: #ffffff;
      --alf-text: #111111;
      --alf-accent: #7C3AED;
      --bg: var(--alf-bg);
    }
    body { background: #ffffff; color: #111111; }
    .container { max-width: 1200px; margin: 0 auto; }
    section h2 { border-bottom: 1px solid #e5e7eb; }
    </style></head><body class='theme-university_platform'>
    <nav class='alf-section-nav'><a href='#team'>Команда</a></nav>
    <section><h2>Ключевые системы</h2>
      <div class="module-card">Module</div>
    </section>
    <section><h2>Используемый технологический стек</h2>
      <span class="stack-tag">Python</span>
    </section>
    <section id='essence'><details class='collapsible-section'><summary>More</summary></details></section>
    <section><h2>Команда проекта</h2>
      <div class="team-card">Member</div>
    </section>
    </body></html>
    """
    results = smoke_mod.validate_offline_university_export(html, expect_collapsible=True)
    failed = [r for r in results if not r.ok]
    assert not failed, [r.label for r in failed]


def test_validate_fails_dark_enterprise_sample(smoke_mod) -> None:
    html = """
    <!DOCTYPE html><html><head><title>Project Landing</title><style>
    :root {
      --bg: #0f1419;
      --surface: #1a2332;
      --text: #e8edf4;
    }
    body { background: var(--bg); color: var(--text); }
    .tagline { max-width: 720px; }
    .container { max-width: 1200px; }
    </style></head><body>
    <h1>Fixture</h1>
    Используемый технологический стек
    Команда проекта
    <span class="stack-tag">x</span><div class="team-card">y</div>
    </body></html>
    """
    results = smoke_mod.validate_offline_university_export(html, expect_collapsible=False)
    failed_labels = [r.label for r in results if not r.ok]
    assert any("dark" in label.lower() or "720px" in label or "Project Landing" in label for label in failed_labels)
    assert not all(r.ok for r in results)


def test_check_live_endo_markers_missing_token(smoke_mod) -> None:
    html = "<html><body><h1>Test</h1></body></html>"
    results = smoke_mod.validate_live_endo_export(html)
    assert all(not r.ok for r in results)
    assert any("GlaucoLogic" in r.label for r in results)


def test_check_university_style_requires_light_bg(smoke_mod) -> None:
    html = "<style>:root { --bg: #0f1419; }</style>"
    results = smoke_mod.check_university_style_markers(html)
    light = results[0]
    assert not light.ok
