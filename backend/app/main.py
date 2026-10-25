import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.dependencies import get_account_repository, get_database, get_publication_repository
from app.services.library.index import library_index
from app.product_mode import log_product_mode_warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _warm_library_index() -> None:
    """Build the search index in the background, so the first visitor after a restart does not wait."""
    try:
        repo = get_publication_repository()
        library_index(repo.list_published(with_texts=False), repo.list_published)
    except Exception:
        # Not fatal: the first library request builds it instead.
        logger.exception("Library index warm-up failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    for path in (
        settings.data_dir,
        settings.uploads_dir,
        settings.contracts_dir,
        settings.extractions_dir,
        settings.published_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
    logger.info("Data directories ready: %s", settings.data_dir)
    get_database()
    logger.info("Database ready: %s", settings.database_path)
    if get_account_repository().count_users() == 0:
        logger.warning(
            "No accounts yet: nobody can sign in. Create the first administrator with "
            "`python -m app.cli create-admin --login <login> --name \"<name>\"` in backend/."
        )
    threading.Thread(target=_warm_library_index, name="library-index-warmup", daemon=True).start()
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
