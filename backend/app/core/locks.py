"""Per-project locks and the optimistic version check for edits of a landing.

The locks hold inside one backend process only, so the backend runs as a single uvicorn worker.
"""

import asyncio
from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException

from app.core.dependencies import get_contract_repository

_project_locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

STALE_VERSION = (
    "Этот лендинг только что изменил другой сотрудник, и ваши последние правки не сохранились. "
    "Обновите страницу, чтобы увидеть свежую версию."
)


def project_lock(project_id: UUID | str) -> asyncio.Lock:
    return _project_locks[str(project_id)]


async def check_expected_version(project_id: UUID, expected_version: int | None) -> None:
    """
    Refuses a change made on top of a contract version that is no longer current (409).

    Call under project_lock(project_id), so nothing saves between this check and the write.
    Requests without a version (the old developer screens) skip the check.
    """
    if expected_version is None:
        return
    current = await get_contract_repository().get_contract(project_id)
    if current is None:
        raise HTTPException(404, "LandingContract not found")
    if current.version != expected_version:
        raise HTTPException(409, STALE_VERSION)
