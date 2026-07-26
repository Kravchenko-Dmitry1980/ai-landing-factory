"""Pipeline map generation for the WOW landing export (Stage P.7).

Produces either a domain CV/FSM pipeline when the source text describes one,
or a 5-stage intelligence pipeline (Sources -> Processing -> Intelligence
-> Storage -> Output). Keyword detection promotes detected technologies into the
matching stage; otherwise a generic fallback pipeline is returned.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.fidelity import FidelityMetadata
from app.schemas.landing_contract import LandingContract


@dataclass(frozen=True)
class PipelineNode:
    """A single pipeline stage with a title and small tech tags."""

    title: str
    tags: list[str] = field(default_factory=list)


# Stage -> keyword stems (casefolded) that promote a tech tag into the stage.
_STAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sources": (
        "telegram", "tgstat", "telethon", "twitter", "rss", "vk",
        "источник", "парсинг каналов", "scraper", "crawler",
    ),
    "processing": (
        "parser", "parsing", "парсинг", "очистк", "cleaning", "normaliz",
        "нормализ", "preprocess", "etl", "tokeniz",
    ),
    "intelligence": (
        "embedding", "эмбеддинг", "bert", "e5", "llm", "gpt", "semantic",
        "семантик", "ner", "classif", "классифик", "vlm", "rerank",
    ),
    "storage": (
        "qdrant", "neo4j", "postgres", "redis", "elasticsearch", "clickhouse",
        "vector", "граф", "graph", "kafka", "s3",
    ),
    "output": (
        "digest", "дайджест", "dashboard", "дашборд", "analytics", "аналитик",
        "ui", "отчёт", "report", "api", "telegram bot", "бот",
    ),
}

_STAGE_TITLES: dict[str, str] = {
    "sources": "Источники",
    "processing": "Обработка",
    "intelligence": "AI-анализ",
    "storage": "Хранилище",
    "output": "Продукт",
}

_GENERIC_PIPELINE: tuple[PipelineNode, ...] = (
    PipelineNode("Источники данных", ["Data"]),
    PipelineNode("Обработка", ["Pipeline"]),
    PipelineNode("AI-анализ", ["ML"]),
    PipelineNode("Логика продукта", ["Service"]),
    PipelineNode("Вывод пользователю", ["UI"]),
)

_CV_PIPELINE: tuple[PipelineNode, ...] = (
    PipelineNode("Видеокадр", ["VMS", "camera"]),
    PipelineNode("YOLO v11 nano", ["detection"]),
    PipelineNode("ByteTrack", ["tracking"]),
    PipelineNode("Feature Extractor v3", ["features"]),
    PipelineNode("Random Forest / LSTM", ["classification"]),
    PipelineNode("Compliance Engine / FSM", ["rules"]),
    PipelineNode("Incident", ["alert"]),
    PipelineNode("CASHIER WATCH UI", ["dashboard"]),
)

_CV_SIGNAL_RE = re.compile(
    r"(yolo|bytetrack|cashier\s*watch|compliance\s*engine|\bfsm\b|"
    r"видеокадр|currency.?exchange|валютно.?обмен)",
    re.IGNORECASE,
)

_ARROW_SPLIT_RE = re.compile(r"\s*(?:→|->|=>|⇒)\s*")

_MAX_TAGS_PER_STAGE = 3


def _collect_tokens(contract: LandingContract) -> list[str]:
    """Flat list of short technology-ish tokens for keyword matching."""

    tokens: list[str] = []
    fidelity: FidelityMetadata | None = contract.fidelity
    if fidelity:
        for items in fidelity.tech_stack_grouped.values():
            tokens.extend(items)
        for module in fidelity.modules:
            tokens.append(module.name)
    for block in contract.blocks:
        if block.key in ("tech_stack", "inputs", "outputs", "essence", "tasks"):
            tokens.extend(block.bullets or [])
            if block.content:
                tokens.extend(block.content.split())
    # Deduplicate preserving order, keep concise tokens.
    seen: set[str] = set()
    out: list[str] = []
    for tok in tokens:
        clean = tok.strip().strip(".,;:()[]")
        if not clean or len(clean) > 40:
            continue
        low = clean.casefold()
        if low in seen:
            continue
        seen.add(low)
        out.append(clean)
    return out


def _full_text(contract: LandingContract) -> str:
    parts: list[str] = [contract.title or ""]
    for block in contract.blocks:
        parts.append(block.content or "")
        parts.extend(block.bullets or [])
    fidelity = contract.fidelity
    if fidelity:
        for items in fidelity.tech_stack_grouped.values():
            parts.extend(items)
        for module in fidelity.modules:
            parts.append(module.name)
            parts.append(module.description)
    return "\n".join(parts)


def _detect_cv_pipeline(text: str) -> list[PipelineNode] | None:
    """Return domain CV/FSM pipeline when the document describes one."""
    if not _CV_SIGNAL_RE.search(text):
        return None
    # Curated 8-card domain pipeline is preferred over fragile arrow parsing.
    return list(_CV_PIPELINE)


def build_pipeline(contract: LandingContract) -> list[PipelineNode]:
    """Build a domain or 5-stage pipeline; fall back to generic if sparse."""

    text = _full_text(contract)
    cv_nodes = _detect_cv_pipeline(text)
    if cv_nodes:
        return cv_nodes

    lowered = text.casefold()
    tokens = _collect_tokens(contract)

    stage_tags: dict[str, list[str]] = {stage: [] for stage in _STAGE_KEYWORDS}
    matched_stages = 0

    for stage, keywords in _STAGE_KEYWORDS.items():
        for token in tokens:
            low = token.casefold()
            if any(kw in low for kw in keywords):
                if token not in stage_tags[stage] and len(stage_tags[stage]) < _MAX_TAGS_PER_STAGE:
                    stage_tags[stage].append(token)
        # Also probe the full text for keywords not present as discrete tokens.
        if not stage_tags[stage]:
            for kw in keywords:
                if kw in lowered and len(kw) >= 4:
                    stage_tags[stage].append(kw.title())
                    break
        if stage_tags[stage]:
            matched_stages += 1

    # Require a meaningful detection signal before using the specific pipeline.
    if matched_stages < 3:
        return list(_GENERIC_PIPELINE)

    nodes: list[PipelineNode] = []
    for stage in ("sources", "processing", "intelligence", "storage", "output"):
        tags = stage_tags[stage]
        if not tags:
            tags = [_STAGE_TITLES[stage]]
        nodes.append(PipelineNode(title=_STAGE_TITLES[stage], tags=tags))
    return nodes
