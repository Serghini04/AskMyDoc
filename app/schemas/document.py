from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str

class DocumentResponse(DocumentBase):
    id: UUID
    file_hash: str
    file_size_bytes: int
    status: str
    session_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)