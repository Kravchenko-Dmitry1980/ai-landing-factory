"""Shared normalized theme tokens for preview/export parity."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.schemas.style_config import LandingStyleConfigModel, ThemeTokensModel
from app.services.export.style_intent import ACCENT_HEX, parse_style_intent

RADIUS_PX = {"sharp": 4, "soft": 8, "rounded": 16}
GAP_REM = {"compact": 1.0, "normal": 1.5, "spacious": 2.0}
MOTION_DURATION = {"none": "0s", "subtle": "0.25s", "expressive": "0.45s"}
CARD_TRANSFORM = {
    "flat": "none",
    "soft": "translateY(-4px)",
    "glass": "translateY(-2px)",
    "outlined": "none",
}


@dataclass(frozen=True)
class ThemeTokens:
    colorScheme: str
    bg: str
    surface: str
    surface2: str
    text: str
    muted: str
    border: str
    accent: str
    accentHover: str
    accentLight: str
    radiusPx: int
    gapRem: float
    density: str
    motion: str
    heroMode: str
    cardStyle: str

    def to_serializable(self) -> dict[str, Any]:
        return asdict(self)


PROFILE_PRESETS: dict[str, ThemeTokens] = {
    "university_platform": ThemeTokens(
        colorScheme="light",
        bg="#ffffff",
        surface="#F1F4F7",
        surface2="#EEF2F5",
        text="#111111",
        muted="#7A8799",
        border="#E5E7EB",
        accent="#7C3AED",
        accentHover="#6D28D9",
        accentLight="#EDE9FE",
        radiusPx=8,
        gapRem=1.5,
        density="normal",
        motion="subtle",
        heroMode="classic",
        cardStyle="soft",
    ),
    "minimal": ThemeTokens(
        colorScheme="light",
        bg="#ffffff",
        surface="#fafafa",
        surface2="#f5f5f5",
        text="#171717",
        muted="#737373",
        border="#f0f0f0",
        accent="#525252",
        accentHover="#404040",
        accentLight="#f5f5f5",
        radiusPx=4,
        gapRem=2.0,
        density="spacious",
        motion="none",
        heroMode="classic",
        cardStyle="flat",
    ),
    "corporate": ThemeTokens(
        colorScheme="light",
        bg="#f8fafc",
        surface="#ffffff",
        surface2="#f1f5f9",
        text="#0f172a",
        muted="#64748b",
        border="#cbd5e1",
        accent="#2563eb",
        accentHover="#1d4ed8",
        accentLight="#dbeafe",
        radiusPx=8,
        gapRem=1.5,
        density="normal",
        motion="subtle",
        heroMode="classic",
        cardStyle="outlined",
    ),
    "tech": ThemeTokens(
        colorScheme="dark",
        bg="#0f172a",
        surface="#1e293b",
        surface2="#334155",
        text="#e8edf4",
        muted="#94a3b8",
        border="rgba(148,163,184,0.25)",
        accent="#6366f1",
        accentHover="#4f46e5",
        accentLight="rgba(99,102,241,0.2)",
        radiusPx=16,
        gapRem=1.5,
        density="normal",
        motion="expressive",
        heroMode="gradient",
        cardStyle="glass",
    ),
    "bold": ThemeTokens(
        colorScheme="light",
        bg="#ffffff",
        surface="#fff7ed",
        surface2="#ffedd5",
        text="#1c1917",
        muted="#78716c",
        border="#fed7aa",
        accent="#ea580c",
        accentHover="#c2410c",
        accentLight="#ffedd5",
        radiusPx=16,
        gapRem=1.0,
        density="compact",
        motion="expressive",
        heroMode="bold",
        cardStyle="soft",
    ),
    "custom": ThemeTokens(
        colorScheme="light",
        bg="#ffffff",
        surface="#F1F4F7",
        surface2="#EEF2F5",
        text="#111111",
        muted="#7A8799",
        border="#E5E7EB",
        accent="#7C3AED",
        accentHover="#6D28D9",
        accentLight="#EDE9FE",
        radiusPx=8,
        gapRem=1.5,
        density="normal",
        motion="subtle",
        heroMode="classic",
        cardStyle="soft",
    ),
}


def _hero_mode_from_semantic(mode: str | None) -> str:
    if mode == "cards":
        return "bold"
    if mode in ("gradient", "future_3d", "classic", "bold"):
        return mode or "classic"
    return "classic"


def _card_style_for(color_scheme: str, profile: str, hero_mode: str) -> str:
    preset = PROFILE_PRESETS.get(profile)
    if preset and profile != "custom":
        return preset.cardStyle
    if color_scheme == "dark":
        return "glass"
    if hero_mode == "future_3d":
        return "glass"
    return "soft"


def _merge_semantic(base: ThemeTokens, semantic: dict[str, str | None]) -> ThemeTokens:
    data = base.to_serializable()
    accent_key = semantic.get("accent")
    if accent_key and accent_key in ACCENT_HEX:
        data["accent"] = ACCENT_HEX[accent_key]
        if accent_key == "blue":
            data["accentHover"] = "#1d4ed8"
            data["accentLight"] = "#dbeafe"
        elif accent_key == "green":
            data["accentHover"] = "#047857"
            data["accentLight"] = "#d1fae5"
        else:
            data["accentHover"] = "#6D28D9"
            data["accentLight"] = "#EDE9FE"

    if semantic.get("background"):
        data["bg"] = semantic["background"]
    if semantic.get("surface"):
        data["surface"] = semantic["surface"]
        data["surface2"] = semantic["surface"]

    scheme = semantic.get("color_scheme")
    if scheme == "dark":
        data["colorScheme"] = "dark"
        data["bg"] = semantic.get("background") or "#0f1419"
        data["surface"] = semantic.get("surface") or "#1a2332"
        data["surface2"] = "#243044"
        data["text"] = "#e8edf4"
        data["muted"] = "#94a3b8"
        data["border"] = "rgba(148,163,184,0.25)"
        data["accentLight"] = f"{data['accent']}26"
    elif scheme == "light":
        data["colorScheme"] = "light"

    radius = semantic.get("radius")
    if radius in RADIUS_PX:
        data["radiusPx"] = RADIUS_PX[radius]

    density = semantic.get("density")
    if density in GAP_REM:
        data["density"] = density
        data["gapRem"] = GAP_REM[density]

    motion = semantic.get("motion")
    if motion in MOTION_DURATION:
        data["motion"] = motion

    hero = _hero_mode_from_semantic(semantic.get("hero_mode"))
    if semantic.get("hero_mode"):
        data["heroMode"] = hero

    data["cardStyle"] = _card_style_for(data["colorScheme"], "custom", data["heroMode"])
    return ThemeTokens(**data)


def _semantic_from_model(model: ThemeTokensModel | None) -> dict[str, str | None]:
    if not model:
        return {}
    return {
        "color_scheme": model.color_scheme,
        "accent": model.accent,
        "background": model.background,
        "surface": model.surface,
        "radius": model.radius,
        "density": model.density,
        "motion": model.motion,
        "hero_mode": model.hero_mode,
    }


def normalize_theme_tokens(style_config: LandingStyleConfigModel | None) -> ThemeTokens:
    if style_config is None:
        return PROFILE_PRESETS["university_platform"]

    profile = style_config.profile.value
    base = PROFILE_PRESETS.get(profile, PROFILE_PRESETS["university_platform"])

    has_explicit = (
        profile == "custom"
        or bool((style_config.custom_style_prompt or "").strip())
        or style_config.theme_tokens is not None
    )
    if not has_explicit:
        return base

    semantic: dict[str, str | None] = {}
    if profile == "custom" and style_config.custom_style_prompt:
        semantic = parse_style_intent(style_config.custom_style_prompt)
    if style_config.theme_tokens:
        semantic = {**semantic, **_semantic_from_model(style_config.theme_tokens)}

    if semantic:
        return _merge_semantic(base, semantic)
    return base


def serialize_theme_tokens(style_config: LandingStyleConfigModel | None) -> dict[str, Any]:
    return normalize_theme_tokens(style_config).to_serializable()


def hero_gradient_value(tokens: ThemeTokens) -> str:
    if tokens.heroMode == "gradient":
        return f"linear-gradient(135deg, {tokens.accentLight} 0%, transparent 55%)"
    if tokens.heroMode == "future_3d":
        return f"linear-gradient(120deg, {tokens.accentLight}, transparent 70%)"
    if tokens.heroMode == "bold":
        return f"linear-gradient(90deg, {tokens.accentLight}, transparent 80%)"
    return "none"


def theme_tokens_to_css_vars(tokens: ThemeTokens) -> dict[str, str]:
    motion_duration = MOTION_DURATION.get(tokens.motion, "0.25s")
    card_transform = CARD_TRANSFORM.get(tokens.cardStyle, CARD_TRANSFORM["soft"])
    hero_gradient = hero_gradient_value(tokens)
    hero_mode_css = "cards" if tokens.heroMode == "bold" else tokens.heroMode
    return {
        "--alf-bg": tokens.bg,
        "--alf-surface": tokens.surface,
        "--alf-surface-2": tokens.surface2,
        "--alf-text": tokens.text,
        "--alf-muted": tokens.muted,
        "--alf-border": tokens.border,
        "--alf-accent": tokens.accent,
        "--alf-accent-hover": tokens.accentHover,
        "--alf-accent-light": tokens.accentLight,
        "--alf-radius": f"{tokens.radiusPx}px",
        "--alf-gap": f"{tokens.gapRem}rem",
        "--alf-motion-duration": motion_duration,
        "--alf-card-transform": card_transform,
        "--alf-hero-gradient": hero_gradient,
        "--alf-hero-mode": hero_mode_css,
        # compatibility aliases
        "--bg": "var(--alf-bg)",
        "--surface": "var(--alf-surface)",
        "--surface-2": "var(--alf-surface-2)",
        "--text": "var(--alf-text)",
        "--muted": "var(--alf-muted)",
        "--border": "var(--alf-border)",
        "--accent": "var(--alf-accent)",
        "--accent-hover": "var(--alf-accent-hover)",
        "--accent-light": "var(--alf-accent-light)",
        "--radius": "var(--alf-radius)",
        "--gap": "var(--alf-gap)",
    }


def css_root_block(tokens: ThemeTokens) -> str:
    vars_map = theme_tokens_to_css_vars(tokens)
    lines = [f"  {key}: {value};" for key, value in vars_map.items()]
    return ":root {\n" + "\n".join(lines) + "\n}\n"
