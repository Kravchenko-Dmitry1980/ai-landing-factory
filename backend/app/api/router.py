from fastapi import APIRouter, Depends

from app.api.v1 import (
    admin,
    auth,
    contracts,
    demos,
    domain,
    library,
    privacy,
    projects,
    public_landings,
    publications,
    showcase,
    showcases,
    uploads,
)
from app.core.auth import check_same_origin, current_user, require_admin, require_editor

# Public links return a single rendered snapshot; the library and studio still need a session.
api_router = APIRouter(dependencies=[Depends(check_same_origin)])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(public_landings.router, prefix="/public/landings", tags=["public landings"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
api_router.include_router(library.router, prefix="/library", tags=["library"], dependencies=[Depends(current_user)])

_studio = [Depends(require_editor)]
api_router.include_router(privacy.router, prefix="/projects", tags=["privacy"], dependencies=_studio)
api_router.include_router(projects.router, prefix="/projects", tags=["projects"], dependencies=_studio)
api_router.include_router(uploads.router, prefix="/projects", tags=["uploads"], dependencies=_studio)
api_router.include_router(contracts.router, prefix="/projects", tags=["contracts"], dependencies=_studio)
api_router.include_router(domain.router, prefix="/projects", tags=["domain"], dependencies=_studio)
api_router.include_router(publications.router, prefix="/projects", tags=["publications"], dependencies=_studio)
api_router.include_router(demos.router, prefix="/projects", tags=["demos"], dependencies=_studio)
api_router.include_router(showcase.router, prefix="/showcase", tags=["showcase"], dependencies=_studio)
api_router.include_router(showcases.router, prefix="/showcases", tags=["showcases"], dependencies=_studio)
