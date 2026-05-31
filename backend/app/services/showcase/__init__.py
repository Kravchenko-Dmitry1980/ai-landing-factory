"""VR/AR Showcase exhibition stand export (Stage P.5 MVP).

This package is a standalone export mode layered on top of generated landings.
It does NOT replace the normal landing export and has no impact on
``PRODUCT_MODE=simple`` defaults. The only runtime dependency it introduces
is the locally vendored A-Frame WebXR script, embedded only in showcase HTML.
"""

from app.services.showcase.showcase_schema import (
    ShowcaseConfig,
    ShowcaseExportResult,
    ShowcaseProject,
)
from app.services.showcase.showcase_html_exporter import ShowcaseHtmlExporter

__all__ = [
    "ShowcaseConfig",
    "ShowcaseExportResult",
    "ShowcaseProject",
    "ShowcaseHtmlExporter",
]
