"""Publishing a project's landing to the library (editors; mounted under /projects)."""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_editor
from app.core.dependencies import get_contract_repository, get_demo_repository, get_publication_repository
from app.core.locks import project_lock
from app.repositories.account_repository import User
from app.schemas.publication import PublicationInfo, PublishRequest
from app.services.library.metadata import publication_meta

logger = logging.getLogger(__name__)
router = APIRouter()


def check_rendered_page(project_id: UUID, html: str) -> None:
    """
    The renderer emits a complete page without scripts. Anything else did not come from it;
    the library also serves pages under a CSP sandbox, so this is the first of two locks.
    """
    if not html.lstrip()[:15].lower().startswith("<!doctype html"):
        reason = "no doctype"
    elif "<script" in html.lower():
        reason = "contains <script"
    else:
        return
    logger.warning("Refused to publish %s: the page %s", project_id, reason)
    raise HTTPException(422, "Страница собрана неправильно, публикация отменена. Сообщите разработчику.")


@router.get("/{project_id}/publication", response_model=PublicationInfo | None)
def get_publication(project_id: UUID) -> PublicationInfo | None:
    publication = get_publication_repository().get_for_project(str(project_id))
    return PublicationInfo.of(publication) if publication else None


@router.post("/{project_id}/publication", response_model=PublicationInfo)
async def publish(project_id: UUID, body: PublishRequest, user: User = Depends(require_editor)) -> PublicationInfo:
    check_rendered_page(project_id, body.html)
    async with project_lock(project_id):
        contract = await get_contract_repository().get_contract(project_id)
        if contract is None:
            raise HTTPException(404, "Лендинг не найден или материалы ещё не загружены.")
        if contract.version != body.contract_version:
            raise HTTPException(409, "Лендинг изменился, пока собиралась страница. Опубликуйте ещё раз.")
        publication = await asyncio.to_thread(
            get_publication_repository().publish,
            str(project_id),
            html=body.html,
            theme=body.theme,
            contract_version=contract.version,
            meta=publication_meta(contract, body.summary),
            user_id=user.id,
        )
    try:
        await asyncio.to_thread(get_demo_repository().snapshot, str(project_id), publication.version)
    except Exception:
        logger.exception("Demo was not attached to %s v%d", project_id, publication.version)
        raise HTTPException(
            500,
            "Страница опубликована, но демо не удалось приложить. Нажмите «Обновить в библиотеке» ещё раз.",
        ) from None
    logger.info("Published %s as /p/%s v%d by %s", project_id, publication.slug, publication.version, user.login)
    return PublicationInfo.of(publication)


@router.delete("/{project_id}/publication", response_model=PublicationInfo)
def withdraw(project_id: UUID, user: User = Depends(require_editor)) -> PublicationInfo:
    publication = get_publication_repository().withdraw(str(project_id))
    if publication is None:
        raise HTTPException(404, "Этот лендинг ещё не публиковали.")
    logger.info("Withdrew %s (/p/%s) by %s", project_id, publication.slug, user.login)
    return PublicationInfo.of(publication)
