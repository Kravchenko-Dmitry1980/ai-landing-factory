from fastapi import APIRouter

from app.api.v1 import contracts, domain, privacy, projects, showcase, uploads

api_router = APIRouter()
api_router.include_router(privacy.router, prefix="/projects", tags=["privacy"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(uploads.router, prefix="/projects", tags=["uploads"])
api_router.include_router(contracts.router, prefix="/projects", tags=["contracts"])
api_router.include_router(domain.router, prefix="/projects", tags=["domain"])
api_router.include_router(showcase.router, prefix="/showcase", tags=["showcase"])
