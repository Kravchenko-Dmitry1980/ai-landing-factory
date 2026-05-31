"""WOW hero mascot helpers (Stage P.7.7).

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

_UI_CARDS = (
    "<div class='wow-hero-ui-card wow-hero-ui-card--chart' aria-hidden='true'>"
    "<span class='wow-hero-ui-bar wow-hero-ui-bar--1'></span>"
    "<span class='wow-hero-ui-bar wow-hero-ui-bar--2'></span>"
    "<span class='wow-hero-ui-bar wow-hero-ui-bar--3'></span>"
    "<span class='wow-hero-ui-bar wow-hero-ui-bar--4'></span>"
    "</div>"
    "<div class='wow-hero-ui-card wow-hero-ui-card--news' aria-hidden='true'>"
    "<span class='wow-hero-ui-line wow-hero-ui-line--title'></span>"
    "<span class='wow-hero-ui-line'></span>"
    "<span class='wow-hero-ui-line wow-hero-ui-line--short'></span>"
    "</div>"
    "<div class='wow-hero-ui-icon wow-hero-ui-icon--telegram' aria-hidden='true'>"
    "<svg viewBox='0 0 24 24' width='18' height='18' aria-hidden='true'>"
    "<path fill='currentColor' d='M9.78 15.28l-.28 3.92c.4 0 .57-.17.78-.38l1.87-1.78 "
    "3.88 2.85c.71.39 1.22.18 1.4-.64l2.54-12c.23-1.04-.38-1.45-1.07-1.2L2.36 9.82c-1.03.4-1.02.97-.18 "
    "1.22l4.47 1.39L18.9 6.5c.66-.43 1.26-.2.77.26'/></svg>"
    "</div>"
    "<div class='wow-hero-ui-card wow-hero-ui-card--pie' aria-hidden='true'>"
    "<span class='wow-hero-ui-pie'></span>"
    "</div>"
)

_MASCOT_RIG = (
    "<div class='wow-hero-mascot-rig'>"
    "<div class='wow-hero-mascot-pose'>"
    "<div class='wow-hero-mascot-figure'>"
    "<img class='wow-hero-mascot-image' src='{src}' alt='' "
    "width='480' height='480' loading='eager' decoding='async' draggable='false' />"
    "<span class='wow-hero-mascot-eyelid wow-hero-mascot-eyelid--left'></span>"
    "<span class='wow-hero-mascot-eyelid wow-hero-mascot-eyelid--right'></span>"
    "<span class='wow-hero-mascot-medallion'></span>"
    "<span class='wow-hero-mascot-typing-glow'></span>"
    "</div></div></div>"
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
    """Decorative hero mascot block (2.5D rig + cat image + 2D UI cards)."""

    resolved = src if src is not None else cat_mascot_data_uri()
    if not resolved:
        return ""

    safe_src = escape_text(resolved)
    rig = _MASCOT_RIG.format(src=safe_src)
    return (
        "<div class='wow-hero-mascot' aria-hidden='true'>"
        f"{_UI_CARDS}"
        "<div class='wow-hero-mascot-glow'></div>"
        "<div class='wow-hero-mascot-platform'></div>"
        f"{rig}"
        "</div>"
    )
