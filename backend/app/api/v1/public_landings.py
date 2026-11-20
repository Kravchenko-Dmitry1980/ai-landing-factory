"""Read-only access to one explicitly published snapshot, with no library metadata."""

import logging
import re

from fastapi import APIRouter, Response

from app.api.v1.library import PAGE_CSP
from app.core.dependencies import get_publication_repository

logger = logging.getLogger(__name__)
router = APIRouter()

PUBLIC_HEADERS = {
    "Content-Security-Policy": PAGE_CSP,
    "Cache-Control": "no-store",
    "X-Robots-Tag": "noindex, nofollow, noarchive",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}
_TOKEN = re.compile(r"[A-Za-z0-9_-]{43}\Z")
_NOT_FOUND = (
    '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
    '<title>Страница недоступна</title></head><body><h1>Страница недоступна</h1>'
    '<p>Проверьте ссылку или обратитесь к сотруднику, который её отправил.</p></body></html>'
)


def _response(html: str, status_code: int = 200) -> Response:
    return Response(html, status_code=status_code, media_type="text/html", headers=PUBLIC_HEADERS)


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
def no_public_directory() -> Response:
    return _response(_NOT_FOUND, 404)


@router.get("/{token}")
def public_landing(token: str) -> Response:
    if not _TOKEN.fullmatch(token):
        return _response(_NOT_FOUND, 404)
    repo = get_publication_repository()
    publication = repo.get_public(token)
    if publication is None:
        return _response(_NOT_FOUND, 404)
    try:
        html = repo.read_html(publication)
    except FileNotFoundError:
        logger.error("Public snapshot missing for project %s v%d", publication.project_id, publication.version)
        return _response(_NOT_FOUND, 404)
    return _response(html)


@router.get("/{invalid_path:path}", include_in_schema=False)
def no_public_subroutes(invalid_path: str) -> Response:
    return _response(_NOT_FOUND, 404)
