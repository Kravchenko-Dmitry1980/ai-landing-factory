"""Impact metric extraction for the WOW landing export (Stage P.7).

Pulls "exhibition" numbers out of contract text (e.g. ``37 000+ posts``,
``17 models``, ``800+ topics``) and complements them with derived counts so the
WOW export always renders at least four metric cards.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.schemas.fidelity import FidelityMetadata
from app.schemas.landing_contract import LandingContract

logger = logging.getLogger(__name__)

MIN_METRIC_CARDS = 4
MAX_METRIC_CARDS = 6


@dataclass(frozen=True)
class WowMetric:
    """A single impact metric card."""

    label: str
    value: str
    hint: str = ""
    source: str = "extracted"  # extracted | derived | fallback


# Number token: "37 000+", "37000", "800+", "17", "92%", "0.87".
_NUM_RE = re.compile(
    r"(?P<num>\d{1,3}(?:[ \u00a0]\d{3})+\s*\+?"  # grouped thousands
    r"|\d+(?:[.,]\d+)?\s*%"  # percentage
    r"|\d+\s*\+"  # "800+"
    r"|\d+)"  # plain integer
    r"\s*(?P<unit>[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9@\-]*)?"
)

# Stem -> human label/hint. Order matters (longer stems first per group).
_CONTEXT_UNITS: tuple[tuple[str, str], ...] = (
    ("постов", "постов в корпусе"),
    ("посты", "постов в корпусе"),
    ("пост", "постов в корпусе"),
    ("post", "posts ingested"),
    ("сообщени", "сообщений"),
    ("message", "messages"),
    ("модел", "AI-моделей"),
    ("model", "AI models"),
    ("тем", "тем / кластеров"),
    ("topic", "topics"),
    ("кластер", "кластеров"),
    ("cluster", "clusters"),
    ("канал", "каналов-источников"),
    ("channel", "source channels"),
    ("источник", "источников данных"),
    ("source", "data sources"),
    ("дн", "дней разработки"),
    ("day", "days"),
    ("недел", "недель"),
    ("week", "weeks"),
    ("сервис", "сервисов"),
    ("service", "services"),
    ("контейнер", "контейнеров"),
    ("container", "containers"),
    ("пользовател", "пользователей"),
    ("user", "users"),
    ("документ", "документов"),
    ("document", "documents"),
    ("запрос", "запросов"),
    ("query", "queries"),
)

# Product/quality metric keywords -> label. Detected with a nearby number.
_PRODUCT_METRICS: tuple[tuple[str, str], ...] = (
    ("recall@", "Recall@k"),
    ("recall", "Recall"),
    ("precision", "Precision"),
    ("accuracy", "Accuracy"),
    ("точность", "Точность"),
    ("mrr", "MRR"),
    ("ndcg", "nDCG"),
    ("f1", "F1"),
    ("latency", "Latency"),
)


def _normalize_value(raw: str) -> str:
    """Compact a captured number token to a tidy display value."""

    token = raw.strip().replace("\u00a0", " ")
    token = re.sub(r"\s+\+", "+", token)
    token = re.sub(r"\s+%", "%", token)
    token = re.sub(r"\s{2,}", " ", token)
    return token


def _numeric_weight(value: str) -> float:
    digits = re.sub(r"[^\d.]", "", value.replace(" ", ""))
    try:
        return float(digits) if digits else 0.0
    except ValueError:
        return 0.0


def _collect_text(contract: LandingContract) -> str:
    parts: list[str] = []
    if contract.title:
        parts.append(contract.title)
    for block in contract.blocks:
        if block.content:
            parts.append(block.content)
        parts.extend(block.bullets or [])
    fidelity: FidelityMetadata | None = contract.fidelity
    if fidelity:
        for module in fidelity.modules:
            parts.append(module.name)
            parts.append(module.description)
        for member in fidelity.team_structured:
            parts.append(member.role)
            parts.append(member.project_area)
            parts.extend(member.contributions or [])
        for items in fidelity.tech_stack_grouped.values():
            parts.extend(items)
    return "\n".join(p for p in parts if p)


def _match_unit(unit: str) -> str | None:
    lowered = unit.casefold()
    for stem, label in _CONTEXT_UNITS:
        if lowered.startswith(stem):
            return label
    return None


def _extract_context_metrics(text: str) -> list[WowMetric]:
    found: dict[str, WowMetric] = {}
    for match in _NUM_RE.finditer(text):
        unit = match.group("unit")
        if not unit:
            continue
        label = _match_unit(unit)
        if not label:
            continue
        value = _normalize_value(match.group("num"))
        # Ignore trivially small counts for "impact" framing.
        if _numeric_weight(value) < 3 and "%" not in value:
            continue
        key = label
        if key not in found or _numeric_weight(value) > _numeric_weight(found[key].value):
            found[key] = WowMetric(label=label, value=value, source="extracted")
    return list(found.values())


def _extract_product_metrics(text: str) -> list[WowMetric]:
    lowered = text.casefold()
    out: list[WowMetric] = []
    seen: set[str] = set()
    for keyword, label in _PRODUCT_METRICS:
        idx = lowered.find(keyword)
        if idx < 0 or label in seen:
            continue
        window = text[idx : idx + len(keyword) + 16]
        num = re.search(r"\d+(?:[.,]\d+)?\s*%?", window)
        if not num:
            continue
        seen.add(label)
        out.append(
            WowMetric(
                label=label,
                value=_normalize_value(num.group(0)),
                hint="качество модели",
                source="extracted",
            )
        )
    return out


def _derived_metrics(contract: LandingContract) -> list[WowMetric]:
    fidelity: FidelityMetadata | None = contract.fidelity
    blocks = {b.key: b for b in contract.blocks}
    out: list[WowMetric] = []

    modules_count = len(fidelity.modules) if fidelity else 0
    if modules_count:
        out.append(
            WowMetric(label="Подсистем", value=str(modules_count),
                      hint="ключевых модулей", source="derived")
        )

    team_count = len(fidelity.team_structured) if fidelity else 0
    if team_count:
        out.append(
            WowMetric(label="Команда", value=str(team_count),
                      hint="участников проекта", source="derived")
        )

    stack_count = (
        sum(len(v) for v in fidelity.tech_stack_grouped.values()) if fidelity else 0
    )
    if stack_count:
        out.append(
            WowMetric(label="Технологий", value=str(stack_count),
                      hint="в технологическом стеке", source="derived")
        )

    tasks_block = blocks.get("tasks")
    tasks_count = len(tasks_block.bullets) if tasks_block and tasks_block.bullets else 0
    if tasks_count:
        out.append(
            WowMetric(label="Задач", value=str(tasks_count),
                      hint="в дорожной карте", source="derived")
        )

    results_block = blocks.get("results")
    results_count = (
        len(results_block.bullets) if results_block and results_block.bullets else 0
    )
    if results_count:
        out.append(
            WowMetric(label="Результатов", value=str(results_count),
                      hint="достигнутых результатов", source="derived")
        )

    return out


def _fallback_metrics(contract: LandingContract) -> list[WowMetric]:
    fidelity: FidelityMetadata | None = contract.fidelity
    blocks = {b.key: b for b in contract.blocks}
    modules_count = len(fidelity.modules) if fidelity else 0
    team_count = len(fidelity.team_structured) if fidelity else 0
    stack_count = (
        sum(len(v) for v in fidelity.tech_stack_grouped.values()) if fidelity else 0
    )
    tasks_block = blocks.get("tasks")
    tasks_count = len(tasks_block.bullets) if tasks_block and tasks_block.bullets else 0
    return [
        WowMetric(label="Подсистем", value=str(modules_count), source="fallback"),
        WowMetric(label="Команда", value=str(team_count), source="fallback"),
        WowMetric(label="Технологий", value=str(stack_count), source="fallback"),
        WowMetric(label="Задач", value=str(tasks_count), source="fallback"),
    ]


def extract_wow_metrics(contract: LandingContract) -> list[WowMetric]:
    """Extract impact metrics, always returning at least ``MIN_METRIC_CARDS``."""

    text = _collect_text(contract)
    metrics: list[WowMetric] = []
    seen_labels: set[str] = set()

    def _add(items: list[WowMetric]) -> None:
        for item in items:
            if item.label in seen_labels:
                continue
            seen_labels.add(item.label)
            metrics.append(item)

    extracted = _extract_context_metrics(text)
    extracted.sort(key=lambda m: _numeric_weight(m.value), reverse=True)
    _add(extracted)
    _add(_extract_product_metrics(text))
    _add(_derived_metrics(contract))

    if len(metrics) < MIN_METRIC_CARDS:
        _add(_fallback_metrics(contract))

    if len(metrics) < MIN_METRIC_CARDS:
        # Last-resort placeholders so the panel never collapses.
        placeholders = [
            WowMetric(label="Подсистем", value="0", source="fallback"),
            WowMetric(label="Команда", value="0", source="fallback"),
            WowMetric(label="Технологий", value="0", source="fallback"),
            WowMetric(label="Задач", value="0", source="fallback"),
        ]
        for item in placeholders:
            if item.label not in seen_labels:
                seen_labels.add(item.label)
                metrics.append(item)

    return metrics[:MAX_METRIC_CARDS]
