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


def test_validate_passes_university_sample(smoke_mod) -> None:
    html = """
    <!DOCTYPE html><html lang="ru"><head><title>Эндокринология+</title><style>
    :root {
      --bg: #ffffff;
      --text: #111111;
      --accent: #7C3AED;
    }
    body { background: #ffffff; color: #111111; }
    .container { max-width: 1200px; margin: 0 auto; }
    section h2 { border-bottom: 1px solid #e5e7eb; }
    </style></head><body>
    <h1>Эндокринология+</h1>
    <section><h2>Ключевые системы</h2>
      <div>GlaucoLogic</div><div>Copilot врача</div><div>VitaCalc</div>
    </section>
    <section><h2>Используемый технологический стек</h2>
      <span class="stack-tag">Python</span>
    </section>
    <section><h2>Команда проекта</h2>
      <div class="team-card">Member</div>
    </section>
    </body></html>
    """
    results = smoke_mod.validate_university_export_html(html)
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
    <h1>Эндокринология+</h1>
    GlaucoLogic Copilot врача VitaCalc
    Используемый технологический стек
    Команда проекта
    <span class="stack-tag">x</span><div class="team-card">y</div>
    </body></html>
    """
    results = smoke_mod.validate_university_export_html(html)
    failed_labels = [r.label for r in results if not r.ok]
    assert any("dark" in label.lower() or "720px" in label or "Project Landing" in label for label in failed_labels)
    assert not all(r.ok for r in results)


def test_check_required_content_missing_token(smoke_mod) -> None:
    html = "<html><body><h1>Test</h1></body></html>"
    results = smoke_mod.check_required_content(html)
    assert all(not r.ok for r in results)
    assert any("GlaucoLogic" in r.label for r in results)


def test_check_university_style_requires_light_bg(smoke_mod) -> None:
    html = "<style>:root { --bg: #0f1419; }</style>"
    results = smoke_mod.check_university_style_markers(html)
    light = results[0]
    assert not light.ok
