"""Pydantic v2 data contract for the VR/AR Showcase export (Stage P.5)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ShowcaseLayout(StrEnum):
    GALLERY_ARC = "gallery_arc"
    GRID_HALL = "grid_hall"
    CIRCLE_BOOTHS = "circle_booths"


class ShowcaseMode(StrEnum):
    WEB3D = "web3d"
    VR_READY = "vr_ready"


class ShowcaseTheme(StrEnum):
    UNIVERSITY = "university"
    TECH = "tech"
    DARK = "dark"


class ShowcaseProject(BaseModel):
    """A single exhibit (one landing/demo) inside the showcase."""

    id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=600)
    landing_url: str | None = Field(default=None, max_length=2048)
    demo_url: str | None = Field(default=None, max_length=2048)
    demo_label: str | None = Field(default=None, max_length=80)
    category: str | None = Field(default=None, max_length=80)
    tags: list[str] = Field(default_factory=list)
    accent: str | None = Field(default=None, max_length=32)
    source_project_id: str | None = Field(default=None, max_length=128)


class ShowcaseConfig(BaseModel):
    """Full showcase definition submitted by the builder UI or a script."""

    title: str = Field(min_length=1, max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    organization: str | None = Field(default=None, max_length=200)
    layout: ShowcaseLayout = ShowcaseLayout.GALLERY_ARC
    mode: ShowcaseMode = ShowcaseMode.WEB3D
    theme: ShowcaseTheme = ShowcaseTheme.UNIVERSITY
    projects: list[ShowcaseProject] = Field(default_factory=list)


class ShowcaseExportResult(BaseModel):
    """Result returned by the exporter / API endpoint."""

    html: str
    project_count: int
    mode: str
    warnings: list[str] = Field(default_factory=list)
