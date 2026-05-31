"""Interactive WOW Bundle ZIP exporter (Stage P.7.2).

Builds a portable, offline-friendly ZIP that ships the standalone React/R3F WOW
app (built into ``frontend/dist-wow``) together with the project's data. After
unzipping, ``index.html`` boots the interactive WOW landing with no backend, no
dev server and no external CDN.

ZIP layout::

    index.html
    assets/wow-app.js
    assets/wow-app.css        (only if the build produced it)
    data/landing-contract.json
    README_DEMO.txt

The project data is embedded inline inside ``index.html`` (``<script
type="application/json">``) so the bundle works from ``file://`` without any
``fetch``. A copy is also written to ``data/landing-contract.json`` for debugging.
"""

from __future__ import annotations

import io
import json
import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings
from app.schemas.landing_contract import LandingContract
from app.services.export.wow_bundle_data import build_wow_bundle_data
from app.services.showcase.showcase_safety import escape_text

logger = logging.getLogger(__name__)

# Resolved relative to the repo root (settings.base_dir == backend dir).
DEFAULT_ASSETS_DIR: Path = settings.base_dir.parent / "frontend" / "dist-wow" / "assets"

ZIP_INDEX_NAME = "index.html"
ZIP_JS_ENTRY = "assets/wow-app.js"
ZIP_CSS_ENTRY = "assets/wow-app.css"
ZIP_DATA_ENTRY = "data/landing-contract.json"
ZIP_README_ENTRY = "README_DEMO.txt"
ZIP_DOWNLOAD_FILENAME = "ai-wow-landing.zip"

_SOURCE_JS_NAME = "wow-app.js"
_SOURCE_CSS_NAME = "wow-app.css"

_BUILD_INSTRUCTION = "cd frontend && npm run build:wow-bundle"


@dataclass(frozen=True)
class WowBundleExportOptions:
    """Options for the interactive WOW bundle export."""

    include_data_inline: bool = True
    demo_url: str | None = None
    showcase_url: str | None = None


@dataclass(frozen=True)
class WowBundleExportResult:
    """Generated ZIP bytes plus export metadata."""

    data: bytes
    entries: tuple[str, ...]
    metric_count: int
    pipeline_count: int
    has_css: bool


def _validate_zip_entry_name(name: str) -> None:
    """Reject path traversal or absolute paths in ZIP entries."""

    normalized = name.replace("\\", "/")
    if normalized.startswith("/") or normalized.startswith("../"):
        raise ValueError(f"unsafe ZIP entry path: {name!r}")
    if ".." in normalized.split("/"):
        raise ValueError(f"unsafe ZIP entry path: {name!r}")


def _safe_inline_json(payload: dict[str, Any]) -> str:
    """JSON for a ``type=application/json`` script tag (no breakout possible)."""

    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Inside a JSON string the only sequence that can close the script element is
    # ``</``. Escaping ``<`` and ``>`` (which only ever appear inside string
    # values in our payload) neutralises both breakout and markup injection while
    # remaining valid JSON via the ``\uXXXX`` escape understood by ``JSON.parse``.
    return (
        text.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _build_index_html(bundle_data: dict[str, Any], *, has_css: bool) -> str:
    title = escape_text(bundle_data.get("project", {}).get("title") or "AI WOW Landing")
    inline_json = _safe_inline_json(bundle_data)
    css_link = (
        f'  <link rel="stylesheet" href="{ZIP_CSS_ENTRY}" />\n' if has_css else ""
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="ru">\n'
        "<head>\n"
        '  <meta charset="utf-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        f"  <title>{title}</title>\n"
        '  <meta name="robots" content="noindex" />\n'
        f"{css_link}"
        "  <style>\n"
        "    html,body{margin:0;padding:0;background:#f4f6fd;color:#1b1f3b;"
        "font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;}\n"
        "    #wow-bundle-root{min-height:100vh;}\n"
        "    .wow-boot-fallback{padding:48px;max-width:760px;margin:0 auto;}\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        f'  <script id="wow-data" type="application/json">{inline_json}</script>\n'
        '  <div id="wow-bundle-root">\n'
        '    <noscript>\n'
        '      <div class="wow-boot-fallback">\n'
        f"        <h1>{title}</h1>\n"
        "        <p>Для интерактивной WOW-версии включите JavaScript. "
        "Это переносимый демонстрационный артефакт: распакуйте архив и "
        "откройте index.html.</p>\n"
        "      </div>\n"
        "    </noscript>\n"
        "  </div>\n"
        f'  <script src="{ZIP_JS_ENTRY}"></script>\n'
        "</body>\n"
        "</html>\n"
    )


def _build_readme(bundle_data: dict[str, Any]) -> str:
    title = bundle_data.get("project", {}).get("title") or "AI WOW Landing"
    return (
        "Interactive WOW Landing — переносимый демо-артефакт\n"
        "===================================================\n\n"
        f"Проект: {title}\n\n"
        "Что это:\n"
        "  Интерактивная React/R3F-версия лендинга с 3D WOW-hero.\n"
        "  Работает офлайн, без backend, без dev-сервера и без CDN.\n\n"
        "Как открыть:\n"
        "  1. Распакуйте архив целиком (со всеми папками assets/ и data/).\n"
        "  2. Откройте index.html двойным кликом.\n\n"
        "Если браузер блокирует локальный запуск (file://):\n"
        "  Запустите простой статический сервер из папки с index.html:\n"
        "    python -m http.server 8080\n"
        "  затем откройте http://localhost:8080/\n\n"
        "Состав архива:\n"
        "  index.html                  — точка входа\n"
        "  assets/wow-app.js           — React/R3F runtime (всё встроено)\n"
        "  assets/wow-app.css          — стили (если присутствуют)\n"
        "  data/landing-contract.json  — данные проекта (для отладки)\n"
        "  README_DEMO.txt             — этот файл\n"
    )


def _read_assets(assets_dir: Path) -> tuple[bytes, bytes | None]:
    js_path = assets_dir / _SOURCE_JS_NAME
    if not js_path.is_file():
        raise FileNotFoundError(
            "WOW bundle frontend assets not found: "
            f"{js_path}. Build them first: {_BUILD_INSTRUCTION}"
        )
    js_bytes = js_path.read_bytes()
    css_path = assets_dir / _SOURCE_CSS_NAME
    css_bytes = css_path.read_bytes() if css_path.is_file() else None
    return js_bytes, css_bytes


def build_wow_bundle_zip_with_meta(
    contract: LandingContract,
    options: WowBundleExportOptions | None = None,
    *,
    assets_dir: Path | None = None,
) -> WowBundleExportResult:
    """Build the interactive WOW bundle ZIP and return bytes plus metadata."""

    opts = options or WowBundleExportOptions()
    resolved_assets = assets_dir or DEFAULT_ASSETS_DIR

    js_bytes, css_bytes = _read_assets(resolved_assets)
    has_css = css_bytes is not None

    bundle_data = build_wow_bundle_data(
        contract,
        demo_url=opts.demo_url,
        showcase_url=opts.showcase_url,
    )

    index_html = _build_index_html(bundle_data, has_css=has_css)
    readme = _build_readme(bundle_data)
    data_json = json.dumps(bundle_data, ensure_ascii=False, indent=2)

    entries: list[str] = [ZIP_INDEX_NAME, ZIP_JS_ENTRY]
    if has_css:
        entries.append(ZIP_CSS_ENTRY)
    entries.extend([ZIP_DATA_ENTRY, ZIP_README_ENTRY])
    for entry in entries:
        _validate_zip_entry_name(entry)

    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        archive.writestr(ZIP_INDEX_NAME, index_html.encode("utf-8"))
        archive.writestr(ZIP_JS_ENTRY, js_bytes)
        if css_bytes is not None:
            archive.writestr(ZIP_CSS_ENTRY, css_bytes)
        archive.writestr(ZIP_DATA_ENTRY, data_json.encode("utf-8"))
        archive.writestr(ZIP_README_ENTRY, readme.encode("utf-8"))

    return WowBundleExportResult(
        data=buffer.getvalue(),
        entries=tuple(entries),
        metric_count=len(bundle_data.get("metrics", [])),
        pipeline_count=len(bundle_data.get("pipeline", [])),
        has_css=has_css,
    )


def build_wow_bundle_zip(
    contract: LandingContract,
    options: WowBundleExportOptions | None = None,
    *,
    assets_dir: Path | None = None,
) -> bytes:
    """Return portable interactive WOW bundle ZIP bytes."""

    return build_wow_bundle_zip_with_meta(
        contract, options, assets_dir=assets_dir
    ).data
