"""Landing export mode contract (Stage P.7 — WOW exhibition export).

Defines the two stable export modes (``standard`` / ``wow``) and the optional
WOW 3D runtime selector. Parsing helpers raise ``ValueError`` on invalid input
so the API layer can return a clear ``400`` instead of silently downgrading.
"""

from __future__ import annotations

from enum import StrEnum


class LandingExportMode(StrEnum):
    """Which HTML export pipeline to use."""

    STANDARD = "standard"
    WOW = "wow"


class Wow3dRuntime(StrEnum):
    """Optional 3D runtime layered on top of the WOW CSS hero."""

    NONE = "none"
    AFRAME = "aframe"


def parse_export_mode(raw: str | None) -> LandingExportMode:
    """Parse ``mode`` / ``export_mode`` query value.

    ``None`` / empty -> ``standard`` (default). Unknown value -> ``ValueError``.
    """

    if raw is None or not str(raw).strip():
        return LandingExportMode.STANDARD
    key = str(raw).strip().lower()
    try:
        return LandingExportMode(key)
    except ValueError as exc:
        valid = ", ".join(m.value for m in LandingExportMode)
        raise ValueError(
            f"Invalid export mode {raw!r}. Expected one of: {valid}."
        ) from exc


def parse_wow_runtime(raw: str | None) -> Wow3dRuntime:
    """Parse ``wow_3d_runtime`` query value.

    ``None`` / empty -> ``none`` (default, no A-Frame). Unknown -> ``ValueError``.
    A-Frame is never enabled implicitly — it must be requested explicitly.
    """

    if raw is None or not str(raw).strip():
        return Wow3dRuntime.NONE
    key = str(raw).strip().lower()
    try:
        return Wow3dRuntime(key)
    except ValueError as exc:
        valid = ", ".join(r.value for r in Wow3dRuntime)
        raise ValueError(
            f"Invalid wow_3d_runtime {raw!r}. Expected one of: {valid}."
        ) from exc
