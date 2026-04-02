## **🚀 VERSION 1: CORE RAG (2-3 Weeks)**

### **Goal: Working system that IMPRESSES!**

```
FEATURES TO BUILD:
──────────────────
✅ Upload PDF/TXT documents
✅ Extract and chunk text
✅ Generate embeddings
✅ Store in vector DB
✅ Search similar chunks
✅ Generate AI answer
✅ Simple API endpoints

NOT INCLUDED YET:
─────────────────
❌ Caching (V2)
❌ Background jobs (V2)
❌ Multi-tenancy (V3)
❌ Dashboard (V3)
```

---

### **📐 ARCHITECTURE (V1 - Simple!):**

```
┌─────────────┐
│  Client     │
│  (Postman)  │
└──────┬──────┘
       │
┌──────▼────────────────────┐
│  FastAPI                  │
│  ─────────────            │
│  POST /upload             │
│  POST /query              │
│  GET  /documents          │
└──────┬────────────────────┘
       │
   ┌───┴─────────┐
   ▼             ▼
┌────────────┐ ┌──────────────┐
│PostgreSQL  │ │   Qdrant     │
│            │ │              │
│documents   │ │  vectors +   │
│metadata    │ │  chunks      │
└────────────┘ └──────────────┘
```

---

### **🗂️ DATABASE SCHEMA (V1):**

```sql
-- PostgreSQL schema

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    upload_date TIMESTAMP DEFAULT NOW(),
    chunk_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'processing'
);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    vector_id VARCHAR(255), -- Qdrant point ID
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_doc_id ON chunks(document_id);
CREATE INDEX idx_vector_id ON chunks(vector_id);
```

---

### **📁 PROJECT STRUCTURE (V1):**

```
rag-system/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── models.py            # Pydantic models
│   ├── database.py          # PostgreSQL connection
│   ├── dependencies.py      # FastAPI dependencies
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── documents.py     # Upload, list endpoints
│   │   └── query.py         # Search endpoint
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chunking.py      # Text splitting
│   │   ├── embeddings.py    # OpenAI embeddings
│   │   ├── vector_store.py  # Qdrant operations
│   │   └── llm.py           # GPT-4 generation
│   │
│   └── utils/
│       ├── __init__.py
│       └── file_parser.py   # PDF/TXT extraction
│
├── tests/
│   ├── __init__.py
│   ├── test_chunking.py
│   └── test_api.py
│
├── alembic/                 # Database migrations
│   └── versions/
│
├── requirements.txt
├── .env
├── docker-compose.yml       # PostgreSQL + Qdrant
└── README.md
```

---

### **🔧 IMPLEMENTATION BREAKDOWN (V1):**

```
WEEK 1: SETUP & UPLOAD (15-20 hours)
─────────────────────────────────────

Day 1-2 (6 hours): Project Setup
──────────────────────────────────
✅ Create project structure
✅ Set up FastAPI boilerplate
✅ Docker Compose (PostgreSQL + Qdrant)
✅ Environment variables (.env)
✅ Database models (SQLAlchemy)

Tasks:
1. mkdir rag-system && cd rag-system
2. python -m venv venv && source venv/bin/activate
3. Create docker-compose.yml:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: rag_db
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: rag_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  qdrant_data:
```

1. pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary qdrant-client openai python-multipart pypdf2
2. Create database schema
3. Test connection to both DBs

```
Day 3-4 (8 hours): File Upload
───────────────────────────────
✅ PDF/TXT parser
✅ Upload endpoint
✅ Save to PostgreSQL
✅ Basic error handling

Code:
```python
# app/utils/file_parser.py
from pypdf2 import PdfReader
from typing import Tuple

def extract_text(file_path: str, file_type: str) -> Tuple[str, int]:
    """Extract text from PDF or TXT file."""
    if file_type == 'pdf':
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text, len(text)

    elif file_type == 'txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return text, len(text)

    else:
        raise ValueError(f"Unsupported file type: {file_type}")

# app/routers/documents.py
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document
from app.utils.file_parser import extract_text
import shutil
from pathlib import Path

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Save file
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text
    file_type = file.filename.split('.')[-1]
    text, char_count = extract_text(str(file_path), file_type)

    # Save to DB
    doc = Document(
        filename=file.filename,
        file_type=file_type,
        file_size=file_path.stat().st_size,
        status='uploaded'
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "char_count": char_count,
        "status": "uploaded"
    }
```

Day 5-7 (6 hours): Testing & Debugging
───────────────────────────────────────
✅ Test with different PDFs
✅ Handle edge cases (empty files, corrupted PDFs)
✅ Write unit tests
✅ Fix bugs

DELIVERABLE WEEK 1: ✅ File upload working!

```

---
```

WEEK 2: CHUNKING & EMBEDDINGS (15-20 hours)
────────────────────────────────────────────

Day 1-2 (8 hours): Chunking Logic
──────────────────────────────────
✅ Implement text splitting
✅ Save chunks to PostgreSQL
✅ Link chunks to documents

Code:

```python
# app/services/chunking.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List

class ChunkingService:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\\n\\n", "\\n", ". ", " ", ""]
        )

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        return self.splitter.split_text(text)

# In your upload endpoint, add:
from app.services.chunking import ChunkingService
from app.models import Chunk

chunker = ChunkingService()
chunks = chunker.chunk_text(text)

# Save chunks to DB
for idx, chunk_text in enumerate(chunks):
    chunk = Chunk(
        document_id=doc.id,
        chunk_index=idx,
        content=chunk_text,
        char_count=len(chunk_text)
    )
    db.add(chunk)

doc.chunk_count = len(chunks)
doc.status = 'chunked'
db.commit()
```

Day 3-4 (8 hours): Embeddings & Vector Store
─────────────────────────────────────────────
✅ Generate embeddings (OpenAI)
✅ Store in Qdrant
✅ Link vector IDs to chunks

Code:

```python
# app/services/embeddings.py
from openai import OpenAI
from typing import List

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI()
        self.model = "text-embedding-3-small"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [item.embedding for item in response.data]

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        return self.embed_texts([text])[0]

# app/services/vector_store.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List
import uuid

class VectorStoreService:
    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection_name = "documents"
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if doesn't exist."""
        collections = self.client.get_collections().collections
        if self.collection_name not in [c.name for c in collections]:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # text-embedding-3-small dimension
                    distance=Distance.COSINE
                )
            )

    def add_vectors(
        self,
        vectors: List[List[float]],
        metadatas: List[dict]
    ) -> List[str]:
        """Add vectors to Qdrant."""
        points = []
        ids = []

        for vector, metadata in zip(vectors, metadatas):
            point_id = str(uuid.uuid4())
            ids.append(point_id)

            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload=metadata
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        return ids

    def search(
        self,
        query_vector: List[float],
        limit: int = 5
    ) -> List[dict]:
        """Search for similar vectors."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
        ]

# Update upload endpoint:
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStoreService

embedder = EmbeddingService()
vector_store = VectorStoreService()

# After saving chunks to PostgreSQL:
chunk_texts = [chunk.content for chunk in db.query(Chunk).filter(Chunk.document_id == doc.id).all()]
embeddings = embedder.embed_texts(chunk_texts)

# Prepare metadata
metadatas = [
    {
        "document_id": str(doc.id),
        "chunk_id": str(chunk.id),
        "chunk_index": chunk.chunk_index,
        "content": chunk.content
    }
    for chunk in chunks_from_db
]

# Store in Qdrant
vector_ids = vector_store.add_vectors(embeddings, metadatas)

# Update chunks with vector IDs
for chunk, vector_id in zip(chunks_from_db, vector_ids):
    chunk.vector_id = vector_id

doc.status = 'indexed'
db.commit()
```

Day 5-7 (4 hours): Testing
──────────────────────────
✅ Test embedding generation
✅ Test vector storage
✅ Test retrieval
✅ Measure time (should be <5s for 1 doc)

DELIVERABLE WEEK 2: ✅ Documents indexed in vector DB!

```

---
```

WEEK 3: QUERY & GENERATION (15-20 hours)
─────────────────────────────────────────

Day 1-2 (8 hours): Search Endpoint
───────────────────────────────────
✅ Query endpoint
✅ Embed query
✅ Search Qdrant
✅ Return relevant chunks

Code:

```python
# app/routers/query.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/query", tags=["query"])

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

class QueryResponse(BaseModel):
    question: str
    results: List[dict]

@router.post("/search", response_model=QueryResponse)
async def search_documents(request: QueryRequest):
    embedder = EmbeddingService()
    vector_store = VectorStoreService()

    # Embed question
    query_embedding = embedder.embed_text(request.question)

    # Search
    results = vector_store.search(
        query_vector=query_embedding,
        limit=request.top_k
    )

    return QueryResponse(
        question=request.question,
        results=results
    )
```

Day 3-5 (10 hours): LLM Generation
───────────────────────────────────
✅ Integrate GPT-4
✅ Build prompt with context
✅ Stream response (optional)
✅ Return answer

Code:

```python
# app/services/llm.py
from openai import OpenAI
from typing import List

class LLMService:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-4"

    def generate_answer(
        self,
        question: str,
        context_chunks: List[str]
    ) -> str:
        """Generate answer using retrieved context."""

        # Build context
        context = "\\n\\n".join([
            f"[{i+1}] {chunk}"
            for i, chunk in enumerate(context_chunks)
        ])

        # Build prompt
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.

Context:
{context}

Question: {question}

Instructions:
- Answer the question using ONLY the information from the context
- If the context doesn't contain the answer, say "I don't have enough information to answer this question"
- Be concise and accurate
- Cite the context chunk number [1], [2], etc. when relevant

Answer:"""

        # Generate
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content

# Update query endpoint:
from app.services.llm import LLMService

@router.post("/ask")
async def ask_question(request: QueryRequest):
    embedder = EmbeddingService()
    vector_store = VectorStoreService()
    llm = LLMService()

    # Search
    query_embedding = embedder.embed_text(request.question)
    results = vector_store.search(query_embedding, limit=request.top_k)

    # Extract chunks
    context_chunks = [r["payload"]["content"] for r in results]

    # Generate answer
    answer = llm.generate_answer(request.question, context_chunks)

    return {
        "question": request.question,
        "answer": answer,
        "sources": [
            {
                "chunk": r["payload"]["content"][:200] + "...",
                "score": r["score"],
                "document_id": r["payload"]["document_id"]
            }
            for r in results
        ]
    }
```

Day 6-7 (4 hours): Polish & Test
─────────────────────────────────
✅ Test full flow
✅ Handle errors
✅ Add logging
✅ Write README

DELIVERABLE WEEK 3: ✅ WORKING RAG SYSTEM!

```

---

### **🎯 V1 COMPLETION CHECKLIST:**
```

MUST HAVE:
──────────
✅ Upload PDF/TXT documents
✅ View uploaded documents (GET /documents)
✅ Ask questions (POST /query/ask)
✅ Get AI answers with sources
✅ Error handling (try bad files, bad questions)
✅ Basic logging
✅ README with setup instructions
✅ Docker Compose for dependencies

NICE TO HAVE (if time):
───────────────────────
✅ Delete documents endpoint
✅ Progress indicator during upload
✅ Response time tracking
✅ Basic tests (pytest)

DEMO READY:
───────────
✅ Can upload a PDF
✅ Can ask 3-5 questions and get good answers
✅ Response time < 3 seconds
✅ No crashes!

```

---

## **📈 WHAT YOU LEARN IN V1:**
```

SKILLS GAINED:
──────────────
✅ FastAPI (routing, dependencies, file handling)
✅ PostgreSQL (schema design, SQLAlchemy)
✅ Vector databases (Qdrant basics)
✅ Embeddings (OpenAI API)
✅ LLM integration (GPT-4 prompting)
✅ Text processing (chunking strategies)
✅ Docker (multi-container setup)
✅ Async Python (basic patterns)
✅ API design (RESTful endpoints)

CONCEPTS UNDERSTOOD:
────────────────────
✅ What is RAG (Retrieval-Augmented Generation)
✅ How embeddings work
✅ Semantic search vs keyword search
✅ Chunking tradeoffs (size vs context)
✅ Prompt engineering (context formatting)
✅ System integration (multiple services)

DELIVERABLE:
────────────
✅ Working RAG system (impressive!)
✅ Clean, documented code
✅ Portfolio piece (put on GitHub!)
✅ Can demo to potential clients!

VALUE:
──────
You can now build custom RAG systems for clients!
Potential earnings: 8,000-15,000 MAD per project! 💰

```

---

## **🚀 VERSION 2: PRODUCTION RAG (4-6 Weeks)**

### **What Changes: Performance + Reliability!**
```

NEW FEATURES:
─────────────
✅ Redis caching (query results)
✅ Background processing (Celery)
✅ Hybrid search (vector + full-text)
✅ Advanced chunking (semantic)
✅ Rate limiting
✅ Monitoring (basic metrics)
✅ Better error handling
✅ API documentation (Swagger)

ARCHITECTURE UPGRADE:
─────────────────────

┌─────────────┐
│  Client     │
└──────┬──────┘
│
┌──────▼────────────────────┐
│  FastAPI + Rate Limiter   │
└──────┬────────────────────┘
│
┌───┴──────────┐
▼              ▼
┌─────────┐   ┌──────────┐
│ Redis   │   │ Celery   │ ← NEW!
│ Cache   │   │ Workers  │
└─────────┘   └──────────┘
│              │
└────┬─────────┘
▼
┌────────────────┐
│  PostgreSQL    │
│  + pgvector    │ ← NEW! (hybrid search)
└────────────────┘
│
┌────▼─────┐
│  Qdrant  │
└──────────┘

```

I can continue with detailed V2 and V3 breakdowns. Should I continue, or do you want to discuss V1 implementation details first?

This gives you:
- ✅ Clear V1 path (achievable in 3 weeks!)
- ✅ Specific code examples
- ✅ Week-by-week breakdown
- ✅ What you learn at each stage
- ✅ Testing criteria

**Should I continue with V2 and V3 detailed plans?** 🚀
```