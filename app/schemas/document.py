from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str

class DocumentResponse(DocumentBase):
    id: UUID
    file_hash: str
    status: str
    created_at: datetime