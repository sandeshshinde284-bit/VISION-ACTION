# V.I.S.I.O.N. Process Flow & Workflows
**Date:** Oct 21, 2026 | **Version:** 1.0 | **Status:** Verified

This document describes the key workflows and process flows in V.I.S.I.O.N., including sequence diagrams and step-by-step procedures.

---

## 1. AUTHENTICATION FLOW

### Login Process
```
User → LoginView.vue
    ↓
POST /api/login (username, password)
    ↓
backend/db_service.authenticate_user()
    ↓
Generate secure session token (64-char)
    ↓
Store in sessionStorage
    ↓
Redirect to HomeView
```

**Steps:**
1. User enters credentials in LoginView.vue
2. Frontend sends POST request to `/api/login`
3. Backend validates credentials against SQLite `users` table
4. On success, server generates cryptographically secure token
5. Token stored in browser `sessionStorage` (cleared on tab close)
6. Frontend redirects to `/` (HomeView)
7. WebSocket connection validates token on `/ws` connect

**Security:**
- Password stored as hash in database (never plain text)
- Token is 64-character random string (Python `secrets` module)
- `sessionStorage` (not `localStorage`) — cleared when tab closes
- All API endpoints validate token before processing

---

## 2. WEBSOCKET CONNECTION FLOW

### Initial Connection
```
Frontend WebSocketService
    ↓
Connect to ws://localhost:8000/ws
    ↓
Backend accepts connection (if token valid)
    ↓
Hydrate message history from SQLite
    ↓
Send [HYDRATED_HISTORY: {...}]
    ↓
UI renders chat history + ready for input
```

**Steps:**
1. HomeView mounts → WebSocketService connects to `/ws`
2. Backend receives connection, validates `vision_auth_token` from query params
3. Backend queries SQLite `messages` table for session history
4. Streams historical chat messages to frontend (ChatGPT-style hydration)
5. Frontend renders messages in SystemLog.vue
6. UI shows "ready" state, user can type

### Message Flow
```
User types message
    ↓
handleSend() validates input
    ↓
WebSocket.send({text, scope: AUTO/WEB/INTERNAL/BOTH})
    ↓
Backend receives message
    ↓
Route intent (CHAT/WEB/INTERNAL)
    ↓
Call Gemini + RAG as needed
    ↓
Stream response tokens in real-time
    ↓
Save message to SQLite
    ↓
Frontend renders streaming response
```

**Routing Logic (ai_service.py):**
1. **Layer 1 (Fast-Path):** Check for `@web`, `@internal`, `@both` shortcuts (regex)
2. **Layer 2 (Intent Classification):** If ambiguous, call Gemini to classify intent
3. **Layer 3 (Execution):**
   - `GREETING` → CHAT (no RAG, no web search)
   - `GENERAL` → WEB (Google Search grounding)
   - `INTERNAL` → RAG (ChromaDB semantic search)
   - `AMBIGUOUS` → Ask user for clarification

---

## 3. RAG (RETRIEVAL-AUGMENTED GENERATION) PIPELINE

### Document Upload & Indexing
```
Frontend: User clicks "📎 Attach" → Drag-and-drop file
    ↓
POST /api/upload (PDF/DOCX/TXT)
    ↓
Backend validates file (size ≤ 15MB)
    ↓
Extract text (pypdf for PDF, python-docx for DOCX)
    ↓
Calculate SHA-256 hash (deduplication)
    ↓
Split into 1000-char chunks (200-char overlap)
    ↓
Embed via Vertex AI text-embedding-004
    ↓
Store in ChromaDB (local, persistent)
    ↓
Save metadata (filename, page, section) to SQLite
    ↓
Frontend shows "Document indexed" status
```

**Deduplication:** If same file uploaded twice, SHA-256 hash matches → skip embedding (saves cost)

### Semantic Search & Context Injection
```
User asks question
    ↓
RAG decides: Should I search ChromaDB?
    ↓
Convert question to vector (text-embedding-004)
    ↓
Query ChromaDB: cosine_similarity ≤ 0.85
    ↓
Retrieve Top-3 matching documents
    ↓
Extract: filename, page, section metadata
    ↓
Inject context into system prompt:
  "[SOURCE CONTEXT - SYNTHESIZE ONLY]
   <retrieved_text>
   [/SOURCE CONTEXT]"
    ↓
Send to Gemini with injected context
    ↓
Parse response, strip [SOURCE:] tags
    ↓
Render citations in RAG Citations drawer
```

**Threshold:** `distance ≤ 0.85` (configurable, may be too loose/strict — to be tuned)

---

## 4. SESSION & CHAT MANAGEMENT FLOW

### New Session
```
User clicks "+ New Session"
    ↓
POST /api/sessions {session_id, title, admin_name}
    ↓
Backend creates record in `sessions` table
    ↓
Clear message list in UI
    ↓
WebSocket maintains connection (same user)
    ↓
New messages saved to new session
```

### Session History
```
GET /api/sessions (admin_name)
    ↓
Backend queries all sessions for this user
    ↓
Return list: {id, title, timestamp, message_count}
    ↓
Frontend renders in sidebar
    ↓
User clicks session → Switch context
```

---

## 5. SYSTEM DIRECTIVES & AI PERSONA FLOW

### Load Directives
```
Backend startup
    ↓
Check database `system_settings` table
    ↓
If empty: Read SYSTEM_DIRECTIVES.md from disk
    ↓
Seed to database
    ↓
Reload into ai_service.system_context
    ↓
Gemini uses as system prompt for all calls
```

### Update Directives (Admin Only)
```
Admin user submits new directives via UI
    ↓
POST /api/directives (content, role=ADMIN)
    ↓
Backend validates role (only ADMIN/LEAD)
    ↓
Save to database
    ↓
Mirror to local disk (if writable)
    ↓
Call ai_service.reload_directives()
    ↓
Next Gemini call uses updated context
```

---

## 6. TELEMETRY STREAMING FLOW

### Real-Time System Metrics
```
Backend (every 2 seconds):
    ↓
Fetch CPU%, RAM%, Disk% via psutil
    ↓
Stream via WebSocket: [TELEMETRY: {cpu, ram, disk}]
    ↓
Frontend receives and updates dashboard
    ↓
Charts update in real-time
```

---

## 7. DEPLOYMENT FLOW (Development)

See `03-DeploymentAndCommands.md` for setup steps.

**Quick Summary:**
```
Backend:
  python3.12 -m venv backend/.venv
  source backend/.venv/bin/activate
  pip install -r backend/requirements.txt
  python -m backend.app.main

Frontend:
  npm install
  npm run dev (port 5173)

Visit: http://localhost:5173
```

---

## 8. INTEGRATION FLOWS (Partial)

### Confluence Sync (Partial Implementation)
```
/api/sync/confluence → Trigger sync
    ↓
Fetch documents from Confluence API
    ↓
Extract text + metadata
    ↓
Treat as RAG documents (chunk, embed, store)
```

**Status:** Routes exist; full automation unclear

### ADO Sync (Partial Implementation)
```
/api/sync/ado → Trigger sync
    ↓
Fetch work items from ADO API
    ↓
Extract description + comments
    ↓
Treat as RAG documents (chunk, embed, store)
```

**Status:** Routes exist; full automation unclear

---

## SUMMARY

**Key Workflows:**
1. ✅ Authentication (DB-driven, secure tokens)
2. ✅ WebSocket connection (history hydration)
3. ✅ Message routing (intent classification)
4. ✅ RAG pipeline (upload → chunk → embed → search)
5. ✅ Session management (multi-session support)
6. ✅ Directives reload (dynamic system prompt)
7. ✅ Telemetry streaming (real-time metrics)
8. ⚠️ Confluence/ADO sync (partial)

All verified to exist in codebase.
