from __future__ import annotations

import re
import logging
from uuid import UUID

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.document import Document
from app.repositories.chunk_repo import ChunkRepository
from app.services.embeddings import BaseEmbeddingService, BGEM3EmbeddingService
from app.services.qdrant import QdrantService

qdrant_service = QdrantService()

def extract_text(file_path: str, ext: str) -> str:
    """
    Routes the file to the correct parser based on its extension.
    """
    
    raw_text = ""
    
    if ext == ".pdf":
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            raw_text += page.get_text()
        doc.close()
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        raise ValueError(f"Unsupported extension for extraction: {ext}")
    return raw_text

def clean_text(text: str) -> str:
    """
    Sanitizes raw extracted text to prepare it for the LLM.
    """
    # Fix hyphenated words at the end of lines (e.g., "informa-\ntion" -> "information")
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    
    # Replace multiple newlines with a single space
    text = re.sub(r"\n+", " ", text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r"\s{2,}", " ", text)
    
    return text.strip()


def chunk_document_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Splits a massive string into smaller, overlapping chunks using industry standards.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        # It tries to split on double newlines (paragraphs), then single newlines, then spaces.
        separators=["\n\n", "\n", " ", ""] 
    )
    
    chunks = splitter.split_text(text)
    return chunks

def process_document(
    db: Session, 
    doc_id: UUID | str,
    file_path: str, 
    ext: str, 
    embedding_service: BaseEmbeddingService,
) -> int:
    """
    The master pipeline: Extracts, Cleans, Chunks, Embeds, and Saves.
    Notice how we INJECT the embedding_service here! 
    """
    raw_text = extract_text(file_path, ext)
    
    clean_str = clean_text(raw_text)
    
    chunks = chunk_document_text(clean_str, chunk_size=1000, chunk_overlap=200)
    
    saved_chunks = ChunkRepository.create_bulk(
        db=db,
        document_id=doc_id,
        chunks_data=chunks,
    )
    
    qdrant_payloads = []
        
    for chunk in saved_chunks:
        # Generate the 1024-dimensional BGE-M3 vector
        vector = embedding_service.embed_text(chunk.content)
        qdrant_payloads.append({
            "id": str(chunk.id),
            "vector": vector,
            "payload": {
                "document_id": str(doc_id),
                "chunk_index": chunk.chunk_index
            }
        })
    
    qdrant_service.upsert_points(qdrant_payloads)
        
    return len(chunks)

def process_document_background(
    doc_id: UUID | str,
    file_path: str,
    ext: str,
    embedding_service: BaseEmbeddingService | None = None,
):
    """
    This is the function we actually pass to FastAPI BackgroundTasks.
    It creates a completely fresh database session that won't close permaturely.
    """
    with SessionLocal() as db:
        try:
            if embedding_service is None:
                embedding_service = BGEM3EmbeddingService()

            print(f"Starting background processsing for document {doc_id} ...")
            chunks_created = process_document(db, doc_id, file_path, ext, embedding_service)
            
            # Update the Document status in the DB:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = "COMPLETED"
                db.commit()
            
            print(f"Successfully processed and embedded {chunks_created} chunks!")
        except Exception as e:
            logging.error(f"Failed to process document {doc_id}: {e}")
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = "FAILED"
            db.commit()