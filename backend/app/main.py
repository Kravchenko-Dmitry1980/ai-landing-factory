import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.product_mode import log_product_mode_warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for path in (
        settings.data_dir,
        settings.uploads_dir,
        settings.contracts_dir,
        settings.extractions_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
    logger.info("Data directories ready: %s", settings.data_dir)
    logger.info("CORS origins: %s", settings.cors_origins)
    logger.info("Product mode: %s", settings.normalized_product_mode)
    log_product_mode_warnings(settings)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0-mvp",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
