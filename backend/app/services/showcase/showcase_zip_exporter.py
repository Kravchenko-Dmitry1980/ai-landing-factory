"""Portable ZIP bundle export for VR/AR Showcase (Stage P.5.2).

Builds an in-memory ZIP containing ``showcase.html``, the vendored A-Frame
runtime, and its license — ready for offline unzip-and-open workflows.
"""

from __future__ import annotations

import io
import logging
import zipfile
from dataclasses import dataclass

from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter
from app.services.showcase.showcase_schema import ShowcaseConfig
from app.services.showcase.showcase_vendor import (
    DEFAULT_AFRAME_SRC,
    VENDOR_LICENSE,
    VENDOR_SOURCE,
    ZIP_AFRAME_ENTRY,
    ZIP_HTML_NAME,
    ZIP_LICENSE_ENTRY,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ShowcaseZipExportResult:
    """Metadata for a generated showcase ZIP bundle."""

    data: bytes
    project_count: int
    mode: str
    warnings: list[str]
    entries: tuple[str, ...]


def _assert_vendor_assets_present() -> None:
    missing: list[str] = []
    if not VENDOR_SOURCE.is_file():
        missing.append(str(VENDOR_SOURCE))
    if not VENDOR_LICENSE.is_file():
        missing.append(str(VENDOR_LICENSE))
    if missing:
        raise FileNotFoundError(
            "Vendored A-Frame assets missing for ZIP export: "
            + "; ".join(missing)
        )


def _validate_zip_entry_name(name: str) -> None:
    """Reject path traversal or absolute paths in ZIP entries."""

    normalized = name.replace("\\", "/")
    if normalized.startswith("/") or normalized.startswith("../"):
        raise ValueError(f"unsafe ZIP entry path: {name!r}")
    if ".." in normalized.split("/"):
        raise ValueError(f"unsafe ZIP entry path: {name!r}")


def build_showcase_zip(config: ShowcaseConfig) -> bytes:
    """Return portable showcase ZIP bytes (HTML + vendored A-Frame + license)."""

    return build_showcase_zip_with_meta(config).data


def build_showcase_zip_with_meta(config: ShowcaseConfig) -> ShowcaseZipExportResult:
    """Build ZIP and return bytes plus export metadata."""

    _assert_vendor_assets_present()

    exporter = ShowcaseHtmlExporter(aframe_src=DEFAULT_AFRAME_SRC)
    export_result = exporter.export(config)

    if exporter._aframe_src != DEFAULT_AFRAME_SRC:
        logger.warning("ZIP export forced local aframe_src=%s", DEFAULT_AFRAME_SRC)

    entries = (ZIP_HTML_NAME, ZIP_AFRAME_ENTRY, ZIP_LICENSE_ENTRY)
    for entry in entries:
        _validate_zip_entry_name(entry)

    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        archive.writestr(ZIP_HTML_NAME, export_result.html.encode("utf-8"))
        archive.write(VENDOR_SOURCE, arcname=ZIP_AFRAME_ENTRY)
        archive.write(VENDOR_LICENSE, arcname=ZIP_LICENSE_ENTRY)

    data = buffer.getvalue()
    return ShowcaseZipExportResult(
        data=data,
        project_count=export_result.project_count,
        mode=export_result.mode,
        warnings=list(export_result.warnings),
        entries=entries,
    )
