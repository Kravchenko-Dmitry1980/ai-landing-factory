"""Read-only access to one explicitly published snapshot, with no library metadata."""

import logging
import re

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse

from app.api.v1.library import PAGE_CSP
from app.core.dependencies import get_demo_repository, get_publication_repository
from app.schemas.demo import PublicDemoMeta

logger = logging.getLogger(__name__)
router = APIRouter()

PUBLIC_HEADERS = {
    "Content-Security-Policy": PAGE_CSP,
    "Cache-Control": "no-store",
    "X-Robots-Tag": "noindex, nofollow, noarchive",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}
_OPAQUE = re.compile(r"[A-Za-z0-9_-]{43}\Z")
_READABLE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
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


def _acceptable(token: str) -> bool:
    return bool(_OPAQUE.fullmatch(token) or (len(token) <= 80 and _READABLE.fullmatch(token)))


def _published(token: str):
    if not _acceptable(token):
        return None
    return get_publication_repository().get_public(token)


@router.get("/{token}/meta", response_model=PublicDemoMeta)
def public_demo_meta(token: str) -> PublicDemoMeta:
    publication = _published(token)
    if publication is None:
        raise HTTPException(404, "Страница недоступна")
    demos = get_demo_repository()
    video = demos.published_video(publication.project_id, publication.version)
    poster = demos.published_poster(publication.project_id, publication.version)
    return PublicDemoMeta(demo=video is not None, poster=poster is not None, title=publication.title)


def _public_file(path, media_type: str) -> FileResponse:
    return FileResponse(
        path,
        media_type=media_type,
        content_disposition_type="inline",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "X-Robots-Tag": "noindex, nofollow, noarchive",
        },
    )


@router.get("/{token}/demo")
def public_demo_video(token: str) -> FileResponse:
    publication = _published(token)
    path = (
        get_demo_repository().published_video(publication.project_id, publication.version)
        if publication is not None
        else None
    )
    if path is None:
        raise HTTPException(404, "Страница недоступна")
    return _public_file(path, "video/mp4")


@router.get("/{token}/poster")
def public_demo_poster(token: str) -> FileResponse:
    publication = _published(token)
    path = (
        get_demo_repository().published_poster(publication.project_id, publication.version)
        if publication is not None
        else None
    )
    if path is None:
        raise HTTPException(404, "Страница недоступна")
    media = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(path.suffix.lstrip("."), "")
    if not media:
        raise HTTPException(404, "Страница недоступна")
    return _public_file(path, media)


@router.get("/{token}")
def public_landing(token: str) -> Response:
    if not _acceptable(token):
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
