#!/usr/bin/env python3
"""Generate a demo VR/AR Showcase HTML with three sample projects.

Usage (Windows PowerShell):
    cd C:\\Dima\\Projects\\CURSOR\\_uat\\ai-landing-factory-fresh\\backend
    ..\\.venv\\Scripts\\python.exe scripts\\export_showcase_demo.py

Output:
    backend/data/exports/showcase_demo.html
    backend/data/exports/vendor/aframe/aframe.min.js  (offline runtime copy)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter
from app.services.showcase.showcase_schema import (
    ShowcaseConfig,
    ShowcaseLayout,
    ShowcaseMode,
    ShowcaseProject,
    ShowcaseTheme,
)
from app.services.showcase.showcase_vendor import (
    ALLOWED_AFRAME_CDN,
    copy_aframe_vendor_to_export_dir,
    is_local_aframe_src,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("export_showcase_demo")

DEFAULT_OUTPUT = BACKEND / "data" / "exports" / "showcase_demo.html"


def build_demo_config() -> ShowcaseConfig:
    return ShowcaseConfig(
        title="AI Landing Factory — Витрина проектов",
        subtitle="VR/AR Showcase MVP · стенд выставки сгенерированных лендингов",
        organization="AI Landing Factory",
        layout=ShowcaseLayout.GALLERY_ARC,
        mode=ShowcaseMode.WEB3D,
        theme=ShowcaseTheme.UNIVERSITY,
        projects=[
            ShowcaseProject(
                id="endo",
                title="Эндокринология+",
                description=(
                    "Медицинский AI-ассистент: распознавание, диагностика и "
                    "поддержка принятия решений для врача-эндокринолога."
                ),
                demo_url="https://aistudio.google.com/",
                demo_label="AI Studio демо",
                landing_url="https://example.com/landings/endo",
                category="Medical AI",
                tags=["diagnostics", "copilot", "medical"],
                accent="#7C3AED",
            ),
            ShowcaseProject(
                id="indlab",
                title="Indlab News Assistant",
                description=(
                    "Телеграм-ассистент для мониторинга и аннотации отраслевых "
                    "новостей с фактчекингом."
                ),
                demo_url="https://aistudio.google.com/",
                demo_label="AI Studio демо",
                landing_url="https://example.com/landings/indlab",
                category="NLP",
                tags=["telegram", "news", "summarization"],
                accent="#3B82F6",
            ),
            ShowcaseProject(
                id="ksk",
                title="KSK Platform",
                description=(
                    "Платформа автоматизации барьер-контроля и сервисных заявок "
                    "для распределённых объектов."
                ),
                demo_url="https://aistudio.google.com/",
                demo_label="AI Studio демо",
                landing_url="https://example.com/landings/ksk",
                category="Platform",
                tags=["automation", "iot", "ops"],
                accent="#0EA5E9",
            ),
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Export demo VR/AR showcase HTML.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output HTML path (default: backend/data/exports/showcase_demo.html)",
    )
    parser.add_argument(
        "--aframe-src",
        default=None,
        help=(
            "Override A-Frame runtime URL. Default: local vendor/aframe/aframe.min.js. "
            f"CDN example: {ALLOWED_AFRAME_CDN}"
        ),
    )
    args = parser.parse_args()

    config = build_demo_config()
    exporter = ShowcaseHtmlExporter(aframe_src=args.aframe_src)
    result = exporter.export(config)

    output: Path = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.html, encoding="utf-8")

    vendor_path: Path | None = None
    if is_local_aframe_src(exporter._aframe_src):
        vendor_path = copy_aframe_vendor_to_export_dir(output)

    logger.info("Showcase demo exported")
    logger.info("  path=%s", output)
    logger.info("  aframe_src=%s", exporter._aframe_src)
    if vendor_path:
        logger.info("  vendor=%s", vendor_path)
    logger.info("  projects=%d mode=%s", result.project_count, result.mode)
    logger.info("  html_bytes=%d", len(result.html))
    if result.warnings:
        for warning in result.warnings:
            logger.info("  warning: %s", warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
