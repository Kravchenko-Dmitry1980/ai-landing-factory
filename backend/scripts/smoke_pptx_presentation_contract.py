#!/usr/bin/env python3
"""Smoke test: PPTX project presentation → LandingContract synthesis."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.repositories.contract_repository import ContractRepository
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.extraction.dispatcher import DispatcherExtractionService
from app.services.export.export_theme import ExportTheme
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.services.generation.stub_generator import StubGenerationService
from app.services.pipeline.content_pipeline import ContentPipeline
from app.services.pipeline.pii_stage import PIIStageService
from app.services.prompts.engine import PromptEngine
from app.repositories.file_store import FileStore
from app.repositories.project_repository import ProjectRepository

DEFAULT_PROJECT_ID = "4b1b296d-bb61-41bd-bb83-d2dbb1814e70"


class SmokeFailure(Exception):
    pass


def _check(condition: bool, msg: str) -> None:
    if not condition:
        raise SmokeFailure(msg)
    print(f"  OK: {msg}")


async def run_smoke(project_id: UUID) -> None:
    repo = ContractRepository(settings)
    builder = ContractBuilderService(repo)

    extraction = await repo.get_extraction(project_id)
    _check(extraction is not None, "extraction exists")

    contract = await builder.reparse_structured(project_id)
    _check(contract is not None, "contract reparse")

    _check(
        contract.fidelity is not None
        and contract.fidelity.parser_mode == "project_presentation",
        f"parser_mode={contract.fidelity.parser_mode if contract.fidelity else None}",
    )

    score = contract.fidelity.completeness.score if contract.fidelity and contract.fidelity.completeness else 0
    _check(score >= 80, f"completeness score={score}")

    _check(
        contract.title and "Автоматизация открытия шлагбаума" in contract.title,
        f"title={contract.title!r}",
    )
    _check(contract.client and "КСК ИТ" in contract.client, f"client={contract.client!r}")

    modules = contract.fidelity.modules if contract.fidelity else []
    _check(len(modules) >= 5, f"modules={len(modules)}")

    grouped = contract.fidelity.tech_stack_grouped if contract.fidelity else {}
    flat = " ".join(item for items in grouped.values() for item in items).lower()
    for token in ("yolov8", "streamlit", "cvat"):
        _check(token in flat, f"stack contains {token}")

    team_n = len(contract.fidelity.team_structured) if contract.fidelity else 0
    _check(team_n >= 2, f"team={team_n}")

    print("\n--- Export university_platform ---")
    html = await StyledHtmlExporter(repo).to_html(
        project_id, theme=ExportTheme.UNIVERSITY_PLATFORM
    )
    for token in (
        "Автоматизация",
        "Используемый технологический стек",
        "Команда проекта",
        "max-width: 1200px",
    ):
        _check(token in html, f"export contains {token!r}")

    print("\n=== PPTX PRESENTATION SMOKE PASSED ===")


async def upload_and_run(pptx_path: Path) -> None:
    project = await ProjectRepository(settings).create("Smoke KSK IT PPTX", None)
    store = FileStore(settings)
    repo = ContractRepository(settings)
    pii_stage = PIIStageService(settings)
    pipeline = ContentPipeline(
        DispatcherExtractionService(store),
        ContractBuilderService(repo),
        StubGenerationService(PromptEngine(), repo),
        repo,
        pii_stage,
    )
    content = pptx_path.read_bytes()
    await store.save_upload(project.id, pptx_path.name, content, None)
    await pipeline.run_after_upload(project.id)
    await run_smoke(project.id)


def main() -> int:
    parser = argparse.ArgumentParser(description="PPTX presentation contract smoke")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--pptx", type=Path, default=None)
    args = parser.parse_args()

    try:
        if args.pptx:
            asyncio.run(upload_and_run(args.pptx))
        else:
            asyncio.run(run_smoke(UUID(args.project_id)))
        return 0
    except SmokeFailure as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
