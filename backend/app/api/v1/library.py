"""The library of published landings, for every signed-in account."""

import logging

from fastapi import APIRouter, HTTPException, Query, Response

from app.core.dependencies import get_publication_repository
from app.repositories.publication_repository import Publication
from app.schemas.publication import (
    LibraryCard,
    LibraryHit,
    LibrarySearch,
    LibraryShelf,
    LibraryShelves,
    SimilarCard,
    TopicCount,
)
from app.services.library.index import LibraryIndex, library_index, publication_topics
from app.services.library.topics import TOPICS_BY_KEY

logger = logging.getLogger(__name__)
router = APIRouter()

# Published pages are documents without scripts. The sandbox gives them no origin even if
# someone opens this address directly, so a page can never act on behalf of the viewer.
PAGE_CSP = (
    "sandbox; default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
)
NOT_IN_LIBRARY = "Такого лендинга в библиотеке нет: его сняли с публикации или адрес неверный."
MAX_QUERY_CHARS = 200


def _library() -> tuple[dict[str, Publication], LibraryIndex]:
    """
    Fresh rows for the cards (names, dates) and the index for ranking. The rows come without
    texts; the texts are read only when the index has to be rebuilt.
    """
    repo = get_publication_repository()
    current = repo.list_published(with_texts=False)
    index = library_index(current, lambda: repo.list_published())
    return {p.slug: p for p in current}, index


def _card(index: LibraryIndex, publication: Publication) -> LibraryCard:
    return LibraryCard.of(publication, index.topics_of(publication.slug))


@router.get("", response_model=LibrarySearch)
def search_library(
    q: str = Query(default=""),
    limit: int = Query(default=100, ge=1, le=500),
) -> LibrarySearch:
    """
    Without a query: everything, newest first. With one: landings that contain every word
    (title, then people and customer, topic, description, text), then landings on a similar topic.
    A query longer than the field allows is cut, not refused: a shared link must still open.
    """
    query = q.strip()[:MAX_QUERY_CHARS]
    fresh, index = _library()
    result = index.search(query)
    hits = [hit for hit in result.hits if hit.publication.slug in fresh][:limit]
    return LibrarySearch(
        total=len(fresh),
        query=query,
        direct_total=result.direct_total,
        related_total=result.related_total,
        terms=result.terms,
        hits=[
            LibraryHit(
                card=_card(index, fresh[hit.publication.slug]),
                reasons=list(hit.reasons),
                similar_topic=hit.similar_topic,
            )
            for hit in hits
        ],
    )


# "_" never appears in a landing address (slugify keeps a-z, 0-9 and "-"), so no landing hides here.
@router.get("/_shelves", response_model=LibraryShelves)
def library_shelves() -> LibraryShelves:
    """The front page of the library: the newest landings and one carousel per topic."""
    fresh, index = _library()

    def cards(publications) -> list[LibraryCard]:
        return [_card(index, fresh[p.slug]) for p in publications if p.slug in fresh]

    return LibraryShelves(
        total=len(fresh),
        fresh=cards(index.fresh()),
        shelves=[
            LibraryShelf(key=s.key, label=s.label, note=s.note, cards=cards(s.publications)) for s in index.shelves()
        ],
        topics=[TopicCount(key=key, label=TOPICS_BY_KEY[key].label, count=n) for key, n in index.topic_counts()],
    )


@router.get("/{slug}", response_model=LibraryCard)
def get_card(slug: str) -> LibraryCard:
    """One row and at most one landing parsed: opening a landing never waits for the whole index."""
    publication = get_publication_repository().get_published(slug)
    if publication is None:
        raise HTTPException(404, NOT_IN_LIBRARY)
    return LibraryCard.of(publication, publication_topics(publication))


@router.get("/{slug}/similar", response_model=list[SimilarCard])
def similar_landings(slug: str) -> list[SimilarCard]:
    """Landings to show under this one, each with what it shares with it."""
    fresh, index = _library()
    if slug not in fresh:
        raise HTTPException(404, NOT_IN_LIBRARY)
    return [
        SimilarCard(card=_card(index, fresh[s.publication.slug]), reason=s.reason)
        for s in index.similar(slug)
        if s.publication.slug in fresh
    ]


@router.get("/{slug}/html")
def get_page(slug: str) -> Response:
    repo = get_publication_repository()
    publication = repo.get_published(slug)
    if publication is None:
        raise HTTPException(404, NOT_IN_LIBRARY)
    try:
        html = repo.read_html(publication)
    except FileNotFoundError:
        logger.error(
            "Published file missing for %s (project %s) v%d",
            publication.slug,
            publication.project_id,
            publication.version,
        )
        raise HTTPException(500, "Файл опубликованной страницы пропал с сервера. Опубликуйте лендинг заново.") from None
    return Response(
        html,
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Security-Policy": PAGE_CSP,
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-cache",
        },
    )
