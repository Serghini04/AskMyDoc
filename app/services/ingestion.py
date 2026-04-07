import os
import re
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .embedding_service import BGEM3EmbeddingService

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
        with open(file_path, "r",encoding="uft-8") as f :
            raw_text = f.read()
    else:
        raise ValueError(f"Usupported extension for extraction: {ext}")
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

embedding_service = BGEM3EmbeddingService()

def process_document(
    db: Session, 
    doc_id: UUID, 
    file_path: str, 
    ext: str, 
    embedding_service=embedding_service
):
    """
    The master pipeline: Extracts, Cleans, Chunks, Embeds, and Saves.
    Notice how we INJECT the embedding_service here! 
    """
    raw_text = extract_text(file_path, ext)
    
    clean_str = clean_text(raw_text)
    
    chunks = chunk_document_text(clean_str, chunk_size=1000, chunk_overlap=200)
    
    for position, chunk_text in enumerate(chunks):
        vector = embedding_service.embed_text(chunk_text)
        
        # B. Save the text metadata to PostgreSQL (We will write this repo next)
        # chunk_record = ChunkRepository.create(...)
        
        # C. Save the Vector to Qdrant (We will write this connection next)
        # qdrant_client.upsert(...)
        
    return len(chunks)