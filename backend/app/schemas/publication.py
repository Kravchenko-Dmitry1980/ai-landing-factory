from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.repositories.publication_repository import Publication, PublicationStatus
from app.services.library.topics import TOPICS_BY_KEY

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


class TopicTag(BaseModel):
    key: str
    label: str


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
    # Strongest first; empty when the text matches no topic of the library.
    topics: list[TopicTag]
    theme: str
    version: int
    first_published_at: datetime
    published_at: datetime
    published_by_name: str | None = None

    @classmethod
    def of(cls, publication: Publication, topics: tuple[str, ...] = ()) -> LibraryCard:
        return cls(
            project_id=publication.project_id,
            slug=publication.slug,
            path=publication_path(publication.slug),
            title=publication.title,
            summary=publication.summary,
            customer=publication.customer,
            lead=publication.lead,
            people=publication.people,
            topics=[TopicTag(key=key, label=TOPICS_BY_KEY[key].label) for key in topics],
            theme=publication.theme,
            version=publication.version,
            first_published_at=publication.first_published_at,
            published_at=publication.published_at,
            published_by_name=publication.published_by_name,
        )


class TopicCount(BaseModel):
    key: str
    label: str
    count: int


class LibraryHit(BaseModel):
    card: LibraryCard
    # Where the query was found: "в названии", "участник: …", "похожая тема: …".
    reasons: list[str]
    similar_topic: bool = False


class LibrarySearch(BaseModel):
    # Everything published, whatever the query: the library says how big it is.
    total: int
    query: str
    # Counted before the list is cut to the limit.
    direct_total: int
    related_total: int
    # Words of the query that count; 0 with a non-empty query means nothing searchable was typed.
    terms: int
    hits: list[LibraryHit]


class LibraryShelf(BaseModel):
    key: str
    label: str
    note: str
    cards: list[LibraryCard]


class LibraryShelves(BaseModel):
    """The library's front page: newest landings, then one carousel per topic."""

    total: int
    fresh: list[LibraryCard]
    shelves: list[LibraryShelf]
    topics: list[TopicCount]


class SimilarCard(BaseModel):
    card: LibraryCard
    # What the two landings share: "общая тема: …", "общий заказчик: …", "общие слова: …".
    reason: str
