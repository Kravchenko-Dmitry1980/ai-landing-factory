"""HTML section builders for the WOW landing export (Stage P.7).

All user-controlled text is routed through ``escape_text`` and links through
``sanitize_url`` so a malicious title or demo URL can never break out of its
context. The CSS hero is always rendered; the optional A-Frame scene is layered
on top and is never required for content access.
"""

from __future__ import annotations

from app.schemas.export_mode import Wow3dRuntime
from app.schemas.fidelity import FidelityMetadata, LandingModule, TeamMember
from app.schemas.landing_contract import LandingBlock, LandingContract
from app.services.export.export_tagline import resolve_tagline
from app.services.export.theme_tokens import ThemeTokens
from app.services.export.wow.wow_metrics import WowMetric
from app.services.export.wow.wow_mascot import build_wow_hero_mascot_html
from app.services.export.wow.wow_pipeline import PipelineNode
from app.services.showcase.showcase_safety import escape_text, sanitize_url
from app.services.showcase.showcase_vendor import DEFAULT_AFRAME_SRC, is_local_aframe_src

KICKER = "AI PROJECT EXHIBIT"

# Core technologies that get a glow accent in the stack cloud.
_CORE_STACK = {
    "qdrant", "neo4j", "postgres", "postgresql", "redis", "kafka",
    "pytorch", "tensorflow", "fastapi", "docker", "kubernetes", "llm",
    "bert", "e5", "openai", "elasticsearch", "clickhouse",
}


def _orbit_cards(contract: LandingContract) -> list[tuple[str, str]]:
    fidelity: FidelityMetadata | None = contract.fidelity
    blocks = {b.key: b for b in contract.blocks}
    modules_count = len(fidelity.modules) if fidelity else 0
    team_count = len(fidelity.team_structured) if fidelity else 0
    stack_count = (
        sum(len(v) for v in fidelity.tech_stack_grouped.values()) if fidelity else 0
    )
    tasks_block = blocks.get("tasks")
    tasks_count = len(tasks_block.bullets) if tasks_block and tasks_block.bullets else 0

    cards: list[tuple[str, str]] = []
    if modules_count:
        cards.append((str(modules_count), "Подсистемы"))
    if team_count:
        cards.append((str(team_count), "Команда"))
    if stack_count:
        cards.append((str(stack_count), "Технологии"))
    if tasks_count:
        cards.append((str(tasks_count), "Задачи"))
    cards.append(("Live", "Статус"))
    return cards[:5]


def build_wow_hero(
    contract: LandingContract,
    blocks: dict[str, LandingBlock],
    tokens: ThemeTokens,
    *,
    runtime: Wow3dRuntime = Wow3dRuntime.NONE,
    aframe_block: str = "",
) -> str:
    tagline_block = blocks.get("tagline")
    essence_block = blocks.get("essence")
    tagline_raw = tagline_block.content if tagline_block else ""
    essence_raw = essence_block.content if essence_block else ""
    tagline_text = resolve_tagline(contract.title, tagline_raw, essence_raw, None)

    meta_parts: list[str] = []
    if contract.client:
        meta_parts.append(f"<span>Заказчик: {escape_text(contract.client[:120])}</span>")
    if contract.timeline:
        meta_parts.append(f"<span>Период: {escape_text(contract.timeline)}</span>")
    if contract.lead:
        meta_parts.append(f"<span>Тимлид: {escape_text(contract.lead)}</span>")
    meta_html = "".join(meta_parts)

    orbit = "".join(
        f"<article class='wow-orbit-card'>"
        f"<div class='o-value'>{escape_text(value)}</div>"
        f"<div class='o-label'>{escape_text(label)}</div>"
        f"</article>"
        for value, label in _orbit_cards(contract)
    )

    # WOW hero is always pseudo-3D regardless of profile heroMode.
    mascot_html = build_wow_hero_mascot_html()
    return (
        f"<section id='wow-hero' class='wow-hero wow-cockpit hero--future-3d'>"
        f"<div class='wow-bg-grid' aria-hidden='true'></div>"
        f"<div class='wow-bg-radar' aria-hidden='true'></div>"
        f"{mascot_html}"
        f"<div class='wow-cockpit-shell'>"
        f"<div class='wow-kicker'>{escape_text(KICKER)}</div>"
        f"<h1>{escape_text(contract.title or 'AI-проект')}</h1>"
        f"<p class='wow-tagline'>{escape_text(tagline_text)}</p>"
        f"<div class='wow-hero-meta'>{meta_html}</div>"
        f"<div class='wow-hero-actions'>"
        f"<a class='wow-btn primary' href='#wow-cta'>Открыть демо</a>"
        f"<a class='wow-btn secondary' href='#wow-metrics'>Показатели</a>"
        f"<a class='wow-btn secondary' href='#wow-pipeline'>Pipeline</a>"
        f"</div>"
        f"{aframe_block}"
        f"</div>"
        f"<div class='wow-orbit'>{orbit}</div>"
        f"</section>"
    )


def build_wow_metric_panel(metrics: list[WowMetric]) -> str:
    cards = []
    for metric in metrics:
        hint = (
            f"<div class='m-hint'>{escape_text(metric.hint)}</div>" if metric.hint else ""
        )
        cards.append(
            f"<div class='wow-metric-card' data-metric-source='{escape_text(metric.source)}'>"
            f"<div class='m-value'>{escape_text(metric.value)}</div>"
            f"<div class='m-label'>{escape_text(metric.label)}</div>"
            f"{hint}"
            f"</div>"
        )
    return (
        f"<section id='wow-metrics' class='wow-section'>"
        f"<div class='wow-section-title'>Impact / показатели</div>"
        f"<div class='wow-metric-panel'>{''.join(cards)}</div>"
        f"</section>"
    )


def build_wow_pipeline_map(nodes: list[PipelineNode]) -> str:
    parts: list[str] = []
    for index, node in enumerate(nodes):
        if index > 0:
            parts.append("<div class='wow-pipeline-connector' aria-hidden='true'>→</div>")
        tags = "".join(
            f"<span class='p-tag'>{escape_text(tag)}</span>" for tag in node.tags
        )
        parts.append(
            f"<div class='wow-pipeline-node'>"
            f"<div class='p-step'>STAGE {index + 1}</div>"
            f"<div class='p-title'>{escape_text(node.title)}</div>"
            f"<div class='p-tags'>{tags}</div>"
            f"</div>"
        )
    return (
        f"<section id='wow-pipeline' class='wow-section'>"
        f"<div class='wow-section-title'>Intelligence pipeline</div>"
        f"<div class='wow-pipeline-map'>{''.join(parts)}</div>"
        f"</section>"
    )


def _modules_block(modules: list[LandingModule]) -> str:
    if not modules:
        return ""
    cards = []
    for mod in modules:
        cards.append(
            f"<article class='wow-hologram-card'>"
            f"<span class='h-badge'>Subsystem</span>"
            f"<h3>{escape_text(mod.name)}</h3>"
            f"<p>{escape_text(mod.description[:400])}</p>"
            f"</article>"
        )
    return (
        f"<section id='wow-modules' class='wow-section'>"
        f"<div class='wow-section-title'>Ключевые системы</div>"
        f"<div class='wow-module-grid'>{''.join(cards)}</div>"
        f"</section>"
    )


def _stack_block(grouped: dict[str, list[str]]) -> str:
    if not grouped:
        return ""
    groups = []
    for category, items in grouped.items():
        chips = []
        for item in items:
            core = "is-core" if item.strip().casefold() in _CORE_STACK else ""
            chips.append(
                f"<span class='wow-chip {core}'>{escape_text(item)}</span>"
            )
        groups.append(
            f"<div class='wow-stack-group'><h4>{escape_text(category)}</h4>"
            f"<div class='wow-stack-chips'>{''.join(chips)}</div></div>"
        )
    return (
        f"<section id='wow-stack' class='wow-section'>"
        f"<div class='wow-section-title'>Технологический стек</div>"
        f"<div class='wow-stack-cloud'>{''.join(groups)}</div>"
        f"</section>"
    )


def _team_capacity_block(members: list[TeamMember]) -> str:
    if not members:
        return ""
    roles = sorted({m.role for m in members if m.role})
    role_chips = "".join(
        f"<span class='wow-chip'>{escape_text(role)}</span>" for role in roles[:8]
    )
    return (
        f"<section id='wow-team' class='wow-section'>"
        f"<div class='wow-section-title'>Команда</div>"
        f"<div class='wow-metric-panel'>"
        f"<div class='wow-metric-card'>"
        f"<div class='m-value'>{len(members)}</div>"
        f"<div class='m-label'>Team capacity</div>"
        f"<div class='m-hint'>участников проекта</div>"
        f"</div></div>"
        f"<div class='wow-stack-chips' style='margin-top:1rem'>{role_chips}</div>"
        f"</section>"
    )


def build_wow_story_sections(
    contract: LandingContract,
    blocks: dict[str, LandingBlock],
    fidelity: FidelityMetadata | None,
    tokens: ThemeTokens,
) -> str:
    modules = fidelity.modules if fidelity else []
    grouped = fidelity.tech_stack_grouped if fidelity else {}
    members = fidelity.team_structured if fidelity else []
    return (
        _modules_block(modules)
        + _stack_block(grouped)
        + _team_capacity_block(members)
    )


def build_wow_cta(contract: LandingContract, *, demo_url: str | None = None) -> str:
    safe_demo = sanitize_url(demo_url) if demo_url else None
    if safe_demo:
        demo_btn = (
            f"<a class='wow-btn primary' href='{escape_text(safe_demo)}' "
            f"target='_blank' rel='noopener noreferrer'>Открыть демо</a>"
        )
    else:
        demo_btn = (
            "<a class='wow-btn primary is-disabled' aria-disabled='true' "
            "title='Демо-ссылка не добавлена'>Демо-ссылка не добавлена</a>"
        )
    return (
        f"<section id='wow-cta' class='wow-demo-cta'>"
        f"<h2>Демо и витрина проекта</h2>"
        f"<p>Откройте рабочее демо или добавьте проект в VR/AR-витрину "
        f"для презентации на стенде.</p>"
        f"<div class='wow-cta-actions'>"
        f"{demo_btn}"
        f"<a class='wow-btn secondary' href='/showcase'>Открыть VR/AR-витрину</a>"
        f"</div>"
        f"</section>"
    )


def build_wow_aframe_hero(
    contract: LandingContract,
    *,
    aframe_src: str = DEFAULT_AFRAME_SRC,
    runtime_available: bool = True,
) -> str:
    """Compact embedded A-Frame scene (opt-in). Local vendored runtime only.

    Returns an empty string if the runtime is unavailable; the CSS hero remains
    the source of truth for content. No user text is injected into JS.
    """

    if not is_local_aframe_src(aframe_src):
        # Defense in depth: WOW export must never reach for a remote runtime.
        return (
            "<!-- wow: non-local A-Frame runtime rejected; CSS hero fallback only -->"
        )

    if not runtime_available:
        return (
            "<!-- wow: vendored A-Frame runtime missing; CSS hero fallback only -->"
            "<p class='wow-aframe-fallback'>3D-сцена недоступна — показан CSS-режим.</p>"
        )

    # No user text is injected into the scene (only static, escaped attributes),
    # so there is no need for inline JS here.
    safe_title = escape_text((contract.title or "AI Project")[:80])
    return (
        "<div class='wow-aframe-hero' aria-label='3D project showcase'>"
        "<a-scene embedded vr-mode-ui='enabled: false' "
        "background='color: #05070f'>"
        "<a-entity light='type: ambient; intensity: 0.9'></a-entity>"
        "<a-entity light='type: directional; intensity: 0.6' position='1 1 1'></a-entity>"
        "<a-box position='-1.1 1.2 -3' rotation='0 45 0' color='#6366f1' "
        "depth='0.2' width='1.2' height='0.7' "
        "animation='property: rotation; to: 0 405 0; loop: true; dur: 16000; easing: linear'></a-box>"
        "<a-box position='1.1 1.2 -3' rotation='0 -30 0' color='#7c3aed' "
        "depth='0.2' width='1.2' height='0.7'></a-box>"
        f"<a-text value='{safe_title}' align='center' color='#e8edf4' "
        "position='0 1.95 -3' width='4'></a-text>"
        "<a-sky color='#05070f'></a-sky>"
        "<a-camera position='0 1.6 0' look-controls='enabled: false' wasd-controls='enabled: false'></a-camera>"
        "</a-scene>"
        "<p class='wow-aframe-fallback'>Встроенная 3D-сцена (A-Frame, локальный runtime). "
        "Контент доступен и без 3D.</p>"
        "</div>"
    )
