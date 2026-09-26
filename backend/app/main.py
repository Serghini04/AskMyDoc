import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.errors import register_exception_handlers
from app.api.routers import chat, documents
from app.config import settings
from app.database import SessionLocal
from app.logging_config import configure_logging
from app.services import ingestion, qdrant

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"


def create_app(*, resume_ingestion: bool = True) -> FastAPI:
    """
    Build the application. `resume_ingestion=False` skips startup recovery,
    for tests that must not touch the real database.
    """

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if resume_ingestion:
            # Off the startup path: recovery calls the embedding API per document.
            threading.Thread(
                target=ingestion.resume_unfinished_documents,
                name="resume-ingestion",
                daemon=True,
            ).start()
        yield
        logger.info("Shutting down")

    app = FastAPI(
        title="AskMyDoc RAG API",
        description="Ingest documents and ask questions answered from their content.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(documents.router, prefix=API_PREFIX)
    app.include_router(chat.router, prefix=API_PREFIX)

    @app.get("/health", tags=["Health"])
    def liveness() -> dict[str, str]:
        """The process is up."""
        return {"status": "healthy"}

    @app.get("/health/ready", tags=["Health"])
    def readiness() -> JSONResponse:
        """Dependencies are reachable: 200 when Postgres and Qdrant answer, 503 otherwise."""
        checks = {"database": _check_database(), "vector_store": _check_vector_store()}
        ready = all(result == "ok" for result in checks.values())
        return JSONResponse(
            status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "ready" if ready else "unavailable", "checks": checks},
        )

    return app


def _check_database() -> str:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        logger.warning("Readiness: database unreachable", exc_info=True)
        return "unreachable"
    return "ok"


def _check_vector_store() -> str:
    try:
        qdrant.get_qdrant_service().client.get_collections()
    except Exception:
        logger.warning("Readiness: vector store unreachable", exc_info=True)
        return "unreachable"
    return "ok"


configure_logging(settings.LOG_LEVEL)
app = create_app()
