from enum import StrEnum


class DocumentStatus(StrEnum):
    """Ingestion lifecycle: PENDING -> PROCESSING -> COMPLETED | FAILED."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


IN_PROGRESS_STATUSES = (DocumentStatus.PENDING, DocumentStatus.PROCESSING)


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
