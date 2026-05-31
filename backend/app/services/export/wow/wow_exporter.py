"""WOW exhibition-grade HTML exporter (Stage P.7).

Orchestrates the WOW sections into a self-contained, presentation-grade HTML
document. Parallel to ``StyledHtmlExporter`` (standard mode) and never the
default. The A-Frame runtime is opt-in and always served from the local
vendored path — never a CDN.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from app.repositories.contract_repository import ContractRepository
from app.schemas.export_mode import Wow3dRuntime
from app.schemas.landing_contract import LandingContract
from app.schemas.style_config import LandingStyleConfigModel, effective_style_config
from app.services.export.export_theme import ExportTheme
from app.services.export.theme_tokens import ThemeTokens, normalize_theme_tokens
from app.services.export.wow.wow_css import build_wow_css
from app.services.export.wow.wow_metrics import extract_wow_metrics
from app.services.export.wow.wow_pipeline import build_pipeline
from app.services.export.wow.wow_sections import (
    build_wow_aframe_hero,
    build_wow_cta,
    build_wow_hero,
    build_wow_metric_panel,
    build_wow_pipeline_map,
    build_wow_story_sections,
)
from app.services.showcase.showcase_safety import escape_text
from app.services.showcase.showcase_vendor import DEFAULT_AFRAME_SRC, VENDOR_SOURCE

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WowExportOptions:
    """Resolved WOW export options."""

    runtime: Wow3dRuntime = Wow3dRuntime.NONE
    demo_url: str | None = None


class WowHtmlExporter:
    """Export contract + landing as exhibition-grade WOW HTML."""

    def __init__(self, repository: ContractRepository) -> None:
        self._repo = repository

    async def to_html(
        self,
        project_id: UUID,
        *,
        theme: ExportTheme | None = None,
        style_config: LandingStyleConfigModel | None = None,
        options: WowExportOptions | None = None,
    ) -> str:
        contract = await self._repo.get_contract(project_id)
        if not contract:
            return (
                "<!DOCTYPE html><html lang='ru'><body>"
                "<p>Landing not generated yet.</p></body></html>"
            )

        merged_style = (
            style_config or contract.style_config or effective_style_config(contract)
        )
        resolved_theme = theme or ExportTheme.from_profile(merged_style.profile)
        opts = options or WowExportOptions()
        return self._render(contract, resolved_theme, merged_style, opts)

    def _render(
        self,
        contract: LandingContract,
        theme: ExportTheme,
        style_config: LandingStyleConfigModel,
        options: WowExportOptions,
    ) -> str:
        tokens: ThemeTokens = normalize_theme_tokens(style_config)
        blocks = {b.key: b for b in contract.blocks}
        fidelity = contract.fidelity

        metrics = extract_wow_metrics(contract)
        pipeline = build_pipeline(contract)

        runtime_available = VENDOR_SOURCE.is_file()
        aframe_block = ""
        head_script = ""
        if options.runtime == Wow3dRuntime.AFRAME:
            aframe_block = build_wow_aframe_hero(
                contract,
                aframe_src=DEFAULT_AFRAME_SRC,
                runtime_available=runtime_available,
            )
            if runtime_available:
                head_script = (
                    f"<script src='{escape_text(DEFAULT_AFRAME_SRC)}'></script>"
                )
            else:
                logger.warning(
                    "WOW A-Frame requested but vendored runtime missing at %s",
                    VENDOR_SOURCE,
                )

        hero = build_wow_hero(
            contract,
            blocks,
            tokens,
            runtime=options.runtime,
            aframe_block=aframe_block,
        )
        metric_panel = build_wow_metric_panel(metrics)
        pipeline_map = build_wow_pipeline_map(pipeline)
        story = build_wow_story_sections(contract, blocks, fidelity, tokens)
        cta = build_wow_cta(contract, demo_url=options.demo_url)

        footer = (
            f"<footer class='wow-footer'>AI Landing Factory · "
            f"{escape_text(contract.title or 'Проект')} · WOW exhibit · "
            f"v{contract.version}</footer>"
        )

        css = build_wow_css(tokens)
        title = escape_text(contract.title or "AI-проект")
        body_class = self._body_class(theme, tokens, style_config)

        return (
            f"<!DOCTYPE html><html lang='ru'><head>"
            f"<meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{title}</title>"
            f"<style>{css}</style>"
            f"{head_script}"
            f"</head>"
            f'<body class="{body_class}" data-export-mode="wow">'
            f"<main class='wow-shell'>"
            f"{hero}{metric_panel}{pipeline_map}{story}{cta}{footer}"
            f"</main></body></html>"
        )

    @staticmethod
    def _body_class(
        theme: ExportTheme,
        tokens: ThemeTokens,
        style_config: LandingStyleConfigModel,
    ) -> str:
        classes = ["wow-landing", theme.body_class(), f"wow-profile-{style_config.profile.value}"]
        if tokens.colorScheme == "dark":
            classes.append("wow--dark")
        else:
            classes.append("wow--light")
        return " ".join(classes)
