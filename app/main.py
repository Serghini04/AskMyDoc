import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import documents, chat

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="AskMyDoc RAG API",
    description="API for ingesting documents and querying them via LLMs.",
    lifespan=lifespan,
    version="1.0.0",
)

app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
