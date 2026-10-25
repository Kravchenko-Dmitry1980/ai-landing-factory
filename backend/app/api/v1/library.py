"""The library of published landings, for every signed-in account."""

import logging

from fastapi import APIRouter, HTTPException, Query, Response

from app.core.dependencies import get_publication_repository
from app.repositories.publication_repository import Publication
from app.schemas.publication import LibraryCard, LibraryPage
from app.services.library.search import query_terms, score, words

logger = logging.getLogger(__name__)
router = APIRouter()

# Published pages are documents without scripts. The sandbox gives them no origin even if
# someone opens this address directly, so a page can never act on behalf of the viewer.
PAGE_CSP = (
    "sandbox; default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
)


def _rank(publication: Publication, terms: list[str]) -> float:
    return score(
        terms,
        [
            (3.0, words(publication.title)),
            (2.5, words(" ".join([*publication.people, publication.customer, publication.lead]))),
            (1.5, words(publication.summary)),
            (1.0, publication.body_text.split()),
        ],
    )


@router.get("", response_model=LibraryPage)
def list_library(
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=100, ge=1, le=500),
) -> LibraryPage:
    """Newest first; with a query, the best matches first (title, then people and customer, then text)."""
    publications = get_publication_repository().list_published()
    total = len(publications)
    terms = query_terms(q)
    if terms:
        ranked = [(rank, p) for p in publications if (rank := _rank(p, terms)) > 0]
        ranked.sort(key=lambda item: (item[0], item[1].published_at), reverse=True)
        publications = [p for _, p in ranked]
    return LibraryPage(total=total, cards=[LibraryCard.of(p) for p in publications[:limit]])


@router.get("/{slug}", response_model=LibraryCard)
def get_card(slug: str) -> LibraryCard:
    publication = get_publication_repository().get_published(slug)
    if publication is None:
        raise HTTPException(404, "Такого лендинга в библиотеке нет: его сняли с публикации или адрес неверный.")
    return LibraryCard.of(publication)


@router.get("/{slug}/html")
def get_page(slug: str) -> Response:
    repo = get_publication_repository()
    publication = repo.get_published(slug)
    if publication is None:
        raise HTTPException(404, "Такого лендинга в библиотеке нет: его сняли с публикации или адрес неверный.")
    try:
        html = repo.read_html(publication)
    except FileNotFoundError:
        logger.error("Published file missing for %s v%d", publication.slug, publication.version)
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
