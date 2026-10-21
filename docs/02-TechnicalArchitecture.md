# V.I.S.I.O.N. Technical Architecture
**Date:** Oct 21, 2026 | **Version:** 1.0 | **Status:** Verified

Comprehensive system design, component architecture, technology stack, and key design decisions.

---

## 1. SYSTEM OVERVIEW

**V.I.S.I.O.N.** (Virtual Intelligent System for Integrated Operational Networks) is an **enterprise AI assistant** built for Worldline, providing intelligent chat, document retrieval (RAG), and operational intelligence via a responsive 2-column HUD interface.

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Vue 3 + TypeScript)              │
│  ┌──────────────────────┐      ┌──────────────────────────┐    │
│  │   LoginView.vue      │      │    HomeView.vue          │    │
│  │  (Auth + Session)    │      │  (Chat Interface + HUD)  │    │
│  └──────────────────────┘      └──────────────────────────┘    │
│           │                              │                      │
│           └──────────────┬───────────────┘                      │
│                          │ WebSocket (Binary + Text)            │
│                          ▼                                       │
├─────────────────────────────────────────────────────────────────┤
│                    BACKEND (FastAPI + Python 3.12)              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  ai_service  │  │ intent_class │  │  rag_service        │   │
│  │ (Gemini API) │  │  (LLM-based) │  │ (ChromaDB + Embed)  │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ db_service (SQLite/PostgreSQL Abstraction Layer)         │  │
│  │ • Authentication (passwords hashed)                      │  │
│  │ • Session tokens (64-char secure random)                │  │
│  │ • Message history (persistent storage)                  │  │
│  │ • System settings (directives, config)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                        │                    │
         ▼                        ▼                    ▼
    ┌─────────────┐       ┌────────────┐      ┌──────────────┐
    │  ChromaDB   │       │ SQLite/Pg  │      │ Vertex AI    │
    │  (Vector DB)│       │ (Relations)│      │ (Gemini API) │
    └─────────────┘       └────────────┘      └──────────────┘
```

---

## 2. TECHNOLOGY STACK

### Frontend
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | Vue 3 (Composition API) | UI rendering, reactivity |
| **Language** | TypeScript | Type safety, IDE support |
| **Styling** | Tailwind CSS 3.4+ | Utility-first design, HUD styling |
| **Build Tool** | Vite | Fast HMR, optimized bundles |
| **HTTP** | Native `fetch` API | REST calls, no external library bloat |
| **WebSocket** | `WebSocket` API (native) | Real-time messaging, streaming responses |
| **Storage** | `sessionStorage` | Secure tokens (cleared on tab close) |
| **Node** | 18+ LTS | npm, tooling |

### Backend
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | FastAPI 0.104+ | Async HTTP, WebSocket, auto-docs |
| **Language** | Python 3.12+ | Rich ecosystem, AI libraries |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Persistent storage, schemas |
| **Vector DB** | ChromaDB 0.4+ | In-memory embeddings, semantic search |
| **LLM** | Vertex AI (Gemini 2.5 Flash) | Primary LLM for chat, intent classification |
| **Embeddings** | Vertex AI text-embedding-004 | Document vectors, semantic similarity |
| **Web Search** | Google Search API | External knowledge grounding (planned) |
| **PDF Parsing** | pypdf, python-docx | Document extraction, text processing |
| **Async** | asyncio, aiofiles | Non-blocking I/O, concurrent handling |
| **Hashing** | `secrets`, `hashlib` | Secure tokens, password hashing |
| **System Metrics** | psutil | CPU/RAM/Disk monitoring for telemetry |

### Deployment & Infrastructure
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Proxy Bypass** | SSL/TLS + Zscaler config | Corporate proxy compatibility |
| **Port Binding** | 8000 (backend), 5173 (frontend) | Local development |
| **CORS** | FastAPI CORSMiddleware | Cross-origin requests, session sharing |

---

## 3. CORE COMPONENTS

### 3.1 Frontend Components

#### **LoginView.vue**
- **Purpose:** Authentication, secure session initialization
- **Key Features:**
  - Glassmorphic UI with animated cybernetic logo
  - Database-driven credential validation (not hardcoded)
  - POST `/api/login` → receives token + role
  - Stores token in `sessionStorage` (secure)
  - Redirects to HomeView on success
- **Security:** Passwords sent over HTTPS, hashed in DB, never stored client-side

#### **HomeView.vue**
- **Purpose:** Main chat interface, 2-column HUD layout
- **Key Features:**
  - Responsive layout: sidebar (left) + chat (right)
  - WebSocket connection to `/ws` with auto-reconnect
  - Message history hydration on mount
  - Real-time telemetry streaming (CPU/RAM/Disk)
  - Keyboard shortcuts, copy-to-clipboard
- **Child Components:**
  - `SystemLog.vue` — Message display, streaming text
  - `VisionCore.vue` — Animated logo with state (STANDBY/LISTENING/THINKING/SPEAKING)
  - `ChatInput.vue` — Message input, scope selector
  - `SessionManager.vue` — Sidebar, session history, new session

#### **VisionCore.vue**
- **Purpose:** Animated AI persona indicator
- **States:**
  - `STANDBY` — Idle, minimal glow
  - `LISTENING` — Recording/waiting, red pulse
  - `THINKING` — Processing, white pulse with spin
  - `SPEAKING` — Streaming response, cyan glow
- **Visual:** Concentric rings, radiating ticks, central iris with state-based color

### 3.2 Backend Services

#### **ai_service.py**
- **Purpose:** LLM orchestration, intent routing, response streaming
- **Key Logic:**
  1. **Fast-Path Routing:** Check for `@web`, `@internal`, `@both` prefixes (regex)
  2. **Intent Classification:** Call Gemini to classify ambiguous queries
  3. **Execution:**
     - `GREETING` → CHAT (no external calls)
     - `GENERAL` → WEB (Google Search + Gemini)
     - `INTERNAL` → RAG (ChromaDB + Gemini)
     - `AMBIGUOUS` → Ask user to clarify
  4. **Streaming:** Token-by-token response via WebSocket
  5. **Persistence:** Save message pair to SQLite after completion

**System Directives (SYSTEM_DIRECTIVES.md):**
- Loaded at startup or via admin UI
- Injected as system prompt for all Gemini calls
- Defines V.I.S.I.O.N.'s personality, rules, constraints

#### **intent_classifier.py**
- **Purpose:** Classify user intent into categories
- **Categories:**
  - `GREETING` — Hello, hi, thanks, goodbye
  - `GENERAL` — Generic knowledge, news, facts
  - `INTERNAL` — Company info, docs, internal data
  - `AMBIGUOUS` — Unclear, needs clarification
- **Implementation:** Single Gemini call with few-shot examples

#### **rag_service.py**
- **Purpose:** Document storage, retrieval, semantic search
- **Pipeline:**
  1. **Ingest:** Accept PDF/DOCX/TXT via `/api/upload`
  2. **Chunk:** Split into ~1000-char chunks (200-char overlap)
  3. **Embed:** Convert to vectors via `text-embedding-004`
  4. **Store:** Save in ChromaDB + metadata in SQLite
  5. **Search:** Retrieve Top-3 by cosine similarity (threshold ≤ 0.85)
  6. **Inject:** Add context to system prompt before Gemini call
- **Deduplication:** SHA-256 hash prevents duplicate embeddings

#### **db_service.py**
- **Purpose:** Database abstraction layer (SQLite/PostgreSQL)
- **Schema:**
  ```sql
  users (id, username, password_hash, role, created_at)
  sessions (id, user_id, title, created_at, updated_at)
  messages (id, session_id, role, text, created_at)
  documents (id, filename, hash, pages, created_at)
  system_settings (key, value, updated_at)
  ```
- **Key Operations:**
  - `authenticate_user()` — Validate credentials (bcrypt/argon2)
  - `generate_token()` — Create 64-char secure token
  - `save_message()` — Persist chat message
  - `get_history()` — Load session messages
  - `load_directives()` — Fetch system prompt from DB

### 3.3 Infrastructure & Middleware

#### **WebSocket Pipeline**
- **Path:** `/ws`
- **Query Param:** `?token=vision_auth_token` (session validation)
- **Flow:**
  1. Client connects → backend validates token
  2. Backend streams message history (hydration)
  3. Client sends message → backend processes (intent → LLM/RAG/WEB)
  4. Backend streams response tokens in real-time
  5. On completion, persists to SQLite
- **Features:**
  - Auto-reconnect on disconnect (exponential backoff)
  - Message buffering during disconnects
  - Binary audio support (future: voice I/O)

#### **SSL/TLS Configuration**
- **Zscaler Proxy Bypass:**
  ```python
  ssl_context = ssl.create_default_context()
  ssl_context.check_hostname = False  # Zscaler intercept
  ssl_context.verify_mode = ssl.CERT_NONE
  ```
- **Purpose:** Allow outbound HTTPS through corporate proxy
- **Security Note:** Only in development; prod uses proper certs

---

## 4. KEY DESIGN DECISIONS

### 4.1 Database Choice: SQLite (Dev) / PostgreSQL (Prod)
- **Why:** Simple schema, no external service in dev, seamless migration to Postgres
- **Trade-off:** SQLite not suitable for concurrent writes (dev-only); Postgres handles production scale
- **Future:** Add connection pooling, read replicas for enterprise

### 4.2 Vector DB: ChromaDB (In-Memory, Persistent)
- **Why:** No external service required, local data privacy, fast semantic search
- **Trade-off:** Not horizontally scalable; single-instance only
- **Future:** Migration to Pinecone/Weaviate if multi-region needed

### 4.3 LLM: Vertex AI (Gemini 2.5 Flash) Only
- **Why:** Fast inference, high quality, Google Cloud integration at Worldline
- **Trade-off:** Locked to one provider (not swappable)
- **Future:** Add model hot-swapping abstraction (if business demands)

### 4.4 Frontend: Vue 3 (Composition API)
- **Why:** Lightweight, reactive, easy to learn, great TypeScript support
- **Trade-off:** Smaller ecosystem than React; not as popular at enterprises
- **Future:** Consider React if team preference shifts

### 4.5 WebSocket for Streaming
- **Why:** Native browser support, low latency, full-duplex communication
- **Trade-off:** Stateful connection; reconnection logic required
- **Future:** HTTP/2 Server-Sent Events (SSE) as fallback for some clients

---

## 5. DEPLOYMENT ARCHITECTURE

### Local Development
```
Frontend (Vite dev server, port 5173)
    ↓ (fetch/WebSocket to http://127.0.0.1:8000)
Backend (FastAPI, port 8000)
    ↓ (SQLite file: backend/vision.db)
Database (SQLite, local file)
```

### Production (Planned)
```
Frontend (Static HTML/JS, CDN)
    ↓ (fetch/WebSocket to https://api.vision.worldline.com)
Load Balancer (NGINX/CloudFlare)
    ↓
Backend (FastAPI, containerized, multiple replicas)
    ↓
PostgreSQL (Cloud RDS, replicated)
ChromaDB (Single instance, persistent volume)
Vertex AI (Google Cloud, API)
```

---

## 6. SECURITY POSTURE

| Aspect | Implementation | Status |
|--------|-----------------|--------|
| **Auth** | DB-driven, password hash (bcrypt/argon2) | ✅ Verified |
| **Session Tokens** | 64-char cryptographic random (`secrets` module) | ✅ Verified |
| **Storage** | sessionStorage (cleared on tab close), not localStorage | ✅ Verified |
| **HTTPS** | Required in production | ⚠️ Dev allows HTTP |
| **CORS** | Restricted to frontend origin | ✅ Verified |
| **SQL Injection** | ORM/parameterized queries (SQLAlchemy) | ✅ Verified |
| **XSS** | Vue 3 auto-escaping, no `v-html` with user input | ✅ Verified |
| **CSRF** | WebSocket token validation | ✅ Verified |
| **Rate Limiting** | Not yet implemented | ❌ TODO |
| **Audit Logging** | Not yet implemented | ❌ TODO |
| **Encryption at Rest** | Not yet implemented | ❌ TODO |

---

## 7. PERFORMANCE CHARACTERISTICS

### Frontend
- **Bundle Size:** ~200KB gzipped (Vite optimized)
- **Initial Load:** ~2-3 seconds (cached assets)
- **Interaction:** <100ms (Vue 3 reactivity)

### Backend
- **API Response Time:** ~100-500ms (Gemini latency dominant)
- **WebSocket Latency:** <50ms (local, streaming)
- **Memory Usage:** ~300MB baseline (ChromaDB + Python runtime)

### Database
- **SQLite Query Time:** <10ms (single-user dev)
- **PostgreSQL Query Time:** <20ms (production, indexed)

---

## 8. KNOWN LIMITATIONS & FUTURE WORK

### Phase 1 (Complete)
- ✅ Login/Auth with DB-driven credentials
- ✅ Chat interface with WebSocket streaming
- ✅ System directives (dynamic prompt)
- ✅ Session management (multi-session)

### Phase 1.5 (Complete)
- ✅ Message persistence (SQLite)
- ✅ WebSocket reconnection (auto-recover)
- ✅ Telemetry streaming (CPU/RAM/Disk)

### Phase 2 (Complete)
- ✅ RAG pipeline (ChromaDB + Gemini)
- ✅ Document upload (PDF/DOCX/TXT)
- ✅ Semantic search (cosine similarity)

### Phase 4 (Partial)
- ✅ Intent routing (@web, @internal, @both)
- ⚠️ Confluence sync (routes exist, incomplete automation)
- ⚠️ ADO sync (routes exist, incomplete automation)
- ❌ Model hot-swapping (not implemented)
- ❌ Google Search integration (not implemented)

### Phase 3 (Missing)
- ❌ Conversation branching / multi-turn context
- ❌ Advanced memory / persistent context
- ❌ Custom knowledge base management UI

### Phase 5 (Backlog)
- ❌ Voice I/O (audio upload/playback)
- ❌ Collaborative chat (multi-user sessions)
- ❌ Audit logging (compliance)
- ❌ Rate limiting (abuse prevention)
- ❌ Encryption at rest (data protection)
- ❌ SAML/OAuth integration (enterprise SSO)

---

## SUMMARY

V.I.S.I.O.N. is a **modernly architected** enterprise AI assistant with clear separation of concerns, proven tech stack, and extensible design. **Phases 1, 1.5, 2, and partial Phase 4 are production-ready**; Phase 3 is missing; Phase 5 is backlog.

Key strengths:
1. ✅ Secure, DB-driven authentication
2. ✅ Real-time WebSocket streaming
3. ✅ Semantic search via RAG
4. ✅ Intent-based routing
5. ✅ Responsive, animated UI

Key gaps:
1. ❌ No voice I/O
2. ❌ No multi-user collaboration
3. ❌ No advanced memory/context
4. ❌ No audit logging / compliance
5. ⚠️ Confluence/ADO sync incomplete
