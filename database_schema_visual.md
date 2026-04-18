# Database Schema Visual

This document visualizes the current relational schema defined by Alembic migration `92c0a144db29` and SQLAlchemy models.

## ER Diagram

```mermaid
erDiagram
    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : has
    CHAT_SESSIONS ||--o{ DOCUMENTS : owns
    DOCUMENTS ||--o{ CHUNKS : contains

    CHAT_SESSIONS {
        uuid id PK
        varchar_255 title
        timestamptz created_at
    }

    CHAT_MESSAGES {
        uuid id PK
        uuid session_id FK
        varchar_50 role
        text content
        timestamptz created_at
    }

    DOCUMENTS {
        uuid id PK
        uuid session_id FK
        varchar_255 filename
        varchar_64 file_hash UK
        varchar_50 status
        timestamptz created_at
        timestamptz updated_at
    }

    CHUNKS {
        uuid id PK
        uuid document_id FK
        int chunk_index
        text content
        uuid vector_id
        timestamptz created_at
    }
```

## Constraints and Indexes

- Primary keys: `chat_sessions.id`, `chat_messages.id`, `documents.id`, `chunks.id`
- Foreign keys:
  - `chat_messages.session_id -> chat_sessions.id` (ON DELETE CASCADE)
  - `documents.session_id -> chat_sessions.id` (ON DELETE CASCADE)
  - `chunks.document_id -> documents.id` (ON DELETE CASCADE)
- Unique constraint / index:
  - `documents.file_hash` is unique and indexed (`ix_documents_file_hash`)
- Secondary indexes:
  - `chunks.document_id` (`idx_chunk_document_id`)
  - `chunks.vector_id` (`ix_chunks_vector_id`)

## Data Lifecycle (Cascade Behavior)

- Deleting a chat session removes its messages and documents.
- Deleting a document removes all related chunks.
- This keeps orphan records out of the transactional database.
