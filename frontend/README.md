# AskMyDoc — Frontend

A Next.js web client for the AskMyDoc RAG backend: a marketing landing page plus a
ChatGPT-style interface for chatting with your own documents.

## Stack

- **Next.js 16** (App Router) + **TypeScript** (strict)
- **Tailwind CSS v4** with a token-based design system (see [`DESIGN.md`](./DESIGN.md))
- **TanStack Query** for all server state (caching, mutations, optimistic updates, polling)
- **Zustand** for the small amount of client-only UI state
- **Zod** for validating every API response at the boundary
- **react-markdown** + `remark-gfm` for rendering assistant answers
- **Framer Motion** for restrained motion

## Getting started

```bash
# 1. Install
npm install

# 2. Configure the API base URL
cp .env.example .env.local
#   edit NEXT_PUBLIC_API_BASE_URL if your backend isn't on http://localhost:8000

# 3. Run
npm run dev          # http://localhost:3000
```

The backend must be running and must allow this origin via CORS
(`CORS_ORIGINS=http://localhost:3000`, already the default in the backend `.env.example`).

### Scripts
| Command | Purpose |
|---|---|
| `npm run dev` | Dev server |
| `npm run build` | Production build (also type-checks) |
| `npm run start` | Serve the production build |
| `npm run lint` | ESLint |

## Architecture

```
src/
  app/
    page.tsx                 Landing page
    chat/
      layout.tsx             Sidebar + content shell
      page.tsx               No session selected
      [sessionId]/page.tsx   A single conversation
  components/
    brand/                   Wordmark
    landing/                 Hero, how-it-works, features, footer
    chat/                    Sidebar, message list, composer, document chips…
    ui/                      Button, ConfirmDialog (hand-styled primitives)
    providers/               React Query provider
  lib/
    api/                     Typed client, Zod schemas, endpoint modules
    hooks/                   useSessions, useChat, useDocuments, query keys
    store/                   Zustand UI store
    env.ts, utils.ts
```

**Principles**
- Components never call `fetch` directly — everything goes through `lib/api` + a hook.
- Responses are Zod-validated, so component types are trustworthy.
- Loading / empty / error states exist for every async surface.
- One place to add auth later (`authToken` in `lib/api/client.ts`).

## API contract

Talks to the FastAPI backend under `NEXT_PUBLIC_API_BASE_URL`:
`/sessions` (CRUD + `/{id}/chat`) and `/documents` (upload, get, delete, download).
Types mirror the backend Pydantic schemas exactly — see `src/lib/api/schemas.ts`.

## Backend limitations handled here

These are real V1 backend constraints the client is built around:

1. **CORS** must be enabled server-side, or the browser blocks every request. The client
   surfaces a clear "couldn't reach the server / check CORS" error when that happens.
2. **No streaming** — `POST /sessions/{id}/chat` returns the full reply at once. The send
   flow is isolated in `useSendMessage` so a future token-streaming upgrade is localized.
3. **No auth** — single-user/open. There's one injection point for an auth token.
4. **Async document processing** — uploads start as `processing`; the client polls each
   document until its status settles.

Session rename is supported via `PATCH /sessions/{id}` (added alongside this client).
