"""URL validation, text escaping and accent sanitation for showcase export.

All user-controlled text that reaches the generated HTML/A-Frame scene must go
through these helpers. The goal is that a malicious ``title`` or ``demo_url``
can never execute script or break out of an attribute context.
"""

from __future__ import annotations

import logging
import re
from html import escape

logger = logging.getLogger(__name__)

# Schemes explicitly rejected even if they look like URLs.
_DANGEROUS_SCHEME_RE = re.compile(
    r"^\s*(?:javascript|data|vbscript|file|blob|about)\s*:",
    re.IGNORECASE,
)
_SAFE_ABSOLUTE_RE = re.compile(r"^\s*https?://", re.IGNORECASE)
# A hex color like #fff, #ffffff or #ffffffff (with alpha).
_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def escape_text(value: str | None) -> str:
    """HTML-escape arbitrary user text (also escapes quotes for attributes)."""

    if not value:
        return ""
    return escape(str(value), quote=True)


def sanitize_url(value: str | None) -> str | None:
    """Return a safe URL or ``None``.

    Accepts ``http(s)://`` absolute URLs and relative paths. Rejects
    ``javascript:``, ``data:``, ``vbscript:``, ``file:`` and similar.
    """

    if not value:
        return None
    candidate = str(value).strip()
    if not candidate:
        return None

    if _DANGEROUS_SCHEME_RE.match(candidate):
        logger.warning("showcase: rejected dangerous URL scheme: %r", candidate[:64])
        return None

    if _SAFE_ABSOLUTE_RE.match(candidate):
        return candidate

    # Relative path: must not contain a scheme separator that could smuggle
    # in something like "foo:bar" interpreted as a scheme.
    if "://" in candidate:
        logger.warning("showcase: rejected non-http(s) absolute URL: %r", candidate[:64])
        return None
    if re.match(r"^\s*[a-zA-Z][a-zA-Z0-9+.\-]*:", candidate):
        # Has a scheme-like prefix but is not http(s) -> reject.
        logger.warning("showcase: rejected scheme-like relative URL: %r", candidate[:64])
        return None

    # Allow site-relative and document-relative paths.
    if candidate.startswith(("/", "./", "../", "#")) or re.match(r"^[\w\-./]+$", candidate):
        return candidate

    logger.warning("showcase: rejected unrecognized URL: %r", candidate[:64])
    return None


def sanitize_accent(value: str | None, fallback: str) -> str:
    """Return a safe hex color string, or the theme fallback."""

    if not value:
        return fallback
    candidate = str(value).strip()
    if _HEX_COLOR_RE.match(candidate):
        return candidate
    return fallback


def js_string_literal(value: str | None) -> str:
    """Return a JSON-safe single-quoted JS string literal for inline handlers.

    Used only inside the showcase export's minimal inline click handler. We
    escape quotes, backslashes, angle brackets and line terminators so the
    value cannot terminate the script context.
    """

    if not value:
        return "''"
    out = (
        str(value)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "")
        .replace("\r", "")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    return f"'{out}'"
