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
    description: str = Field(default="", max_length=1000)
    landing_url: str | None = Field(default=None, max_length=2048)
    demo_url: str | None = Field(default=None, max_length=2048)
    demo_label: str | None = Field(default=None, max_length=80)
    category: str | None = Field(default=None, max_length=80)
    tags: list[str] = Field(default_factory=list)
    accent: str | None = Field(default=None, max_length=32)
    source_project_id: str | None = Field(default=None, max_length=128)
    order_index: int = Field(default=0)


class ShowcaseConfig(BaseModel):
    """Full showcase definition submitted by the builder UI or a script.

    ``id`` / ``created_at`` / ``updated_at`` are optional so the stateless
    export endpoints (Stage P.5) keep accepting bare configs, while the
    registry (Stage P.6) always populates them.
    """

    id: str | None = Field(default=None, max_length=128)
    title: str = Field(min_length=1, max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    organization: str | None = Field(default=None, max_length=200)
    layout: ShowcaseLayout = ShowcaseLayout.GALLERY_ARC
    mode: ShowcaseMode = ShowcaseMode.WEB3D
    theme: ShowcaseTheme = ShowcaseTheme.UNIVERSITY
    projects: list[ShowcaseProject] = Field(default_factory=list)
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)


class ShowcaseExportResult(BaseModel):
    """Result returned by the exporter / API endpoint."""

    html: str
    project_count: int
    mode: str
    warnings: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Stage P.6 — Registry request/response contracts
# --------------------------------------------------------------------------


class ShowcaseCreateRequest(BaseModel):
    """Payload to create a new (empty) showcase."""

    title: str = Field(min_length=1, max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    organization: str | None = Field(default=None, max_length=200)
    layout: ShowcaseLayout = ShowcaseLayout.GALLERY_ARC
    mode: ShowcaseMode = ShowcaseMode.WEB3D
    theme: ShowcaseTheme = ShowcaseTheme.UNIVERSITY


class ShowcaseUpdateRequest(BaseModel):
    """Partial update of showcase-level settings."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    organization: str | None = Field(default=None, max_length=200)
    layout: ShowcaseLayout | None = None
    mode: ShowcaseMode | None = None
    theme: ShowcaseTheme | None = None


class ShowcaseProjectCreateRequest(BaseModel):
    """Payload to add one project/exhibit to a showcase."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    landing_url: str | None = Field(default=None, max_length=2048)
    demo_url: str | None = Field(default=None, max_length=2048)
    demo_label: str | None = Field(default=None, max_length=80)
    category: str | None = Field(default=None, max_length=80)
    tags: list[str] | None = None
    accent: str | None = Field(default=None, max_length=32)
    source_project_id: str | None = Field(default=None, max_length=128)


class ShowcaseProjectUpdateRequest(BaseModel):
    """Partial update of a single project/exhibit."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    landing_url: str | None = Field(default=None, max_length=2048)
    demo_url: str | None = Field(default=None, max_length=2048)
    demo_label: str | None = Field(default=None, max_length=80)
    category: str | None = Field(default=None, max_length=80)
    tags: list[str] | None = None
    accent: str | None = Field(default=None, max_length=32)
    source_project_id: str | None = Field(default=None, max_length=128)


class ShowcaseReorderRequest(BaseModel):
    """Reorder projects by a full list of project ids."""

    ordered_ids: list[str] = Field(default_factory=list)


class ShowcaseSummary(BaseModel):
    """Lightweight list-view entry for the showcase registry."""

    id: str
    title: str
    project_count: int
    updated_at: str | None = None
    created_at: str | None = None


class LandingCandidate(BaseModel):
    """An existing landing project that can be attached to a showcase."""

    project_id: str
    title: str
    client: str | None = None
    description: str | None = None
    preview_url: str
    export_html_url: str
    landing_url: str
    export_available: bool = False
    updated_at: str | None = None
