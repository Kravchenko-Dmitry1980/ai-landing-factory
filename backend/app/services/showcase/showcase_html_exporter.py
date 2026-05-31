"""Generate a self-contained VR/AR Showcase HTML page (A-Frame + 2D fallback).

The output is a single HTML document containing:
  * an ``<a-scene>`` WebXR exhibition stand with one card per project,
  * a minimal inline click handler that opens demo/landing URLs safely,
  * a fully accessible 2D fallback ``<section>`` rendered below the scene.

Only the A-Frame runtime is external (vendored locally or pinned CDN). The
normal landing export is untouched and still ships zero external JS.
"""

from __future__ import annotations

import logging

from app.services.showcase.showcase_layout import (
    CARD_HEIGHT,
    CARD_WIDTH,
    compute_placements,
)
from app.services.showcase.showcase_safety import (
    escape_text,
    js_string_literal,
    sanitize_accent,
    sanitize_url,
)
from app.services.showcase.showcase_schema import (
    ShowcaseConfig,
    ShowcaseExportResult,
    ShowcaseProject,
    ShowcaseTheme,
)

logger = logging.getLogger(__name__)

# Pinned A-Frame runtime. Showcase export is a separate mode and is allowed to
# load the WebXR runtime. Override with a relative path to a vendored copy
# (e.g. ``vendor/aframe/aframe.min.js``) for a fully offline deployment.
DEFAULT_AFRAME_SRC = "https://aframe.io/releases/1.7.0/aframe.min.js"

_THEME_PALETTE: dict[ShowcaseTheme, dict[str, str]] = {
    ShowcaseTheme.UNIVERSITY: {
        "bg": "#f5f6fb",
        "sky": "#e8ecf7",
        "ground": "#d7deef",
        "panel": "#ffffff",
        "text": "#111111",
        "muted": "#5a6072",
        "accent": "#7C3AED",
    },
    ShowcaseTheme.TECH: {
        "bg": "#0b1020",
        "sky": "#0b1020",
        "ground": "#10182f",
        "panel": "#16203a",
        "text": "#e8edff",
        "muted": "#9aa6c4",
        "accent": "#3B82F6",
    },
    ShowcaseTheme.DARK: {
        "bg": "#0f1419",
        "sky": "#0f1419",
        "ground": "#161c24",
        "panel": "#1a2332",
        "text": "#f1f5f9",
        "muted": "#94a3b8",
        "accent": "#22D3EE",
    },
}

# A-Frame text color must contrast with the (light) card panel.
_CARD_PANEL_COLOR = "#ffffff"
_CARD_TITLE_COLOR = "#111111"
_CARD_BODY_COLOR = "#333333"


class ShowcaseHtmlExporter:
    """Render a :class:`ShowcaseConfig` into showcase HTML."""

    def __init__(self, aframe_src: str = DEFAULT_AFRAME_SRC) -> None:
        self._aframe_src = aframe_src

    def export(self, config: ShowcaseConfig) -> ShowcaseExportResult:
        warnings: list[str] = []
        palette = _THEME_PALETTE.get(config.theme, _THEME_PALETTE[ShowcaseTheme.UNIVERSITY])

        if not config.projects:
            warnings.append("Showcase has no projects; rendered empty stand and fallback.")

        placements = compute_placements(config.layout, len(config.projects))

        scene_cards: list[str] = []
        fallback_cards: list[str] = []
        for project, placement in zip(config.projects, placements):
            accent = sanitize_accent(project.accent, palette["accent"])
            demo_url = sanitize_url(project.demo_url)
            landing_url = sanitize_url(project.landing_url)

            if project.demo_url and not demo_url:
                warnings.append(f"Project '{project.id}': demo_url rejected by URL safety.")
            if project.landing_url and not landing_url:
                warnings.append(f"Project '{project.id}': landing_url rejected by URL safety.")

            scene_cards.append(
                self._render_scene_card(project, placement, accent, demo_url, landing_url)
            )
            fallback_cards.append(
                self._render_fallback_card(project, accent, demo_url, landing_url)
            )

        html = self._render_document(
            config=config,
            palette=palette,
            scene_cards="".join(scene_cards),
            fallback_cards="".join(fallback_cards),
        )

        return ShowcaseExportResult(
            html=html,
            project_count=len(config.projects),
            mode=str(config.mode),
            warnings=warnings,
        )

    # ----------------------------------------------------------------- scene

    def _render_scene_card(
        self,
        project: ShowcaseProject,
        placement,
        accent: str,
        demo_url: str | None,
        landing_url: str | None,
    ) -> str:
        title = escape_text(project.title)
        description = escape_text(project.description[:160])
        demo_label = escape_text(project.demo_label or "Открыть демо")

        target_url = demo_url or landing_url
        click_attr = ""
        cta_text = ""
        if target_url:
            # Minimal, sanitized inline handler. URL is emitted as a JS string
            # literal that cannot break out of the handler context.
            click_attr = (
                f' class="alf-clickable"'
                f' onclick="alfOpen(event, {js_string_literal(target_url)})"'
            )
            cta_text = (
                f"<a-text value=\"{demo_label} \u2197\" align=\"center\" "
                f"color=\"{accent}\" width=\"3\" "
                f"position=\"0 -0.36 0.02\"></a-text>"
            )

        return (
            f'<a-entity position="{placement.position_attr()}" '
            f'rotation="{placement.rotation_attr()}"{click_attr}>'
            f'<a-plane width="{CARD_WIDTH}" height="{CARD_HEIGHT}" '
            f'color="{_CARD_PANEL_COLOR}" '
            f'material="shader: flat" '
            f'position="0 0 0"></a-plane>'
            f'<a-plane width="{CARD_WIDTH}" height="0.08" color="{accent}" '
            f'material="shader: flat" position="0 0.49 0.01"></a-plane>'
            f'<a-text value="{title}" align="center" color="{_CARD_TITLE_COLOR}" '
            f'width="2.4" wrap-count="22" position="0 0.30 0.02"></a-text>'
            f'<a-text value="{description}" align="center" color="{_CARD_BODY_COLOR}" '
            f'width="2.2" wrap-count="30" position="0 -0.02 0.02"></a-text>'
            f"{cta_text}"
            f"</a-entity>"
        )

    # -------------------------------------------------------------- fallback

    def _render_fallback_card(
        self,
        project: ShowcaseProject,
        accent: str,
        demo_url: str | None,
        landing_url: str | None,
    ) -> str:
        title = escape_text(project.title)
        description = escape_text(project.description)
        category = escape_text(project.category)
        tags = "".join(
            f'<span class="showcase-tag">{escape_text(tag)}</span>'
            for tag in project.tags
            if tag
        )
        demo_label = escape_text(project.demo_label or "Демо")

        links: list[str] = []
        if demo_url:
            links.append(
                f'<a class="showcase-link showcase-link--demo" '
                f'href="{escape_text(demo_url)}" target="_blank" rel="noopener noreferrer">'
                f"{demo_label} \u2197</a>"
            )
        if landing_url:
            links.append(
                f'<a class="showcase-link" href="{escape_text(landing_url)}" '
                f'target="_blank" rel="noopener noreferrer">Лендинг \u2197</a>'
            )
        links_html = f'<div class="showcase-links">{"".join(links)}</div>' if links else ""

        cat_html = (
            f'<p class="showcase-category">{category}</p>' if category else ""
        )
        tags_html = f'<div class="showcase-tags">{tags}</div>' if tags else ""
        desc_html = f"<p>{description}</p>" if description else ""

        return (
            f'<article class="showcase-card" style="--card-accent:{accent}">'
            f"<h3>{title}</h3>"
            f"{cat_html}{desc_html}{tags_html}{links_html}"
            f"</article>"
        )

    # -------------------------------------------------------------- document

    def _render_document(
        self,
        config: ShowcaseConfig,
        palette: dict[str, str],
        scene_cards: str,
        fallback_cards: str,
    ) -> str:
        title = escape_text(config.title)
        subtitle = escape_text(config.subtitle)
        organization = escape_text(config.organization)

        vr_attr = "" if config.mode.value == "vr_ready" else ' vr-mode-ui="enabled: false"'

        subtitle_html = f'<p class="showcase-subtitle">{subtitle}</p>' if subtitle else ""
        org_html = (
            f'<p class="showcase-org">{organization}</p>' if organization else ""
        )

        empty_hint = ""
        if not config.projects:
            empty_hint = (
                '<p class="showcase-empty">В этой витрине пока нет проектов.</p>'
            )

        css = self._build_css(palette)
        script = self._build_script()

        scene = (
            f'<a-scene embedded{vr_attr} background="color: {palette["sky"]}" '
            f'class="showcase-scene" aria-hidden="true">'
            f'<a-sky color="{palette["sky"]}"></a-sky>'
            f'<a-plane rotation="-90 0 0" width="40" height="40" '
            f'color="{palette["ground"]}" material="shader: flat" '
            f'position="0 0 0"></a-plane>'
            f'<a-entity light="type: ambient; intensity: 0.9"></a-entity>'
            f'<a-entity light="type: directional; intensity: 0.4" '
            f'position="1 3 2"></a-entity>'
            f'<a-text value="{title}" align="center" color="{palette["text"]}" '
            f'width="6" position="0 3.0 -4"></a-text>'
            f"{scene_cards}"
            f'<a-entity id="rig" position="0 0 0">'
            f'<a-camera position="0 1.6 5" wasd-controls look-controls>'
            f'<a-cursor color="{palette["accent"]}" '
            f'raycaster="objects: .alf-clickable"></a-cursor>'
            f"</a-camera></a-entity>"
            f"</a-scene>"
        )

        fallback = (
            f'<section class="showcase-fallback" aria-label="Список проектов витрины">'
            f'<h2>Проекты витрины</h2>'
            f"{empty_hint}"
            f'<div class="showcase-grid">{fallback_cards}</div>'
            f"</section>"
        )

        runtime_note = (
            '<p class="showcase-note">VR/AR Showcase export uses A-Frame runtime. '
            "Раздел ниже доступен без WebXR.</p>"
        )

        return (
            f"<!DOCTYPE html><html lang='ru'><head>"
            f"<meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{title}</title>"
            f'<script src="{escape_text(self._aframe_src)}"></script>'
            f"<style>{css}</style></head>"
            f"<body class='showcase-theme-{escape_text(config.theme.value)}'>"
            f'<header class="showcase-header">'
            f"<h1>{title}</h1>{subtitle_html}{org_html}{runtime_note}"
            f"</header>"
            f"{scene}"
            f"{fallback}"
            f'<footer class="showcase-footer">'
            f"<p>AI Landing Factory \u00b7 VR/AR Showcase</p></footer>"
            f"<script>{script}</script>"
            f"</body></html>"
        )

    @staticmethod
    def _build_css(palette: dict[str, str]) -> str:
        return (
            ":root{"
            f"--sc-bg:{palette['bg']};--sc-panel:{palette['panel']};"
            f"--sc-text:{palette['text']};--sc-muted:{palette['muted']};"
            f"--sc-accent:{palette['accent']};"
            "}"
            "*{box-sizing:border-box}"
            "body{margin:0;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;"
            "background:var(--sc-bg);color:var(--sc-text);}"
            ".showcase-header{max-width:1100px;margin:0 auto;padding:32px 20px 12px;}"
            ".showcase-header h1{margin:0 0 6px;font-size:1.9rem;}"
            ".showcase-subtitle{margin:0 0 4px;color:var(--sc-muted);font-size:1.05rem;}"
            ".showcase-org{margin:0;color:var(--sc-muted);font-size:0.95rem;}"
            ".showcase-note{margin:10px 0 0;font-size:0.8rem;color:var(--sc-muted);}"
            ".showcase-scene{display:block;width:100%;height:60vh;min-height:360px;}"
            ".showcase-fallback{max-width:1100px;margin:0 auto;padding:28px 20px 8px;}"
            ".showcase-fallback h2{font-size:1.4rem;margin:0 0 16px;}"
            ".showcase-empty{color:var(--sc-muted);}"
            ".showcase-grid{display:grid;gap:18px;"
            "grid-template-columns:repeat(auto-fill,minmax(260px,1fr));}"
            ".showcase-card{background:var(--sc-panel);border-radius:14px;padding:18px;"
            "border-top:4px solid var(--card-accent,var(--sc-accent));"
            "box-shadow:0 2px 10px rgba(0,0,0,0.08);}"
            ".showcase-card h3{margin:0 0 8px;font-size:1.1rem;}"
            ".showcase-card p{margin:0 0 10px;color:var(--sc-muted);font-size:0.92rem;"
            "line-height:1.45;}"
            ".showcase-category{font-size:0.78rem;text-transform:uppercase;"
            "letter-spacing:0.04em;color:var(--card-accent,var(--sc-accent));"
            "font-weight:600;}"
            ".showcase-tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;}"
            ".showcase-tag{font-size:0.72rem;padding:3px 9px;border-radius:999px;"
            "background:rgba(124,58,237,0.12);color:var(--sc-text);}"
            ".showcase-links{display:flex;flex-wrap:wrap;gap:10px;}"
            ".showcase-link{display:inline-block;font-size:0.85rem;font-weight:600;"
            "text-decoration:none;padding:8px 14px;border-radius:10px;"
            "border:1px solid var(--card-accent,var(--sc-accent));"
            "color:var(--card-accent,var(--sc-accent));}"
            ".showcase-link--demo{background:var(--card-accent,var(--sc-accent));"
            "color:#fff;}"
            ".showcase-footer{max-width:1100px;margin:0 auto;padding:24px 20px;"
            "color:var(--sc-muted);font-size:0.85rem;}"
            "@media(max-width:600px){.showcase-scene{height:48vh;min-height:300px;}}"
        )

    @staticmethod
    def _build_script() -> str:
        # Minimal, showcase-only handler. Opens a sanitized URL in a new tab.
        # The URL is injected as a JS string literal by the exporter; this code
        # additionally re-validates the scheme at runtime as defense in depth.
        return (
            "function alfOpen(evt, url){"
            "try{if(evt&&evt.preventDefault){evt.preventDefault();}}catch(e){}"
            "if(!url){return;}"
            "var lowered=String(url).trim().toLowerCase();"
            "if(lowered.indexOf('javascript:')===0||lowered.indexOf('data:')===0||"
            "lowered.indexOf('vbscript:')===0||lowered.indexOf('file:')===0){return;}"
            "window.open(url,'_blank','noopener,noreferrer');"
            "}"
        )
