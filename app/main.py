from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI

from app.api.routers import documents

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lazy-load embedding models from dependencies to keep startup fast and reliable.
    app.state.embedding_service = None
    
    yield  # <-- This is where FastAPI actually boots up and accepts web traffic!
    
    print("Shutting down... Clearing AI models from VRAM.")
    # Free up the GPU memory when the server stops
    app.state.embedding_service = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

app = FastAPI(
    title="Enterprise RAG API",
    description="API for ingesting documents and querying them via LLMs.",
    lifespan=lifespan,
    version="1.0.0"
)

app.include_router(documents.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    """Load balancer health check endpoint."""
    return {"status": "healthy"}
