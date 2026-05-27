"""Safe landing style configuration (no raw CSS from user)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LandingStyleProfile(StrEnum):
    UNIVERSITY_PLATFORM = "university_platform"
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    TECH = "tech"
    BOLD = "bold"
    CUSTOM = "custom"


class ThemeTokensModel(BaseModel):
    color_scheme: str | None = None
    accent: str | None = None
    background: str | None = None
    surface: str | None = None
    radius: str | None = None
    density: str | None = None
    motion: str | None = None
    hero_mode: str | None = None

    @field_validator("background", "surface")
    @classmethod
    def _hex_only(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v.startswith("#") or len(v) not in (4, 7, 9):
            return None
        if any(c not in "0123456789abcdefABCDEF#" for c in v):
            return None
        return v


class LandingStyleConfigModel(BaseModel):
    profile: LandingStyleProfile = LandingStyleProfile.UNIVERSITY_PLATFORM
    custom_style_prompt: str | None = None
    theme_tokens: ThemeTokensModel | None = None

    @field_validator("custom_style_prompt")
    @classmethod
    def _strip_prompt(cls, v: str | None) -> str | None:
        if not v:
            return None
        text = v.strip()[:2000]
        lowered = text.lower()
        if "<script" in lowered or "javascript:" in lowered or "{" in text and ":" in text:
            if "body {" in lowered or "@import" in lowered:
                return None
        return text or None


def default_style_config() -> LandingStyleConfigModel:
    return LandingStyleConfigModel(
        profile=LandingStyleProfile.UNIVERSITY_PLATFORM,
        theme_tokens=None,
    )


def effective_style_config(contract) -> LandingStyleConfigModel:
    """Resolve style for export/preview from contract (incl. legacy)."""
    from app.schemas.landing_contract import LandingContract, LandingStylePreset

    if isinstance(contract, LandingContract) and contract.style_config is not None:
        return contract.style_config

    ps = ""
    style_val = ""
    if isinstance(contract, LandingContract):
        ps = (contract.presentation_style or "").strip()
        style_val = (
            contract.style.value
            if isinstance(contract.style, LandingStylePreset)
            else str(contract.style or "")
        )

    if ps and not ps.startswith("layout:"):
        try:
            return LandingStyleConfigModel(profile=LandingStyleProfile(ps))
        except ValueError:
            pass

    legacy_map = {
        "minimal": LandingStyleProfile.MINIMAL,
        "corporate": LandingStyleProfile.CORPORATE,
        "tech": LandingStyleProfile.TECH,
        "bold": LandingStyleProfile.BOLD,
        "university_platform": LandingStyleProfile.UNIVERSITY_PLATFORM,
    }
    if style_val in legacy_map:
        return LandingStyleConfigModel(profile=legacy_map[style_val])

    return default_style_config()


class StyleConfigPatch(BaseModel):
    profile: LandingStyleProfile
    custom_style_prompt: str | None = None
    theme_tokens: ThemeTokensModel | None = None


class StyleConfigResponse(BaseModel):
    project_id: str
    style_config: LandingStyleConfigModel


def parse_style_config_query(raw: str | None) -> LandingStyleConfigModel | None:
    if not raw or not raw.strip():
        return None
    import json

    try:
        data: Any = json.loads(raw)
        return LandingStyleConfigModel.model_validate(data)
    except Exception:
        return None
