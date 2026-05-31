"""WOW hero mascot helpers (Stage P.7.X).

The cat assistant PNG lives in ``frontend/public/assets/wow/``. For the
self-contained CSS WOW HTML export we inline it as a data URI so the artifact
works without shipping extra files.
"""

from __future__ import annotations

import base64
import logging
from functools import lru_cache

from app.config import settings
from app.services.showcase.showcase_safety import escape_text

logger = logging.getLogger(__name__)

CAT_MASCOT_REL = "assets/wow/cat-assistant.png"
_CAT_SOURCE = (
    settings.base_dir.parent / "frontend" / "public" / "assets" / "wow" / "cat-assistant.png"
)


@lru_cache(maxsize=1)
def cat_mascot_data_uri() -> str:
    """Return a PNG data URI for the hero cat mascot, or empty if missing."""

    try:
        raw = _CAT_SOURCE.read_bytes()
    except OSError:
        logger.warning("WOW cat mascot asset missing at %s", _CAT_SOURCE)
        return ""
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_wow_hero_mascot_html(*, src: str | None = None) -> str:
    """Decorative hero mascot block (portal + pedestal + cat image)."""

    resolved = src if src is not None else cat_mascot_data_uri()
    if not resolved:
        return ""

    safe_src = escape_text(resolved)
    return (
        "<div class='wow-hero-mascot' aria-hidden='true'>"
        "<div class='wow-hero-mascot-glow'></div>"
        "<div class='wow-hero-mascot-portal'>"
        "<span class='wow-hero-mascot-ring'></span>"
        "<span class='wow-hero-mascot-ring wow-hero-mascot-ring--inner'></span>"
        "</div>"
        "<div class='wow-hero-mascot-pedestal'>"
        "<span class='wow-hero-mascot-pedestal-tier wow-hero-mascot-pedestal-tier--1'></span>"
        "<span class='wow-hero-mascot-pedestal-tier wow-hero-mascot-pedestal-tier--2'></span>"
        "</div>"
        f"<img class='wow-hero-mascot-image' src='{safe_src}' alt='' "
        "width='480' height='480' loading='eager' decoding='async' draggable='false' />"
        "<span class='wow-hero-mascot-float wow-hero-mascot-float--1'>AI Assistant</span>"
        "<span class='wow-hero-mascot-float wow-hero-mascot-float--2'>Neural scan</span>"
        "<span class='wow-hero-mascot-float wow-hero-mascot-float--3'>Live</span>"
        "</div>"
    )
