from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import List

from app.schemas.document import DocumentResponse


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)

    model_config = ConfigDict(str_strip_whitespace=True)

class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime

    # CRITICAL: Allows Pydantic to read SQLAlchemy model attributes
    model_config = ConfigDict(from_attributes=True)


class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    messages: List[ChatMessageResponse] = Field(default_factory=list)
    documents: List[DocumentResponse] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)