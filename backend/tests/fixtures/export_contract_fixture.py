"""Synthetic contract + landing for export theme tests (no ENDO project)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.schemas.fidelity import FidelityMetadata, LandingModule, TeamMember
from app.schemas.generation import GeneratedLanding, LandingBlockContent
from app.schemas.landing_contract import (
    ContractStatus,
    LandingBlock,
    LandingContract,
    LandingStylePreset,
)
from app.schemas.style_config import LandingStyleConfigModel, LandingStyleProfile

LONG_ESSENCE_CHARS = 400


def make_export_fixture(
    *,
    style_config: LandingStyleConfigModel | None = None,
    presentation_style: str | None = "university_platform",
) -> tuple[UUID, LandingContract, GeneratedLanding]:
    project_id = uuid4()
    now = datetime.now(timezone.utc)
    blocks = [
        LandingBlock(
            key="tagline",
            title="Tagline",
            content="Demo landing for style export tests.",
            bullets=[],
        ),
        LandingBlock(
            key="essence",
            title="Essence",
            content="Synthetic fixture content.",
            bullets=[],
        ),
        LandingBlock(
            key="team",
            title="Team",
            content="",
            bullets=["Alex Dev — Lead"],
        ),
    ]
    contract = LandingContract(
        project_id=project_id,
        status=ContractStatus.DRAFT,
        style=LandingStylePreset.CORPORATE,
        title="Style Export Fixture",
        client="QA Lab",
        goals=["demo"],
        presentation_style=presentation_style,
        style_config=style_config,
        blocks=blocks,
        fidelity=FidelityMetadata(parser_mode="structured"),
        updated_at=now,
        version=1,
    )
    landing = GeneratedLanding(
        project_id=project_id,
        style=LandingStylePreset.CORPORATE,
        blocks=[
            LandingBlockContent(
                key="tagline",
                title="Tagline",
                body="Demo landing",
                bullets=[],
            )
        ],
        generated_at=now,
        prompt_version="test",
    )
    return project_id, contract, landing


def make_university_export_fixture(
    *,
    long_essence: bool = True,
) -> tuple[UUID, LandingContract, GeneratedLanding]:
    """Rich university_platform contract for offline export smoke (no live ENDO project)."""
    project_id = uuid4()
    now = datetime.now(timezone.utc)
    essence_content = (
        "Synthetic university platform essence for offline export validation. " * 12
        if long_essence
        else "Synthetic university platform essence."
    )
    style_config = LandingStyleConfigModel(profile=LandingStyleProfile.UNIVERSITY_PLATFORM)
    blocks = [
        LandingBlock(
            key="tagline",
            title="Tagline",
            content="Offline university platform export fixture.",
            bullets=[],
        ),
        LandingBlock(
            key="essence",
            title="Суть проекта",
            content=essence_content,
            bullets=[],
        ),
        LandingBlock(
            key="tasks",
            title="Задачи",
            content="",
            bullets=["Validate export", "Verify theme tokens", "Check anchor nav"],
        ),
        LandingBlock(
            key="team",
            title="Команда проекта",
            content="",
            bullets=["Research Lead — Principal Investigator"],
        ),
        LandingBlock(
            key="outlook",
            title="Outlook",
            content="",
            bullets=["Scale platform", "Publish research outcomes"],
        ),
    ]
    contract = LandingContract(
        project_id=project_id,
        status=ContractStatus.DRAFT,
        style=LandingStylePreset.CORPORATE,
        title="University Platform Export Fixture",
        client="QA Lab",
        goals=["offline-smoke"],
        presentation_style="university_platform",
        style_config=style_config,
        blocks=blocks,
        fidelity=FidelityMetadata(
            parser_mode="structured",
            modules=[
                LandingModule(
                    name="GlaucoLogic",
                    description="Clinical decision support module",
                    type="platform",
                ),
                LandingModule(
                    name="Copilot врача",
                    description="Physician assistant workflow",
                    type="ai",
                ),
                LandingModule(
                    name="VitaCalc",
                    description="Metabolic calculator",
                    type="tool",
                ),
            ],
            team_structured=[
                TeamMember(
                    name="Alice Researcher",
                    role="Lead Researcher",
                    project_area="Clinical AI",
                    contributions=["Protocol design", "Validation study"],
                ),
            ],
            tech_stack_grouped={
                "Backend": ["Python", "FastAPI"],
                "Frontend": ["React", "Next.js"],
                "Data": ["PostgreSQL"],
            },
        ),
        updated_at=now,
        version=1,
    )
    landing = GeneratedLanding(
        project_id=project_id,
        style=LandingStylePreset.CORPORATE,
        blocks=[
            LandingBlockContent(
                key="tagline",
                title="Tagline",
                body="Offline university export",
                bullets=[],
            ),
            LandingBlockContent(
                key="essence",
                title="Суть проекта",
                body=essence_content,
                bullets=[],
            ),
        ],
        generated_at=now,
        prompt_version="test",
    )
    return project_id, contract, landing


def make_wow_indlab_fixture() -> tuple[UUID, LandingContract, GeneratedLanding]:
    """Indlab-like news intelligence contract for WOW export tests.

    Contains extractable impact metrics (37 000+ posts, 17 models, 800+ topics)
    and a Telegram -> parsing -> embeddings -> Qdrant/Neo4j -> digest pipeline.
    """
    project_id = uuid4()
    now = datetime.now(timezone.utc)
    style_config = LandingStyleConfigModel(profile=LandingStyleProfile.TECH)
    blocks = [
        LandingBlock(
            key="tagline",
            title="Tagline",
            content="Платформа аналитики новостного потока в реальном времени.",
            bullets=[],
        ),
        LandingBlock(
            key="essence",
            title="Суть проекта",
            content=(
                "Система собирает и анализирует новостной поток из Telegram-каналов. "
                "Обработано 37 000+ постов, обучено 17 моделей, выделено 800+ тем. "
                "Проект реализован за 100 дней. Accuracy 92% на тестовой выборке."
            ),
            bullets=[],
        ),
        LandingBlock(
            key="tasks",
            title="Задачи",
            content="",
            bullets=[
                "Парсинг Telegram-каналов через Telethon",
                "Очистка и нормализация постов",
                "Построение эмбеддингов E5 и кластеризация тем",
                "Семантический поиск поверх Qdrant",
                "Ежедневный AI-дайджест",
            ],
        ),
        LandingBlock(
            key="results",
            title="Результаты",
            content="",
            bullets=[
                "Recall@5 0.87 на семантическом поиске",
                "Автоматический дайджест в Telegram-бот",
                "Граф связей тем в Neo4j",
            ],
        ),
        LandingBlock(
            key="team",
            title="Команда",
            content="",
            bullets=["Lead ML — руководитель"],
        ),
    ]
    contract = LandingContract(
        project_id=project_id,
        status=ContractStatus.DRAFT,
        style=LandingStylePreset.TECH,
        title="Indlab News Intelligence",
        client="Indlab",
        timeline="100 дней",
        lead="Lead ML",
        goals=["news-intelligence"],
        presentation_style="tech",
        style_config=style_config,
        blocks=blocks,
        fidelity=FidelityMetadata(
            parser_mode="structured",
            modules=[
                LandingModule(name="Telegram Ingestor",
                              description="Сбор постов из Telegram через Telethon",
                              type="ingestion"),
                LandingModule(name="Semantic Engine",
                              description="Эмбеддинги E5 + кластеризация тем",
                              type="ai"),
                LandingModule(name="Digest Builder",
                              description="Генерация ежедневного AI-дайджеста",
                              type="product"),
            ],
            team_structured=[
                TeamMember(name="Lead ML Engineer", role="ML Lead",
                           project_area="Semantics",
                           contributions=["Embeddings", "Clustering"]),
                TeamMember(name="Data Engineer", role="Data Engineer",
                           project_area="Ingestion",
                           contributions=["Telethon pipeline"]),
            ],
            tech_stack_grouped={
                "Sources": ["Telegram", "Telethon", "TGStat"],
                "Processing": ["Parser", "Очистка"],
                "Intelligence": ["E5", "LLM", "BERT"],
                "Storage": ["Qdrant", "Neo4j", "Postgres"],
                "Output": ["Digest", "Dashboard"],
            },
        ),
        updated_at=now,
        version=1,
    )
    landing = GeneratedLanding(
        project_id=project_id,
        style=LandingStylePreset.TECH,
        blocks=[
            LandingBlockContent(key="tagline", title="Tagline",
                                body="News intelligence", bullets=[]),
        ],
        generated_at=now,
        prompt_version="test",
    )
    return project_id, contract, landing


def patch_repo_with_fixture(repo, project_id: UUID, contract: LandingContract, landing: GeneratedLanding) -> None:
    """Monkeypatch async repo methods for TestClient export tests."""

    async def get_contract(pid: UUID):
        if pid == project_id:
            return contract
        return None

    async def get_landing(pid: UUID):
        if pid == project_id:
            return landing
        return None

    repo.get_contract = get_contract  # type: ignore[method-assign]
    repo.get_landing = get_landing  # type: ignore[method-assign]
