"""
Rebuild the vector index with the configured embedding model.

Needed whenever EMBEDDING_MODEL / EMBEDDING_DIMENSIONS change: vectors from
different models aren't comparable, so every document is re-embedded.

    make reindex        (runs `python -m app.scripts.reindex` in the api container)
"""

import logging
from collections import Counter

from app.config import settings
from app.database import SessionLocal
from app.logging_config import configure_logging
from app.models.enums import DocumentStatus
from app.repositories.document_repo import DocumentRepository
from app.services.ingestion import resume_unfinished_documents
from app.services.qdrant import QdrantService

logger = logging.getLogger("app.scripts.reindex")


def main() -> None:
    configure_logging(settings.LOG_LEVEL)
    logger.info(
        "Reindexing with %s (%d dims)", settings.EMBEDDING_MODEL, settings.EMBEDDING_DIMENSIONS
    )

    QdrantService(check_dimensions=False).recreate_collection()

    # Queue everything, then reuse the startup-recovery path (idempotent,
    # handles missing files) to process documents one by one.
    with SessionLocal() as db:
        DocumentRepository(db).set_all_statuses(DocumentStatus.PENDING)
        db.commit()

    resume_unfinished_documents()

    with SessionLocal() as db:
        statuses = Counter(
            doc.status for doc in DocumentRepository(db).list_page(offset=0, limit=10_000)
        )
    logger.info("Reindex finished: %s", dict(statuses) or "no documents")


if __name__ == "__main__":
    main()
