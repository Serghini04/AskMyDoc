import uuid
from typing import List
from sqlalchemy.orm import Session

from app.models.document import Chunk

class ChunkRepository:
    
    @staticmethod
    def create_bulk(db: Session, document_id: str, chunks_data: List[str]) -> List[Chunk]:
        """
        Takes a list of string chunks, generates UUIDs for them,
        and does a lightning-fast bulk insert into Postgress
        """
        
        db_chunks = []
        
        for index, text in enumerate(chunks_data):
            new_chunk = Chunk(
                id=uuid.uuid4(),
                document_id=document_id,
                content=text,
                chunk_index=index    
            )
            db_chunks.append(new_chunk)

        db.add_all(db_chunks)
        
        try:
            db.commit()
            return db_chunks
        except Exception as e:
            db.rollback()
            raise e            