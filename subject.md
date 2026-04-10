# AskMyDoc — AI Document Intelligence Platform

> Upload any document. Ask anything about it. Get instant, sourced answers powered by AI.

---

## The Product

AskMyDoc is a production-ready SaaS platform for intelligent document querying. Users upload documents and interact with them through natural language — getting accurate, source-grounded answers in under 500ms.

**Target users:**

- Lawyers reviewing contracts and legal filings
- Accountants querying invoices and financial reports
- Students studying from course PDFs
- Clinics managing patient records and lab results

---

## The Challenge

Build a distributed document intelligence platform that:

- Handles 1,000+ concurrent users
- Processes 100GB+ of documents
- Responds in under 500ms
- Isolates data per tenant (multi-tenancy)
- Supports hybrid search (vector + full-text)
- Optimizes cost at scale

---

## System Architecture

```
┌──────────────────────────────┐
│         AskMyDoc Users       │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  API Gateway (FastAPI + JWT) │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│      RAG Orchestrator        │
│  → embed query               │
│  → check cache               │
│  → retrieve + rerank         │
│  → generate answer           │
└───────┬──────────────┬───────┘
        ▼              ▼
┌──────────────┐  ┌────────────────┐
│ Redis Cache  │  │ Qdrant         │
│              │  │ (Vector Store) │
└──────────────┘  └───────┬────────┘
                          │
                 ┌────────▼────────┐
                 │   PostgreSQL    │
                 │                 │
                 │  metadata       │
                 │  conversations  │
                 │  full-text idx  │
                 └─────────────────┘
```

---

## Core Pipeline

```
Ingestion:  Upload → Parse → Chunk → Embed → Store
Query:      Question → Embed → Search → Rerank → LLM → Answer + Sources
```

---

## Technical Challenges

### 1. Document Processing

- Semantic chunking (not naive token splitting)
- Structure-aware parsing (headers, tables, sections)
- Async ingestion via Celery workers
- Real-time progress tracking via WebSockets

### 2. Hybrid Search

- Vector similarity via Qdrant
- BM25 full-text via PostgreSQL `tsvector`
- Score fusion using the RRF algorithm
- Reranking via cross-encoder model

### 3. Conversation System

- Multi-turn chat with conversation memory
- Source citations attached to every response
- Per-user conversation history across documents

### 4. Multi-Tenancy

- Isolated namespaces per user/organization in Qdrant
- Row-level security in PostgreSQL
- Per-tenant rate limiting and usage tracking

### 5. Caching Strategy

- Query result caching (Redis)
- Embedding caching to avoid recomputation
- Smart cache invalidation on document updates
- LRU eviction policy

### 6. Cost Optimization

- Batch embedding generation
- Token usage tracking per tenant
- Autoscaling Celery workers based on queue depth

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (async) |
| Workers | Celery + Redis |
| Vector DB | Qdrant |
| Relational DB | PostgreSQL + pgvector |
| Cache | Redis |
| Embeddings | BGE-M3 (multilingual, local) |
| LLM | OpenAI / Anthropic (with fallback) |
| Reranker | sentence-transformers (cross-encoder) |
| DevOps | Docker + GitHub Actions CI/CD |
| Cloud | AWS (ECS + RDS + ElastiCache) |
| Monitoring | Prometheus + Grafana |

---

## Team

| Role | Owner |
|---|---|
| Backend + DevOps + Cloud | Mehdi |
| Frontend (React + shadcn/ui) | Collaborator |

---

## Roadmap

### V1 — Core MVP *(now)*
- Document upload, chunking, and embeddings
- Vector search with LLM-generated answers
- Basic conversation history
- Stack: FastAPI + Qdrant + PostgreSQL

### V2 — Production System *(1–2 months)*
- Redis caching layer
- Celery background workers
- Hybrid search (vector + BM25)
- JWT auth + multi-tenancy
- Docker + CI/CD + AWS deployment

### V3 — SaaS Platform *(later)*
- (Server-Sent Events / SSE)
- Subscription billing (Stripe)
- Admin dashboard and usage analytics
- Monitoring (Prometheus + Grafana)
- Load testing (Locust, 1,000+ users)

### V4 — Advanced AI *(future)*
- OCR pipeline for invoices, medical records, and bank documents
- Structured document parsing (tables, forms)
- Multimodal RAG


---

## GitHub README

**AskMyDoc — AI Document Intelligence Platform**

Upload any document. Ask any question. Get sourced answers in under 500ms.

Built on a distributed RAG architecture with hybrid vector + full-text search, multi-tenant data isolation, and a cost-optimized AI pipeline.

`FastAPI` · `Qdrant` · `PostgreSQL` · `Redis` · `BGE-M3` · `Docker` · `AWS`