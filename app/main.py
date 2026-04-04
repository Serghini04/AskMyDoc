from fastapi import FastAPI

from app.api.routers import documents

app = FastAPI(
    title="Enterprise RAG API",
    description="API for ingesting documents and querying them via LLMs.",
    version="1.0.0"
)

app.include_router(documents.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    """Load balancer health check endpoint."""
    return {"status": "healthy"}
