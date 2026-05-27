"""Deterministic custom style intent → safe theme tokens (mirrors frontend styleIntent.ts)."""

from __future__ import annotations

import re
from typing import TypedDict

DANGEROUS_PATTERN = re.compile(
    r"(<\s*script|javascript:|@import|url\s*\(|expression\s*\(|body\s*\{|display\s*:\s*none|\.css|{\s*[^}]*:)",
    re.I,
)

ACCENT_HEX = {
    "blue": "#2563eb",
    "violet": "#7C3AED",
    "green": "#059669",
}

DARK_SURFACES = {"background": "#0f1419", "surface": "#1a2332"}
LIGHT_SURFACES = {"background": "#ffffff", "surface": "#F1F4F7"}

UNIVERSITY_DEFAULT: dict[str, str | None] = {
    "color_scheme": "light",
    "accent": "violet",
    "background": "#ffffff",
    "surface": "#F1F4F7",
    "radius": "soft",
    "density": "normal",
    "motion": "subtle",
    "hero_mode": "classic",
}


class SemanticTokens(TypedDict, total=False):
    color_scheme: str | None
    accent: str | None
    background: str | None
    surface: str | None
    radius: str | None
    density: str | None
    motion: str | None
    hero_mode: str | None


def _normalize_prompt(prompt: str) -> str:
    text = prompt.lower().replace("ё", "е")
    text = re.sub(r"[^\w\s#-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _contains_dangerous(prompt: str) -> bool:
    return bool(DANGEROUS_PATTERN.search(prompt))


def parse_style_intent(prompt: str) -> SemanticTokens:
    raw = prompt.strip()
    if not raw or _contains_dangerous(raw):
        return dict(UNIVERSITY_DEFAULT)

    text = _normalize_prompt(raw)
    tokens: SemanticTokens = dict(UNIVERSITY_DEFAULT)

    if re.search(r"темн|dark|ночн", text):
        tokens["color_scheme"] = "dark"
        tokens["background"] = DARK_SURFACES["background"]
        tokens["surface"] = DARK_SURFACES["surface"]
    elif re.search(r"светл|light|бел", text):
        tokens["color_scheme"] = "light"
        tokens["background"] = LIGHT_SURFACES["background"]
        tokens["surface"] = LIGHT_SURFACES["surface"]

    if re.search(r"син", text):
        tokens["accent"] = "blue"
    elif re.search(r"фиолет", text):
        tokens["accent"] = "violet"
    elif re.search(r"зелен|зелён", text):
        tokens["accent"] = "green"

    if re.search(r"остр|sharp|строг", text):
        tokens["radius"] = "sharp"
    elif re.search(r"скруг|rounded|мягк", text):
        tokens["radius"] = "rounded"

    if re.search(r"компакт|compact|плотн", text):
        tokens["density"] = "compact"
    elif re.search(r"простор|spacious|воздуш", text):
        tokens["density"] = "spacious"

    if re.search(r"анимац|плавн|expressive|динамич|технолог", text):
        tokens["motion"] = "expressive"
    elif re.search(r"без анима|static|none", text):
        tokens["motion"] = "none"
    elif re.search(r"строг|корпоратив|делов", text):
        tokens["motion"] = "subtle"

    if re.search(r"3d|объемн|объёмн|интерактив", text):
        tokens["hero_mode"] = "future_3d"
    elif re.search(r"технолог|cyber|\bai\b", text):
        tokens["hero_mode"] = "gradient"
    elif re.search(r"карточк|cards", text):
        tokens["hero_mode"] = "cards"

    if re.search(r"строг|корпоратив", text):
        tokens.setdefault("density", "normal")
        tokens.setdefault("motion", "subtle")

    if re.search(r"технолог|cyber|\bai\b", text):
        tokens.setdefault("hero_mode", "gradient")
        tokens.setdefault("accent", "blue")

    if tokens.get("hero_mode") == "future_3d":
        tokens.setdefault("motion", "expressive")

    return tokens
