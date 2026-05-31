"""Bundle data contract mapper for the Interactive WOW Bundle (Stage P.7.2).

Converts a :class:`LandingContract` into a compact ``WowBundleData`` dictionary
that the standalone React/R3F bundle consumes (``frontend/src/wow-bundle``).

The structure mirrors the TypeScript ``WowBundleData`` interface 1:1 so the same
payload can be embedded into ``index.html`` and parsed by the bundle without any
backend at runtime. Metric/pipeline logic is shared with the WOW HTML exporter so
the interactive bundle stays consistent with the static WOW export.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.landing_contract import LandingContract
from app.schemas.style_config import LandingStyleConfigModel
from app.services.export.wow.wow_metrics import extract_wow_metrics
from app.services.export.wow.wow_pipeline import build_pipeline
from app.services.showcase.showcase_safety import sanitize_accent, sanitize_url

logger = logging.getLogger(__name__)

BUNDLE_DATA_VERSION = "1"
DEFAULT_ACCENT = "#7c8bff"
_MAX_SUBTITLE = 220
_MAX_MODULES = 12
_MAX_TEAM = 12
_MAX_STACK_ITEMS = 12

# Blocks that can supply a human subtitle, in priority order.
_SUBTITLE_BLOCKS = ("essence", "hero", "tagline")


def _clamp(text: str | None, limit: int) -> str:
    if not text:
        return ""
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "\u2026"


def _resolve_subtitle(contract: LandingContract) -> str:
    blocks = {b.key: b for b in contract.blocks}
    for key in _SUBTITLE_BLOCKS:
        block = blocks.get(key)
        if block and block.content:
            return _clamp(block.content, _MAX_SUBTITLE)
    if contract.quote:
        return _clamp(contract.quote, _MAX_SUBTITLE)
    return "Интеллектуальная система, собранная из проектных материалов."


def _resolve_theme(contract: LandingContract) -> dict[str, Any]:
    style_config: LandingStyleConfigModel | None = contract.style_config
    profile = "tech"
    accent: str | None = None
    if style_config is not None:
        profile = style_config.profile.value
        tokens = style_config.theme_tokens
        if tokens is not None and tokens.accent:
            accent = sanitize_accent(tokens.accent, DEFAULT_ACCENT)
    elif contract.presentation_style:
        profile = contract.presentation_style

    if accent is None:
        accent = DEFAULT_ACCENT

    return {"profile": profile, "accent": accent, "mode": "dark"}


def _map_metrics(contract: LandingContract) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for metric in extract_wow_metrics(contract):
        entry: dict[str, str] = {"value": metric.value, "label": metric.label}
        if metric.hint:
            entry["hint"] = metric.hint
        out.append(entry)
    return out


def _map_pipeline(contract: LandingContract) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in build_pipeline(contract):
        entry: dict[str, Any] = {"title": node.title}
        if node.tags:
            entry["tags"] = list(node.tags)
        out.append(entry)
    return out


def _map_modules(contract: LandingContract) -> list[dict[str, str]]:
    fidelity = contract.fidelity
    if not fidelity:
        return []
    out: list[dict[str, str]] = []
    for module in fidelity.modules[:_MAX_MODULES]:
        entry: dict[str, str] = {"title": module.name}
        if module.description:
            entry["description"] = _clamp(module.description, 160)
        if module.type:
            entry["type"] = module.type
        out.append(entry)
    return out


def _map_stack(contract: LandingContract) -> list[dict[str, Any]]:
    fidelity = contract.fidelity
    if not fidelity or not fidelity.tech_stack_grouped:
        return []
    out: list[dict[str, Any]] = []
    for group, items in fidelity.tech_stack_grouped.items():
        clean_items = [str(i).strip() for i in items if str(i).strip()]
        if not clean_items:
            continue
        out.append({"group": group, "items": clean_items[:_MAX_STACK_ITEMS]})
    return out


def _map_team(contract: LandingContract) -> list[dict[str, str]]:
    fidelity = contract.fidelity
    if not fidelity:
        return []
    out: list[dict[str, str]] = []
    for member in fidelity.team_structured[:_MAX_TEAM]:
        if not member.name:
            continue
        entry: dict[str, str] = {"name": member.name}
        if member.role:
            entry["role"] = member.role
        if member.project_area:
            entry["area"] = member.project_area
        out.append(entry)
    return out


def _map_links(
    contract: LandingContract,
    *,
    demo_url: str | None,
    showcase_url: str | None,
) -> dict[str, str]:
    links: dict[str, str] = {}
    safe_demo = sanitize_url(demo_url)
    if safe_demo:
        links["demo_url"] = safe_demo
    safe_showcase = sanitize_url(showcase_url)
    if safe_showcase:
        links["showcase_url"] = safe_showcase
    return links


def build_wow_bundle_data(
    contract: LandingContract,
    *,
    demo_url: str | None = None,
    showcase_url: str | None = None,
) -> dict[str, Any]:
    """Build the ``WowBundleData`` dict from a landing contract.

    All user-controlled URLs are sanitized; text stays raw here (HTML escaping is
    handled at the embedding boundary in ``wow_bundle_exporter``). The bundle app
    treats every value as text and never interprets it as markup.
    """

    title = _clamp(contract.title, 120) or "AI-проект"
    project: dict[str, str] = {"title": title}
    subtitle = _resolve_subtitle(contract)
    if subtitle:
        project["subtitle"] = subtitle
    if contract.client:
        project["client"] = _clamp(contract.client, 80)
    if contract.lead:
        project["lead"] = _clamp(contract.lead, 80)
    if contract.timeline:
        project["period"] = _clamp(contract.timeline, 80)

    return {
        "version": BUNDLE_DATA_VERSION,
        "project": project,
        "metrics": _map_metrics(contract),
        "pipeline": _map_pipeline(contract),
        "modules": _map_modules(contract),
        "stack": _map_stack(contract),
        "team": _map_team(contract),
        "links": _map_links(contract, demo_url=demo_url, showcase_url=showcase_url),
        "theme": _resolve_theme(contract),
    }
