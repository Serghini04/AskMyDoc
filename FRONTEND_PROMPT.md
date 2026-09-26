# Senior Engineer Prompt — AskMyDoc Frontend (Next.js)

> Hand this to an engineer (human or AI). It is the single source of truth for building
> the AskMyDoc web client. Read it fully before writing any code.

---

## 1. Your Role & Mindset

You are a **senior frontend engineer** shipping the client for *AskMyDoc*, a RAG
(Retrieval-Augmented Generation) product. This frontend goes on a portfolio used in real
interviews — it must be **defensible line by line**. Optimize for:

- **Clean, idiomatic, production code** — not a prototype, not a tutorial.
- **A design that looks human-crafted**, not "AI-generated." (See §4 — this is non-negotiable.)
- **Correctness against the real API contract** in §5. Do not invent endpoints.

Work like a senior: make deliberate architectural choices, justify trade-offs in short
comments/PR notes, keep components small and composable, and don't ship dead code or
speculative abstractions.

---

## 2. Tech Stack (fixed)

- **Next.js (App Router)** + **TypeScript** (strict mode on).
- **Tailwind CSS** for styling + **shadcn/ui** for primitives (button, dialog, dropdown,
  toast, scroll-area, skeleton). Customize tokens — do **not** ship default shadcn theme.
- **TanStack Query** (React Query) for all server state (fetching, caching, mutations,
  optimistic updates). No manual `useEffect` fetch waterfalls.
- **Zustand** (or React context) only for genuinely client-side UI state (sidebar open,
  active session id, draft input). Keep it minimal.
- **react-markdown** + `remark-gfm` + syntax highlighting for rendering assistant answers.
- **Framer Motion** for tasteful motion (see §4).
- **Zod** for validating API responses at the boundary.
- Package manager: **pnpm**. Linting: **ESLint + Prettier**, enforced. Use `next lint`.

Do not add a state-management or UI library beyond the above without a written reason.

---

## 3. Pages & Features

### 3.1 Landing Page (`/`)
A marketing landing page for AskMyDoc. Sections:
- Hero: product name, one-line value prop ("Chat with your documents"), primary CTA
  → "Launch App" (links to `/chat`).
- Short "How it works" (3 steps: Upload → Ask → Get sourced answers).
- Feature highlights (semantic search, your data stays in your session, PDF/TXT support).
- Footer with minimal links.
- Fully responsive, accessible, fast (good Lighthouse + LCP). This page sets the design
  tone — it must feel like a real studio shipped it.

### 3.2 Chat App (`/chat` and `/chat/[sessionId]`)
A **ChatGPT-style** interface. Three regions:

**Left sidebar (session history):**
- "New Chat" button at top → creates a session via API, routes to it.
- List of sessions (title + relative timestamp), newest first, fetched from the API.
- Active session highlighted. Click → load that session.
- Per-session actions on hover (kebab menu): **Delete** (confirm dialog). *(Rename is not
  supported by the backend yet — see §6; build the UI affordance but disable/hide it, or
  do client-only rename clearly marked as TODO.)*
- Collapsible on desktop, drawer on mobile.

**Center (conversation):**
- Empty state when no messages (friendly prompt + suggestions).
- Message list: user vs. assistant bubbles, clearly distinct. Assistant messages render
  **Markdown** (code blocks, lists, tables) with copy-to-clipboard on code blocks.
- Auto-scroll to newest; "scroll to bottom" affordance when scrolled up.
- Loading state while the assistant is thinking (typing indicator / skeleton). **Note: the
  API is request/response, not streaming** — show a pending assistant bubble until the full
  response returns, then swap it in. (See §6 for the streaming caveat.)

**Composer (bottom):**
- Auto-growing textarea, Enter to send / Shift+Enter for newline. Disabled while sending.
- **File attach** button → upload PDF/TXT to the current session (multipart). Show upload
  progress, then poll document `status` until `completed`/`failed` and reflect it as a chip
  near the composer (filename + status). Block sending a message that depends on a doc that
  is still `processing` only if you choose to — otherwise just surface status clearly.
- Validate client-side: only `.pdf`/`.txt`, respect a max size (mirror backend limit).

**Documents panel:**
- Show documents attached to the active session (from `GET /sessions/{id}`). Each row:
  filename, size, status badge, download, delete (confirm).

---

## 4. Design Direction — "Not AI-Generated"

The reference is **https://firassa.studio/**. Open the live site and study it directly
(it is JS-rendered, so inspect it in a browser, not via scraping). Extract and apply its
actual principles — palette, type scale, spacing rhythm, motion timing — rather than
guessing. Then apply these rules so the result reads as *intentional craft*:

**Do:**
- Commit to a real **design language**: one expressive display typeface + one clean text
  typeface, a deliberate type scale, and a restrained palette (pick 1 accent, build neutrals
  around it). Define everything as **design tokens** (CSS vars / Tailwind theme).
- Use **generous, consistent spacing** on an 8px rhythm. Whitespace is a feature.
- **Motion with intent**: subtle, fast (150–250ms), eased entrances; micro-interactions on
  hover/press; respect `prefers-reduced-motion`. No gratuitous animation.
- Aim for a high-end, editorial / studio feel. Strong typographic hierarchy. Real visual
  contrast between sections.
- Pixel-level polish: aligned baselines, optical spacing, consistent border radii, focus
  rings, dark-mode parity if you do dark mode.

**Avoid (these scream "AI template"):**
- Generic SaaS gradient-purple hero with three identical icon cards.
- Default shadcn look, default Tailwind blue, unmodified component shadows.
- Emoji as section icons, centered-everything layouts, lorem-ipsum cadence.
- Inconsistent spacing, mismatched radii, random font weights.

Deliverable for design: a short `DESIGN.md` documenting tokens (color, type, spacing,
motion) and the rationale — so the choices are defensible in an interview.

---

## 5. API Contract (the real backend — do not deviate)

Base URL: `${NEXT_PUBLIC_API_BASE_URL}` → e.g. `http://localhost:8000/api/v1`.
Health check at `/health` (outside the `/api/v1` prefix).

All IDs are **UUID** strings. Timestamps are ISO 8601. Build a typed API client
(`lib/api/`) with Zod schemas; do not scatter raw `fetch` calls in components.

### Sessions
| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/sessions/` | — | `ChatSession` (created, empty) |
| GET | `/sessions/?skip=&limit=` | — | `ChatSession[]` (sidebar history) |
| GET | `/sessions/{id}` | — | `ChatSession` incl. `messages[]` + `documents[]` |
| DELETE | `/sessions/{id}` | — | 204 (also deletes its docs/vectors) |
| POST | `/sessions/{id}/chat` | `{ "message": string }` (1–4000 chars) | `ChatMessage` (the assistant reply) |

### Documents
| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/documents/` | multipart: `session_id` (form), `file` (PDF/TXT) | `Document` (status starts processing) |
| GET | `/documents/?skip=&limit=` | — | `Document[]` |
| GET | `/documents/{id}` | — | `Document` (poll `status` here) |
| DELETE | `/documents/{id}` | — | 204 |
| GET | `/documents/{id}/download` | — | file stream |

### Types (mirror these in TS/Zod)
```ts
type ChatMessage = {
  id: string; session_id: string;
  role: "user" | "assistant";
  content: string; created_at: string;
};
type Document = {
  id: string; filename: string; file_hash: string;
  file_size_bytes: number; status: string; // e.g. processing | completed | failed
  session_id: string; created_at: string;
};
type ChatSession = {
  id: string; title: string; created_at: string;
  messages: ChatMessage[]; documents: Document[];
};
```

### Error handling
- `409` on duplicate file upload (same hash in session) — show a friendly "already added".
- `413` file too large, `415` unsupported type — surface inline near the composer.
- `404` session/document not found — handle route guards gracefully.
- `500` LLM failure on chat — show a retryable error in the assistant slot, keep the user's
  message intact so they can retry.

---

## 6. Known Backend Gaps (account for these — do not silently break)

These are real limitations of the current V1 backend. Build defensively and document them:

1. **CORS is not configured** in the FastAPI app. The browser client *will be blocked*
   until `CORSMiddleware` is added server-side. Flag this to the backend owner and, for
   local dev, document the fix (allow `http://localhost:3000`). Do not work around it with
   a hardcoded proxy hack without noting it.
2. **No streaming endpoint.** Chat is a single request/response. Design the UI so it can be
   upgraded to streaming later (token-by-token) without a rewrite — isolate the "send
   message" logic behind one hook/service.
3. **No session rename endpoint** and titles are auto-assigned at creation. Either hide the
   rename UI or make it client-only and clearly TODO.
4. **No auth.** Everything is open / single-user. Don't build login UI; structure the API
   client so an auth token can be injected later (one place to add an `Authorization`
   header).
5. Document processing is **async** — newly uploaded docs need polling on `GET
   /documents/{id}` (or refetch the session) until status settles.

---

## 7. Architecture & Code Quality

```
src/
  app/                      # App Router routes
    (marketing)/page.tsx    # landing
    chat/[[...sessionId]]/  # chat shell + dynamic session
  components/
    ui/                     # shadcn primitives (themed)
    chat/                   # MessageList, Composer, SessionSidebar, DocumentPanel...
    landing/                # hero, sections
  lib/
    api/                    # typed client, zod schemas, endpoint fns
    hooks/                  # useSessions, useChat, useUploadDocument (React Query)
    store/                  # zustand UI state
    utils/
  styles/                   # tokens, globals
```

Standards:
- **TypeScript strict**, no `any`, no non-null `!` abuse. Validate API responses with Zod.
- **Server state via React Query** with sensible `queryKey`s, optimistic updates for sending
  messages and creating sessions, and cache invalidation on mutations.
- Components are **small, single-responsibility, accessible** (keyboard nav, ARIA, focus
  management in dialogs, labelled inputs).
- **No business logic in JSX** — extract to hooks/lib.
- **Loading / empty / error states for every async surface.** No raw spinners-only UX.
- **Responsive + mobile-first.** The chat must work on a phone (sidebar as drawer).
- Accessibility: meets WCAG AA contrast, visible focus, `prefers-reduced-motion`.
- Performance: code-split routes, lazy-load heavy bits (markdown/highlighter), optimize
  fonts (`next/font`), good Core Web Vitals.
- **Env config** via `.env.local` (`NEXT_PUBLIC_API_BASE_URL`). Never hardcode the host.
- Tests: at minimum, unit-test the API client + key hooks (Vitest + Testing Library), and
  one happy-path integration test for the chat flow.

---

## 8. Deliverables

1. Working Next.js app: landing page + full chat experience per §3.
2. Typed, validated API client matching §5 exactly.
3. `DESIGN.md` (tokens + rationale) and an updated `README.md` (setup, env, run, decisions).
4. Lint/format clean, builds with no TS errors, tests passing.
5. A short note listing the backend gaps from §6 that you hit and how you handled them.

---

## 9. Acceptance Criteria

- I can land on `/`, click "Launch App", create a new chat, upload a PDF, ask a question,
  and get a Markdown-rendered, sourced-feeling answer — all against the real API.
- Sessions persist in the sidebar; I can switch, delete, and resume them.
- The UI is responsive, accessible, and **looks like a real studio designed it** — if a
  reviewer would guess "AI-generated template," it fails this criterion.
- Code is clean enough that each architectural decision is defensible in an interview.
```
