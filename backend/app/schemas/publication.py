from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.repositories.publication_repository import Publication, PublicationStatus

# The rendered page with its fonts and the cat inside is about 250 KB; leave room for long texts.
MAX_HTML_CHARS = 5_000_000


def publication_path(slug: str) -> str:
    return f"/p/{slug}"


class PublishRequest(BaseModel):
    html: str = Field(max_length=MAX_HTML_CHARS)
    theme: Literal["night", "light"]
    # The contract version the page was rendered from: publishing fails if the landing changed since.
    contract_version: int
    summary: str = Field(default="", max_length=2000)


class PublicationInfo(BaseModel):
    """The publication of one project, for the studio."""

    slug: str
    path: str
    status: PublicationStatus
    version: int
    contract_version: int
    theme: str
    title: str
    first_published_at: datetime
    published_at: datetime
    published_by_name: str | None = None
    withdrawn_at: datetime | None = None

    @classmethod
    def of(cls, publication: Publication) -> PublicationInfo:
        return cls(
            slug=publication.slug,
            path=publication_path(publication.slug),
            status=publication.status,
            version=publication.version,
            contract_version=publication.contract_version,
            theme=publication.theme,
            title=publication.title,
            first_published_at=publication.first_published_at,
            published_at=publication.published_at,
            published_by_name=publication.published_by_name,
            withdrawn_at=publication.withdrawn_at,
        )


class LibraryPage(BaseModel):
    # Everything published, whatever the query: the library says how big it is.
    total: int
    cards: list[LibraryCard]


class LibraryCard(BaseModel):
    """A published landing as the library lists it."""

    project_id: str
    slug: str
    path: str
    title: str
    summary: str
    customer: str
    lead: str
    people: list[str]
    theme: str
    version: int
    first_published_at: datetime
    published_at: datetime
    published_by_name: str | None = None

    @classmethod
    def of(cls, publication: Publication) -> LibraryCard:
        return cls(
            project_id=publication.project_id,
            slug=publication.slug,
            path=publication_path(publication.slug),
            title=publication.title,
            summary=publication.summary,
            customer=publication.customer,
            lead=publication.lead,
            people=publication.people,
            theme=publication.theme,
            version=publication.version,
            first_published_at=publication.first_published_at,
            published_at=publication.published_at,
            published_by_name=publication.published_by_name,
        )
