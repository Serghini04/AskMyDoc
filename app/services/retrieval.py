from uuid import UUID
from sqlalchemy.orm import Session
from app.services.embeddings import BaseEmbeddingService
from app.services.qdrant import QdrantService, get_qdrant_service
from app.models.document import Chunk

class RetrievalService:
    @staticmethod
    def get_context_for_query(
        db: Session, 
        session_id: UUID, 
        query: str, 
        embedding_service: BaseEmbeddingService,
        limit: int = 5
    ) -> str:
        """
        The 3-Step Retrieval Pipeline (Pointer Method):
        1. Embed the text.
        2. Search Qdrant for chunk IDs.
        3. Fetch actual text from Postgres.
        """
        
        query_vector = embedding_service.embed_text(query)
        
        # search Qdrant (Filtered by session_id)
        qdrant = get_qdrant_service()
        search_results = qdrant.search_similar_chunks(
            query_vector=query_vector,
            session_id=str(session_id),
            limit=limit
        )
        
        if not search_results:
            return "No relevant documents found for this session."

        chunk_ids = [result.id for result in search_results]
        
        chunks = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
        
        chunk_map = {str(chunk.id): chunk.content for chunk in chunks}
        
        ordered_context = []
        for result in search_results:
            content = chunk_map.get(str(result.id))
            if content:
                ordered_context.append(content)

        final_context_string = "\n\n---\n\n".join(ordered_context)
        
        return final_context_string