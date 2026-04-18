import os
import shutil
import hashlib
import mimetypes
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.document import DocumentResponse
from app.repositories.document_repo import DocumentRepository
from app.models.document import Document
from app.models.chat import ChatSession
from app.services.ingestion import process_document_background

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    
    ALLOWED_EXTENSIONS = {".pdf", ".txt"}
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {ext}. Only PDF and TXT are allowed."
        )

    file_content = await file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    existing_doc = DocumentRepository.get_by_hash(db, file_hash)
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"File already exists with ID: {existing_doc.id}"
        )
    
    try:
        new_doc = DocumentRepository.create(
            db=db,
            filename=file.filename,
            file_hash=file_hash,
            session_id=session_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    safe_filename = f"{new_doc.id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    await file.seek(0) 
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer) 
    
    background_tasks.add_task(
        process_document_background,
        doc_id=new_doc.id,
        file_path=file_path,
        ext=ext,
    )
    
    return new_doc


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0, 
    limit: int = 50, 
    db: Session = Depends(get_db)
):
    """Fetch a paginated list of all uploaded documents."""
    docs = db.query(Document).offset(skip).limit(limit).all()
    return docs


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: UUID, 
    db: Session = Depends(get_db)
):
    """Fetch exactly one document by its UUID."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document not found"
        )
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: UUID, 
    db: Session = Depends(get_db)
):
    """Hard delete a document and its physical file."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document not found"
        )
    
    _, ext = os.path.splitext(doc.filename)
    file_path = os.path.join(UPLOAD_DIR, f"{doc.id}{ext.lower()}")
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 2. Delete the database record
    # TODO: Later, we must also tell Qdrant to delete the vectors associated with this doc!
    db.delete(doc)
    db.commit()
    return None


@router.get("/{doc_id}/download", response_class=FileResponse)
async def download_document(
    doc_id: UUID, 
    db: Session = Depends(get_db)
):
    """Serve the physical PDF or TXT file to the user."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document not found"
        )
    
    _, ext = os.path.splitext(doc.filename)
    file_path = os.path.join(UPLOAD_DIR, f"{doc.id}{ext}")
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Physical file is missing from the server"
        )
    
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = "application/octet-stream"
        
    return FileResponse(
        path=file_path, 
        media_type=content_type, 
        filename=doc.filename 
    )