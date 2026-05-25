#!/usr/bin/env python3
"""Acceptance smoke test for Эндокринология+ structured landing."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.repositories.contract_repository import ContractRepository
from app.repositories.domain_repository import DomainRepository
from app.services.analysis.contract_builder import ContractBuilderService
from app.services.domain.engine import DomainIntelligenceEngine
from app.services.export.styled_html_exporter import StyledHtmlExporter
from app.services.generation.unified_generator import UnifiedGenerationService
from app.services.generation.stub_generator import StubGenerationService
from app.services.analysis.llm_contract_builder import LLMContractBuilderService
from app.services.pipeline.pii_stage import PIIStageService
from app.services.prompts.engine import PromptEngine
from app.services.semantic.generator import SemanticGenerationEngine
from app.services.pii.safe_payload import SafeCloudPayloadService
from app.services.pii.report import to_public_report

DEFAULT_PROJECT_ID = "55a98f90-73fc-4d26-a477-3c974a0cbeed"

MEDICAL_DOMAINS = {"medical_ai", "speech_ai", "document_ai", "multi_agent_system", "rag_system"}
ARCHETYPE_TARGETS = {
    "AI Copilot",
    "Decision Support System",
    "Recommendation Engine",
    "Realtime Speech Pipeline",
}
PATTERN_KEYWORDS = (
    "rag",
    "speech",
    "human-in-the-loop",
    "clinical decision support",
    "multi-agent",
)


class SmokeFailure(Exception):
    pass


def _check(condition: bool, msg: str) -> None:
    if not condition:
        raise SmokeFailure(msg)
    print(f"  OK: {msg}")


async def run_acceptance(project_id: UUID) -> None:
    repo = ContractRepository(settings)
    builder = ContractBuilderService(repo)
    pii_stage = PIIStageService(settings)

    extraction = await repo.get_extraction(project_id)
    _check(extraction is not None, "extraction exists")

    contract = await builder.reparse_structured(project_id)
    _check(contract is not None, "contract reparse")

    _check(contract.title == "Эндокринология+", f"title={contract.title!r}")
    _check(bool(contract.client), "client not empty")
    _check(
        contract.timeline and ("февраль" in contract.timeline.lower() or "апрель" in contract.timeline.lower()),
        f"timeline={contract.timeline!r}",
    )
    _check(bool(contract.lead), "lead not empty")

    essence = next(b for b in contract.blocks if b.key == "essence")
    _check(len(essence.content) >= 800, f"essence length={len(essence.content)}")

    modules = [m.name for m in (contract.fidelity.modules if contract.fidelity else [])]
    for name in ("GlaucoLogic", "Copilot врача", "VitaCalc"):
        _check(name in modules, f"module {name}")

    tasks = next(b for b in contract.blocks if b.key == "tasks").bullets
    purpose = next(b for b in contract.blocks if b.key == "purpose").bullets
    inputs = next(b for b in contract.blocks if b.key == "inputs").bullets
    outputs = next(b for b in contract.blocks if b.key == "outputs").bullets
    results = next(b for b in contract.blocks if b.key == "results").bullets
    outlook = next(b for b in contract.blocks if b.key == "outlook").bullets

    _check(len(tasks) >= 8, f"tasks={len(tasks)}")
    _check(len(purpose) >= 5, f"purpose={len(purpose)}")
    _check(len(inputs) >= 5, f"inputs={len(inputs)}")
    _check(len(outputs) >= 7, f"outputs={len(outputs)}")
    _check(len(results) >= 8, f"results={len(results)}")
    _check(len(outlook) >= 6, f"outlook={len(outlook)}")

    stack_cats = len(contract.fidelity.tech_stack_grouped) if contract.fidelity else 0
    _check(stack_cats >= 5, f"tech_stack categories={stack_cats}")

    team_n = len(contract.fidelity.team_structured) if contract.fidelity else 0
    _check(team_n >= 15, f"team={team_n}")

    score = contract.fidelity.completeness.score if contract.fidelity and contract.fidelity.completeness else 0
    _check(score >= 85, f"completeness score={score}")

    print("\n--- PII ---")
    report, _ = await pii_stage.prescan(extraction)
    _check(report.has_pii and report.redaction_count > 0, f"PII detected count={report.redaction_count}")
    public = to_public_report(report)
    dumped = public.model_dump_json()
    _check("Кравченко" not in dumped and "@" not in dumped.split("placeholder")[0], "public report has no raw PII")

    llm = LLMContractBuilderService(settings, repo, builder, pii_stage=pii_stage)
    preview = await SafeCloudPayloadService(settings, pii_stage).build_preview(
        project_id, extraction, report, llm
    )
    _check(preview.safe_for_cloud, "safe cloud payload")
    _check("Кравченко" not in preview.preview_text_redacted, "cloud preview redacted")

    print("\n--- Domain / Architecture ---")
    domain_repo = DomainRepository(settings)
    domain_engine = DomainIntelligenceEngine(settings, domain_repo, pii_stage)
    domain_report = await domain_engine.analyze(contract, force=True)
    primary = domain_report.graph.domain_profile.primary_domain.value
    _check(
        any(m in primary for m in ("medical", "speech", "rag", "multi")),
        f"primary_domain={primary}",
    )

    arch_types = {a.archetype for a in domain_report.graph.system_archetypes}
    matched_arch = ARCHETYPE_TARGETS & arch_types
    _check(len(matched_arch) >= 2, f"archetypes matched={matched_arch}")

    patterns = " ".join(p.pattern for p in domain_report.graph.architecture_patterns).lower()
    pat_hits = sum(1 for k in PATTERN_KEYWORDS if k in patterns)
    _check(pat_hits >= 2, f"pattern hits={pat_hits}")

    semantic_engine = SemanticGenerationEngine(
        settings, repo, pii_stage, PromptEngine(), domain_engine
    )
    stub = StubGenerationService(PromptEngine(), repo)
    unified = UnifiedGenerationService(semantic_engine, stub, llm, domain_engine)
    gen = await unified.generate_full(project_id, enrich=False)
    arch = gen.semantic.architecture
    _check(arch is not None and len(arch.nodes) >= 5, f"architecture nodes={len(arch.nodes) if arch else 0}")
    _check(arch is not None and len(arch.edges) >= 3, f"architecture edges={len(arch.edges) if arch else 0}")
    layers = {n.layer for n in arch.nodes} if arch else set()
    _check(any("ai" in str(l).lower() for l in layers), f"AI layer in {layers}")
    _check(any("backend" in str(l).lower() or "data" in str(l).lower() for l in layers), f"backend/data layer")

    print("\n--- Export ---")
    html = await StyledHtmlExporter(repo).to_html(project_id)
    for token in (
        "Эндокринология+",
        "GlaucoLogic",
        "Copilot врача",
        "VitaCalc",
        "Используемый технологический стек",
        "Команда проекта",
        "team-card",
        "stack-tag",
        "max-width: 1200px",
    ):
        _check(token in html, f"export contains {token!r}")
    _check("max-width:720px" not in html, "not legacy 720px fallback")

    print("\n=== ENDOCRINOLOGY ACCEPTANCE PASSED ===")


async def upload_and_run(docx_path: Path) -> None:
    from app.repositories.project_repository import ProjectRepository
    from app.repositories.file_store import FileStore
    from app.services.extraction.dispatcher import DispatcherExtractionService
    from app.services.pipeline.content_pipeline import ContentPipeline

    project = await ProjectRepository(settings).create("Smoke Endocrinology", None)
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
    content = docx_path.read_bytes()
    await store.save_upload(project.id, docx_path.name, content, None)
    await pipeline.run_after_upload(project.id)
    await run_acceptance(project.id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Endocrinology acceptance smoke")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--docx", type=Path, default=None)
    args = parser.parse_args()

    try:
        if args.docx:
            asyncio.run(upload_and_run(args.docx))
        else:
            asyncio.run(run_acceptance(UUID(args.project_id)))
        return 0
    except SmokeFailure as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
