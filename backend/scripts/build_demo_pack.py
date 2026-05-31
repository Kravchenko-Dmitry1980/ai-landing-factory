#!/usr/bin/env python3
"""Build the final demo pack (Stage P.8.2).

Assembles Interactive WOW ZIP, static WOW HTML, Showcase ZIP and standard
landing HTML into a timestamped ``demo_release_*`` folder with README and
checklists. Uses existing export services only — no new pipeline.

Usage (from repo root via PowerShell wrapper):
    .\\scripts\\build_demo_pack.ps1
    .\\scripts\\build_demo_pack.ps1 -ProjectId 8d1393c9-0803-4096-8ec9-8b4ca3ee7364
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

BACKEND = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from app.config import settings  # noqa: E402
from app.repositories.contract_repository import ContractRepository  # noqa: E402
from app.schemas.export_mode import Wow3dRuntime  # noqa: E402
from app.services.export.export_theme import ExportTheme  # noqa: E402
from app.services.export.styled_html_exporter import StyledHtmlExporter  # noqa: E402
from app.services.export.wow.wow_exporter import WowExportOptions, WowHtmlExporter  # noqa: E402
from app.services.export.wow_bundle_exporter import (  # noqa: E402
    ZIP_DOWNLOAD_FILENAME,
    build_wow_bundle_zip_with_meta,
)
from app.services.showcase.showcase_zip_exporter import build_showcase_zip_with_meta  # noqa: E402
from export_showcase_demo import build_demo_config  # noqa: E402
from tests.fixtures.export_contract_fixture import (  # noqa: E402
    make_wow_indlab_fixture,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("build_demo_pack")

INTERACTIVE_DIR = "01_interactive_wow_landing"
STATIC_DIR = "02_static_wow_landing"
SHOWCASE_DIR = "03_showcase_vr_ar"
STANDARD_DIR = "04_standard_landing"
CHECKS_DIR = "CHECKS"
OPTIONAL_DIR = "OPTIONAL"

STATIC_WOW_NAME = "wow_landing.html"
STANDARD_NAME = "standard_landing.html"
SHOWCASE_ZIP_NAME = "ai-showcase.zip"


def _git_value(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except OSError:
        pass
    return "unknown"


def _resolve_project_id(raw: str | None) -> tuple[UUID, str, str]:
    """Return (project_id, source_label, detail)."""

    if raw:
        return UUID(raw), "cli", raw

    last_path = ROOT / ".runtime" / "last_project.json"
    if last_path.is_file():
        data = json.loads(last_path.read_text(encoding="utf-8"))
        pid = data.get("project_id")
        if pid:
            return UUID(str(pid)), "last_project", str(pid)

    projects_path = settings.base_dir / "data" / "projects.json"
    if projects_path.is_file():
        registry = json.loads(projects_path.read_text(encoding="utf-8"))
        for key in sorted(registry.keys()):
            entry = registry[key]
            pid = entry.get("id") or key
            contract_path = settings.contracts_dir / f"{pid}.json"
            if contract_path.is_file():
                return UUID(str(pid)), "projects_registry", str(pid)

    _, contract, _ = make_wow_indlab_fixture()
    return contract.project_id, "synthetic_fixture", str(contract.project_id)


async def _load_contract(project_id: UUID):
    repo = ContractRepository(settings)
    contract = await repo.get_contract(project_id)
    landing = await repo.get_landing(project_id)
    return contract, landing


def _human_size(num_bytes: int) -> str:
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes} B"


def _write_readme(
    output_dir: Path,
    *,
    project_id: UUID,
    project_source: str,
    contract_title: str,
) -> None:
    text = f"""# Demo Pack — AI Landing Factory

Финальный демонстрационный комплект для офлайн-показа руководителю.
Собран автоматически скриптом `scripts/build_demo_pack.ps1`.

## 1. Что внутри

| Папка | Артефакт | Назначение |
|-------|----------|------------|
| `{INTERACTIVE_DIR}/` | `{ZIP_DOWNLOAD_FILENAME}` | Главный интерактивный WOW-лендинг с cat mascot |
| `{STATIC_DIR}/` | `{STATIC_WOW_NAME}` | Standalone WOW HTML (двойной клик) |
| `{SHOWCASE_DIR}/` | `{SHOWCASE_ZIP_NAME}` | VR/AR витрина проектов (A-Frame offline) |
| `{STANDARD_DIR}/` | `{STANDARD_NAME}` | Обычный стабильный export без WOW |
| `{CHECKS_DIR}/` | checklist + report | Контроль перед демо |

Проект сборки: `{project_id}` (источник: {project_source}).
Заголовок контракта: {contract_title}.

## 2. Что открыть первым

**`{INTERACTIVE_DIR}/{ZIP_DOWNLOAD_FILENAME}`** — распакуйте и откройте `index.html`.

## 3. Рекомендуемый порядок показа руководителю

1. **Interactive WOW Landing** — главный wow-ленд с котиком справа, KPI слева.
2. **Showcase VR/AR** — витрина проектов в 3D/2D.
3. **Standard Landing** — proof, что обычный export не сломан.
4. **Static WOW HTML** — fallback без ZIP/JS-сборки.

## 4. Как открыть Interactive WOW Landing

1. Распакуйте `{ZIP_DOWNLOAD_FILENAME}` целиком (папки `assets/`, `data/`).
2. Откройте `index.html` в Chrome или Edge.
3. Должны быть видны: светлый hero, текст слева, прозрачный cat mascot справа, анимация.

**Не должно быть:** ring, portal, robot, mini-landing, белая подложка под котом.

## 5. Как открыть Showcase VR/AR

1. Распакуйте `{SHOWCASE_ZIP_NAME}`.
2. Откройте `showcase.html`.
3. Должны быть видны: 3D-стенд (или 2D fallback), карточки проектов.

**Не должно быть:** CDN-ссылок на aframe.io для runtime (всё локально в `vendor/`).

## 6. Что делать, если браузер блокирует file://

Из папки с `index.html` или `showcase.html`:

```powershell
python -m http.server 8080
```

Затем откройте `http://localhost:8080/`.

## 7. Что требует интернет

- Demo-ссылки на AI Studio / внешние landing URL в Showcase (по клику).
- Любые внешние demo URL в CTA, если они указаны в контракте.

## 8. Что работает offline

- Interactive WOW ZIP после распаковки (JS, CSS, cat PNG, JSON inline).
- Static WOW HTML (cat встроен как data URI).
- Showcase ZIP runtime (A-Frame vendored локально).
- Standard landing HTML (self-contained).

## 9. Known limitations

- Interactive bundle — React/R3F esbuild; при `file://` некоторые браузеры могут
  ограничивать module scripts — используйте `python -m http.server`.
- Showcase 3D требует WebGL; без него виден 2D fallback.
- Standard export — university/enterprise профиль текущего проекта, не WOW.

## 10. Контрольный checklist перед демonstrацией

См. `{CHECKS_DIR}/DEMO_PACK_CHECKLIST.md`.
"""
    (output_dir / "README_DEMO_RU.md").write_text(text, encoding="utf-8")


def _write_checklist(output_dir: Path) -> None:
    text = """# Demo Pack Checklist

Отметьте перед показом руководителю.

## Interactive WOW

- [ ] index.html открывается
- [ ] котик виден справа
- [ ] котик без белой подложки
- [ ] нет ring / portal / robot / mini-landing
- [ ] анимация котика видна
- [ ] текст слева читается
- [ ] KPI не перекрыты

## Showcase

- [ ] showcase.html открывается
- [ ] A-Frame runtime локальный
- [ ] 2D fallback виден
- [ ] карточки проектов есть
- [ ] demo links кликабельны, если интернет доступен

## Standard

- [ ] standard_landing.html открывается
- [ ] обычный export не сломан
- [ ] нет WOW-зависимостей

## Static WOW

- [ ] wow_landing.html открывается
- [ ] cat mascot standalone
- [ ] нет белой плашки / mini landing

## Environment

- [ ] проверено без dev-сервера
- [ ] проверено после распаковки ZIP
- [ ] проверено в Chrome/Edge
"""
    checks = output_dir / CHECKS_DIR
    checks.mkdir(parents=True, exist_ok=True)
    (checks / "DEMO_PACK_CHECKLIST.md").write_text(text, encoding="utf-8")


def _write_report(
    output_dir: Path,
    *,
    project_id: UUID,
    project_source: str,
    contract_title: str,
    artifacts: list[tuple[str, Path]],
    gate_simple: str | None,
    gate_full: str | None,
    smoke_wow_bundle: str | None,
) -> None:
    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    commit = _git_value("rev-parse", "HEAD")
    branch = _git_value("rev-parse", "--abbrev-ref", "HEAD")

    lines = [
        "# Demo Pack Report",
        "",
        f"**Дата/время сборки:** {built_at}",
        f"**Git commit:** `{commit}`",
        f"**Git branch:** `{branch}`",
        f"**Project ID:** `{project_id}`",
        f"**Источник project_id:** {project_source}",
        f"**Заголовок контракта:** {contract_title}",
        f"**Output folder:** `{output_dir.name}`",
        "",
        "## Артефакты",
        "",
        "| Файл | Размер |",
        "|------|--------|",
    ]
    for label, path in artifacts:
        size = _human_size(path.stat().st_size) if path.is_file() else "—"
        rel = path.relative_to(output_dir).as_posix()
        lines.append(f"| `{rel}` | {size} |")

    lines.extend(
        [
            "",
            "## Release gates",
            "",
            f"- Simple (`release_check.ps1 -SkipFrontendBuild`): **{gate_simple or 'не запускался'}**",
            f"- Full (`release_check.ps1 -Full -SkipFrontendBuild`): **{gate_full or 'не запускался'}**",
            "",
            "## Smoke scripts",
            "",
            f"- WOW bundle smoke: **{smoke_wow_bundle or 'не запускался'}**",
            "- Demo pack smoke: см. `scripts/smoke_demo_pack.ps1`",
            "",
            "## Offline",
            "",
            "- Interactive WOW ZIP: да (после распаковки)",
            "- Static WOW HTML: да (data URI cat)",
            "- Showcase ZIP: да (vendored A-Frame)",
            "- Standard HTML: да",
            "",
            "## Интернет",
            "",
            "- Demo/landing URL в Showcase cards (по клику)",
            "- Внешние CTA demo links при наличии в контракте",
            "",
            "## Known limitations",
            "",
            "- `file://` может ограничивать module scripts — используйте static server.",
            "- Showcase 3D требует WebGL.",
            "",
            "## Final verdict",
            "",
            "**PENDING** — обновится после `smoke_demo_pack.ps1`.",
            "",
        ]
    )
    checks = output_dir / CHECKS_DIR
    checks.mkdir(parents=True, exist_ok=True)
    (checks / "DEMO_PACK_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


async def _build_async(
    output_dir: Path,
    project_id: UUID,
    project_source: str,
    *,
    gate_simple: str | None,
    gate_full: str | None,
    smoke_wow_bundle: str | None,
) -> None:
    contract, landing = await _load_contract(project_id)
    use_fixture_repo = False
    if contract is None:
        logger.warning(
            "Contract for %s not found — using synthetic Indlab fixture", project_id
        )
        _, contract, landing = make_wow_indlab_fixture()
        project_source = "synthetic_fixture"
        use_fixture_repo = True

    if use_fixture_repo:

        class _FixtureRepo:
            async def get_contract(self, _pid):
                return contract

            async def get_landing(self, _pid):
                return landing

        repo: ContractRepository | _FixtureRepo = _FixtureRepo()
    else:
        repo = ContractRepository(settings)

    output_dir.mkdir(parents=True, exist_ok=True)
    for sub in (INTERACTIVE_DIR, STATIC_DIR, SHOWCASE_DIR, STANDARD_DIR, CHECKS_DIR):
        (output_dir / sub).mkdir(parents=True, exist_ok=True)
    (output_dir / OPTIONAL_DIR).mkdir(parents=True, exist_ok=True)

    # A. Interactive WOW ZIP
    wow_zip_path = output_dir / INTERACTIVE_DIR / ZIP_DOWNLOAD_FILENAME
    wow_result = build_wow_bundle_zip_with_meta(contract)
    wow_zip_path.write_bytes(wow_result.data)
    logger.info("Interactive WOW ZIP: %s (%s)", wow_zip_path, _human_size(len(wow_result.data)))

    # B. Static WOW HTML
    static_html = await WowHtmlExporter(repo).to_html(
        contract.project_id,
        theme=ExportTheme.TECH,
        options=WowExportOptions(runtime=Wow3dRuntime.NONE),
    )
    static_path = output_dir / STATIC_DIR / STATIC_WOW_NAME
    static_path.write_text(static_html, encoding="utf-8")
    logger.info("Static WOW HTML: %s", static_path)

    # C. Showcase ZIP
    showcase_path = output_dir / SHOWCASE_DIR / SHOWCASE_ZIP_NAME
    showcase_result = build_showcase_zip_with_meta(build_demo_config())
    showcase_path.write_bytes(showcase_result.data)
    logger.info("Showcase ZIP: %s (%s)", showcase_path, _human_size(len(showcase_result.data)))

    # D. Standard landing HTML
    theme = ExportTheme.UNIVERSITY_PLATFORM
    if contract.presentation_style and "tech" in str(contract.presentation_style).lower():
        theme = ExportTheme.TECH
    standard_html = await StyledHtmlExporter(repo).to_html(
        contract.project_id,
        theme=theme,
    )
    standard_path = output_dir / STANDARD_DIR / STANDARD_NAME
    standard_path.write_text(standard_html, encoding="utf-8")
    logger.info("Standard HTML: %s", standard_path)

    artifacts = [
        ("interactive_wow_zip", wow_zip_path),
        ("static_wow_html", static_path),
        ("showcase_zip", showcase_path),
        ("standard_html", standard_path),
    ]

    _write_readme(
        output_dir,
        project_id=contract.project_id,
        project_source=project_source,
        contract_title=contract.title or "AI Landing",
    )
    _write_checklist(output_dir)
    _write_report(
        output_dir,
        project_id=contract.project_id,
        project_source=project_source,
        contract_title=contract.title or "AI Landing",
        artifacts=artifacts,
        gate_simple=gate_simple,
        gate_full=gate_full,
        smoke_wow_bundle=smoke_wow_bundle,
    )

    meta = {
        "output_dir": str(output_dir),
        "project_id": str(contract.project_id),
        "project_source": project_source,
        "artifacts": {name: str(path) for name, path in artifacts},
    }
    (output_dir / "demo_pack_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Demo pack ready: %s", output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build final demo pack (P.8.2)")
    parser.add_argument("--project-id", default=None, help="Project UUID (optional)")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: demo_release_YYYYMMDD_HHMM)",
    )
    parser.add_argument("--gate-simple", default=None, help="Simple gate result label")
    parser.add_argument("--gate-full", default=None, help="Full gate result label")
    parser.add_argument("--smoke-wow-bundle", default=None, help="WOW bundle smoke label")
    args = parser.parse_args()

    if args.output_dir:
        output_dir = args.output_dir.resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_dir = (ROOT / f"demo_release_{stamp}").resolve()

    if output_dir.exists() and any(output_dir.iterdir()):
        logger.error(
            "Output directory already exists and is not empty: %s. "
            "Remove it or pass --output-dir with a new path.",
            output_dir,
        )
        return 1

    project_id, project_source, _ = _resolve_project_id(args.project_id)
    logger.info("Using project_id=%s (source=%s)", project_id, project_source)
    logger.info("Output: %s", output_dir)

    asyncio.run(
        _build_async(
            output_dir,
            project_id,
            project_source,
            gate_simple=args.gate_simple,
            gate_full=args.gate_full,
            smoke_wow_bundle=args.smoke_wow_bundle,
        )
    )
    print(f"DEMO_PACK_OUTPUT={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
