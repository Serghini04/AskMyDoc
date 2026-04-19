from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List

from app.schemas.document import DocumentResponse

# 1. Child Schema defined FIRST
class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime

    # CRITICAL: Allows Pydantic to read SQLAlchemy model attributes
    model_config = ConfigDict(from_attributes=True)


# 2. Parent Schema defined SECOND
class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    # Use standard List with default empty lists
    messages: List[ChatMessageResponse] = []
    documents: List[DocumentResponse] = []
    
    model_config = ConfigDict(from_attributes=True)