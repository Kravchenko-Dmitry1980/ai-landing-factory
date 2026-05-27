"""Token-driven export CSS using --alf-* variables with legacy aliases."""

from __future__ import annotations

from app.schemas.style_config import LandingStyleConfigModel, LandingStyleProfile
from app.services.export.export_theme import ExportTheme
from app.services.export.theme_tokens import ThemeTokens, css_root_block, normalize_theme_tokens

CSS_BASE = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Segoe UI", system-ui, Inter, -apple-system, sans-serif;
  background: var(--alf-bg);
  color: var(--alf-text);
  line-height: 1.65;
  min-height: 100vh;
  font-size: 16px;
}
.container { width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }
.hero {
  padding: 3rem 0 2rem;
  border-bottom: 1px solid var(--alf-border);
  margin-bottom: var(--alf-gap);
  border-radius: var(--alf-radius);
}
.hero h1 {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 700;
  margin-bottom: 0.75rem;
  color: var(--alf-text);
  line-height: 1.2;
}
.hero .meta { color: var(--alf-muted); font-size: 0.95rem; display: flex; flex-wrap: wrap; gap: 1rem; }
.hero .tagline { font-size: 1.05rem; color: var(--alf-muted); margin-top: 1rem; max-width: 100%; }
section { margin: var(--alf-gap) 0; }
section h2 {
  font-size: clamp(1.25rem, 3vw, 1.75rem);
  font-weight: 700;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--alf-border);
  color: var(--alf-text);
}
.card {
  background: var(--alf-surface);
  border: 1px solid var(--alf-border);
  border-radius: var(--alf-radius);
  padding: 1.25rem;
}
.card h3 { font-size: 1.05rem; margin-bottom: 0.5rem; color: var(--alf-text); font-weight: 600; }
.card p, .card li { color: var(--alf-text); font-size: 0.9375rem; line-height: 1.55; }
footer {
  margin-top: calc(var(--alf-gap) * 2);
  padding-top: 1.5rem;
  border-top: 1px solid var(--alf-border);
  color: var(--alf-muted);
  font-size: 0.85rem;
  text-align: center;
}
@media (max-width: 640px) {
  .container { padding: 1rem; }
  .hero { padding: 2rem 0 1.5rem; }
}
"""

CSS_SHARED_LAYOUT = """
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--alf-gap); }
.grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--alf-gap); }
.card ul { list-style: none; padding: 0; }
.card ul li { padding: 0.35rem 0; padding-left: 1rem; position: relative; }
.card ul li::before { content: "·"; position: absolute; left: 0; color: var(--alf-accent); }
.card ul li.more { color: var(--alf-muted); font-style: italic; }
.card ul li.more::before { content: "+"; }
ul.bullets { list-style: none; padding: 0; }
ul.bullets li {
  padding: 0.5rem 0 0.5rem 1.25rem;
  position: relative;
  border-bottom: 1px solid var(--alf-border);
}
ul.bullets li::before { content: "▸"; position: absolute; left: 0; color: var(--alf-accent); }
.stack-group { margin-bottom: 1rem; }
.stack-group h4 {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--alf-muted);
  margin-bottom: 0.5rem;
  font-weight: 600;
}
.stack-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.stack-tag {
  background: var(--alf-accent-light);
  border: 1px solid var(--alf-border);
  border-radius: 999px;
  padding: 0.3rem 0.85rem;
  font-size: 0.82rem;
  color: var(--alf-accent);
  font-weight: 500;
}
.team-card .role { color: var(--alf-accent); font-size: 0.85rem; margin-bottom: 0.25rem; font-weight: 500; }
.team-card .area { color: var(--alf-muted); font-size: 0.8rem; margin-bottom: 0.5rem; }
.team-intro { color: var(--alf-muted); font-size: 0.9rem; margin-bottom: 1.25rem; max-width: 100%; line-height: 1.55; }
.incomplete-banner {
  background: #FEF3C7;
  border: 1px solid #F59E0B;
  color: #92400E;
  padding: 0.75rem 1rem;
  border-radius: var(--alf-radius);
  margin-bottom: var(--alf-gap);
  font-size: 0.9rem;
}
.hero .meta { color: var(--alf-muted); font-size: 0.95rem; display: flex; flex-wrap: wrap; gap: 1rem; }
@media (max-width: 640px) { .container { padding: 1rem; } }
"""

CSS_PROFILE_FEATURES = {
    ExportTheme.UNIVERSITY_PLATFORM: """
.theme-university_platform section h2 { border-bottom-color: #111111; }
.theme-university_platform .stack-tag { background: var(--alf-accent-light); color: var(--alf-accent); }
""",
    ExportTheme.MINIMAL: """
.theme-minimal .hero h1 { font-weight: 400; }
.theme-minimal section h2 { text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500; color: var(--alf-muted); border: none; }
.theme-minimal .card { box-shadow: none; }
.theme-minimal section { margin: calc(var(--alf-gap) * 1.25) 0; }
""",
    ExportTheme.CORPORATE: """
.theme-corporate .hero { background: var(--alf-surface); border-bottom: 2px solid var(--alf-accent-light); }
.theme-corporate section h2 { color: var(--alf-accent); }
.theme-corporate .card { border-width: 2px; box-shadow: none; }
""",
    ExportTheme.TECH: """
.theme-tech .hero { background: var(--alf-hero-gradient); }
.theme-tech .hero h1 {
  background: linear-gradient(90deg, #60a5fa, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.theme-tech section h2 { color: #93c5fd; border-bottom-color: var(--alf-accent-light); }
.theme-tech .card {
  background: color-mix(in srgb, var(--alf-surface) 85%, transparent);
  backdrop-filter: blur(8px);
}
.theme-tech .module-card { border-color: rgba(99,102,241,0.35); }
.theme-tech .stack-tag { background: var(--alf-surface-2); color: #93c5fd; }
""",
    ExportTheme.BOLD: """
.theme-bold .hero { border-left: 6px solid var(--alf-accent); padding-left: 1.25rem; }
.theme-bold .hero h1 { font-size: clamp(2.5rem, 6vw, 4rem); font-weight: 800; line-height: 1.05; }
.theme-bold section h2 { font-size: clamp(1.5rem, 3vw, 2.25rem); font-weight: 800; color: var(--alf-accent); border: none; }
.theme-bold .card { border-width: 2px; }
.theme-bold .stack-tag { font-weight: 600; border: 2px solid var(--alf-accent); }
""",
    ExportTheme.CUSTOM: "",
    ExportTheme.ENTERPRISE_DARK: """
.theme-enterprise_dark .hero { background: var(--alf-hero-gradient); }
""",
}

CSS_ENTERPRISE_DARK_LEGACY = """
.theme-enterprise_dark section h2 { border-bottom: 2px solid var(--alf-accent-light); }
.theme-enterprise_dark .card h3 { color: var(--alf-accent); }
"""


def build_export_css(
    theme: ExportTheme,
    style_config: LandingStyleConfigModel | None = None,
    tokens: ThemeTokens | None = None,
) -> str:
    resolved_tokens = tokens
    if resolved_tokens is None:
        cfg = style_config
        if cfg is None:
            try:
                cfg = LandingStyleConfigModel(profile=LandingStyleProfile(theme.value))
            except ValueError:
                cfg = None
        resolved_tokens = normalize_theme_tokens(cfg)

    profile_css = CSS_PROFILE_FEATURES.get(theme, "")
    return (
        css_root_block(resolved_tokens)
        + CSS_BASE
        + CSS_SHARED_LAYOUT
        + profile_css
        + (CSS_ENTERPRISE_DARK_LEGACY if theme == ExportTheme.ENTERPRISE_DARK else "")
    )
