from fastapi import FastAPI

from app.api.routers import documents
from app.services.embeddings import BGEM3EmbeddingService

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing global AI models...")
    app.state.embedding_service = BGEM3EmbeddingService()
    
    yield  # <-- This is where FastAPI actually boots up and accepts web traffic!
    
    print("Shutting down... Clearing AI models from VRAM.")
    # Free up the GPU memory when the server stops
    app.state.embedding_service = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

app = FastAPI(
    title="Enterprise RAG API",
    description="API for ingesting documents and querying them via LLMs.",
    lifespan=lifespan
    version="1.0.0"
)

app.include_router(documents.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    """Load balancer health check endpoint."""
    return {"status": "healthy"}
