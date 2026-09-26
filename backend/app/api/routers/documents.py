from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.dependencies import DocumentServiceDep
from app.schemas.document import DocumentResponse
from app.services import ingestion

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    service: DocumentServiceDep,
    background_tasks: BackgroundTasks,
    session_id: Annotated[UUID, Form()],
    file: Annotated[UploadFile, File()],
):
    """Upload a PDF/TXT to a session. Returns at once (PENDING); indexing runs in the background."""
    document = service.upload(session_id, file.filename or "", file.file)
    background_tasks.add_task(ingestion.ingest_document, document.id)
    return document


@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    service: DocumentServiceDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    return service.list_documents(offset=skip, limit=limit)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: UUID, service: DocumentServiceDep):
    """Fetch one document — the frontend polls this for ingestion status."""
    return service.get(document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: UUID, service: DocumentServiceDep) -> None:
    """Delete a document with its chunks, vectors, and file."""
    service.delete(document_id)


@router.get("/{document_id}/download", response_class=FileResponse)
def download_document(document_id: UUID, service: DocumentServiceDep) -> FileResponse:
    download = service.download(document_id)
    return FileResponse(download.path, media_type=download.media_type, filename=download.filename)
