"""A finished demo video attached to one landing. Editors add it; publishing puts it on the link."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.dependencies import get_demo_repository, get_publication_repository
from app.repositories.demo_repository import DemoRepository
from app.schemas.demo import DemoInfo

logger = logging.getLogger(__name__)
router = APIRouter()

# The gateway accepts 60 MB for the whole request. Leave room for the form itself.
MAX_VIDEO_BYTES = 50 * 1024 * 1024
MAX_POSTER_BYTES = 2 * 1024 * 1024
_VIDEO_TOO_BIG = "Ролик больше 50 МБ. Сожмите его и добавьте снова."
_POSTER_TOO_BIG = "Обложка больше 2 МБ. Выберите картинку поменьше."
_NEED_VIDEO = "Нужен ролик в формате MP4."
_NEED_POSTER = "Обложка должна быть картинкой JPG, PNG или WEBP."
_NEED_DRAFT = "Сначала добавьте ролик."
_MISSING = "У этого лендинга пока нет демо."

_POSTER_MAGIC = (
    (b"\xff\xd8\xff", ".jpg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", ".png", "image/png"),
    (b"RIFF", ".webp", "image/webp"),
)


def _repo() -> DemoRepository:
    return get_demo_repository()


def _info(project_id: str) -> DemoInfo:
    publication = get_publication_repository().get_for_project(project_id)
    status = publication.status if publication else None
    version = publication.version if publication else None
    return _repo().info_for(project_id, status=status, version=version)


async def _read_limited(upload: UploadFile, limit: int, too_big: str) -> bytes:
    parts: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise HTTPException(413, too_big)
        parts.append(chunk)
    return b"".join(parts)


def _poster(data: bytes) -> tuple[bytes, str, str]:
    for magic, ext, media_type in _POSTER_MAGIC:
        if data.startswith(magic):
            if ext == ".webp" and (len(data) < 12 or data[8:12] != b"WEBP"):
                break
            return data, ext, media_type
    raise HTTPException(422, _NEED_POSTER)


def _file(path, media_type: str) -> FileResponse:
    return FileResponse(
        path,
        media_type=media_type,
        content_disposition_type="inline",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/{project_id}/demo", response_model=DemoInfo)
def get_demo(project_id: UUID) -> DemoInfo:
    return _info(str(project_id))


@router.put("/{project_id}/demo", response_model=DemoInfo)
async def put_demo(
    project_id: UUID,
    video: UploadFile = File(...),
    poster: UploadFile | None = File(None),
) -> DemoInfo:
    data = await _read_limited(video, MAX_VIDEO_BYTES, _VIDEO_TOO_BIG)
    if len(data) < 12 or data[4:8] != b"ftyp":
        raise HTTPException(422, _NEED_VIDEO)
    cover: tuple[bytes, str] | None = None
    if poster is not None and poster.filename:
        cover_bytes = await _read_limited(poster, MAX_POSTER_BYTES, _POSTER_TOO_BIG)
        cover_bytes, ext, _media = _poster(cover_bytes)
        cover = (cover_bytes, ext)
    key = str(project_id)
    _repo().save_draft(key, data, cover)
    return _info(key)


@router.put("/{project_id}/demo/poster", response_model=DemoInfo)
async def put_poster(project_id: UUID, poster: UploadFile = File(...)) -> DemoInfo:
    data = await _read_limited(poster, MAX_POSTER_BYTES, _POSTER_TOO_BIG)
    _bytes, ext, _media = _poster(data)
    key = str(project_id)
    try:
        _repo().save_poster(key, data, ext)
    except FileNotFoundError:
        raise HTTPException(409, _NEED_DRAFT) from None
    return _info(key)


@router.delete("/{project_id}/demo/poster", response_model=DemoInfo)
def delete_poster(project_id: UUID) -> DemoInfo:
    key = str(project_id)
    _repo().clear_poster(key)
    return _info(key)


@router.delete("/{project_id}/demo", response_model=DemoInfo)
def delete_demo(project_id: UUID) -> DemoInfo:
    key = str(project_id)
    _repo().clear_draft(key)
    return _info(key)


@router.get("/{project_id}/demo/video")
def draft_video(project_id: UUID) -> FileResponse:
    path = _repo().draft_video(str(project_id))
    if path is None:
        raise HTTPException(404, _MISSING)
    return _file(path, "video/mp4")


@router.get("/{project_id}/demo/poster")
def draft_poster(project_id: UUID) -> FileResponse:
    path = _repo().draft_poster(str(project_id))
    if path is None:
        raise HTTPException(404, _MISSING)
    ext = path.suffix
    media = next((item[2] for item in _POSTER_MAGIC if item[1] == ext), "application/octet-stream")
    return _file(path, media)
