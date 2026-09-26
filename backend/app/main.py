import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routers import documents, chat
from app.services.ingestion import resume_unfinished_documents

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Off the startup path: recovery may load the embedding model and take a while.
    threading.Thread(target=resume_unfinished_documents, name="resume-ingestion", daemon=True).start()
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="AskMyDoc RAG API",
    description="API for ingesting documents and querying them via LLMs.",
    lifespan=lifespan,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
