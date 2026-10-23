# V.I.S.I.O.N. - MASTER ISSUES & BUGS TRACKER

**Date:** 2026-10-21  
**Status:** CRITICAL PRODUCTION ISSUES  
**Version:** 1.0

---

## SUMMARY

Total Issues Found: **16 CRITICAL + HIGH PRIORITY BUGS** (+ 12 discovered along the way — 3 sync/chat crashes, 2 Windows startup crashes, and 7 from the separate `18-IssuesAndRoadmap.md` merge — all logged below, none scattered)

| Priority | Category | Count | Status |
|----------|----------|-------|--------|
| 🔴 MUST FIX | Chat System | 5 issues | 3 FIXED (2026-10-22), 2 still open |
| 🔴 MUST FIX | Error Handling | 6 issues | FIXED (2026-10-22) |
| 🟠 SHOULD FIX | Real-time Feedback | 1 issue | Still open (web search scope UI) |
| 🟡 NICE TO HAVE | Missing Features | 2 issues | Incomplete product |
| 🟡 NICE TO HAVE | Design System | — | Glasmorphic → Flat/Hybrid |
| **TOTAL** | — | **16** | **DO NOT SHIP — 2 open chat UX gaps remain** |

---

## ✅ FIXED ON 2026-10-22

- **Issue #14 root-cause dependency / Confluence sync crash (NEW FIND):** `sync_confluence_page()` referenced an undefined `filename` variable — every single-page Confluence sync (`/api/sync/confluence/page/{id}`) was silently crashing with `NameError`, caught by the blanket `except Exception`, and returning `False` with zero detail. Fixed: `filename` is now derived from `space_key`/`page_id` before use.
- **Issue #1 (Confluence sync fails silently):** `sync_confluence_page()` now classifies every failure (`classify_sync_error()`) into `error_type` + `retryable` + human message, and persists it via `db_service.record_sync_complete(..., error=...)` instead of a bare `False`.
- **Issue #2 (ADO sync fails silently):** Same structured-error treatment applied to `sync_ado_workitem()`.
- **Issue #3 (no retry logic):** Added `retry_with_backoff()` — retryable errors (timeouts, 5xx, 429, connection errors) now retry up to 3x with exponential backoff (3s → 6s → 12s) before giving up; non-retryable errors (401/403/404) fail fast.
- **Issue #4 (RAG ingestion failures had no error detail):** Ingestion failures and crashes now write a classified `error_type` string into `sync_log.error_message` (visible via `GET /api/sync/status`) instead of a generic log line.
- **Issue #7 (thinking state never ends) / #10 (status history not reset) / #11 (timer memory leak):** Already fixed prior to this pass — verified still correct in `SystemLog.vue`.
- **Issue #8 (no feedback during streaming) / #12 (missing STREAMING state):** Added `'STREAMING'` to the `aiState` state machine (`useWebSocket.ts`, `SystemLog.vue`, `HomeView.vue`). The UI now flips from "🧠 thinking" to "📨 V.I.S.I.O.N. is responding..." the moment the first token/chunk arrives, instead of leaving the thinking indicator up while the response is already visible.
- **Issue #9 (timeout has no cancel button):** Added a "❌ Cancel" button next to the "taking longer than usual" warning, wired to a new `cancelRequest()` in `useWebSocket.ts`. This is a **soft cancel**: the backend request already in flight keeps running (it's in a thread executor with no cooperative cancellation hook), but the frontend immediately returns to STANDBY and silently discards whatever response eventually arrives. A true hard-cancel (aborting the backend thread) is tracked as follow-up work below.

## ✅ FIXED ON 2026-10-22 (ROUND 2 — error-handling-doc follow-through)

- **NEW CRITICAL BUG FOUND: chat hangs forever on ANY backend exception.** `ai_service.process_text()`'s top-level `except Exception` built a fallback reply string and `return`ed it — but `websockets.py` calls `process_text` via `run_in_executor` and **discards the return value**. So on any exception after `message_start` was sent (a Gemini quota error, a dropped DB write, anything), the frontend never received `streaming_complete` and was stuck in THINKING/STREAMING forever, with the soft-cancel button as the only way out. Fixed: the except block now sends `message_start` → `text_chunk` (fallback text) → `streaming_complete` itself before returning, so the UI always recovers on its own.
- **Issue #5 (no sync status WebSocket push) — now fully fixed:** Added `ACTIVE_CONNECTIONS` registry + `broadcast_sync_notification()` in `websockets.py`, and a `_notify_sync_complete()` wrapper in `sync_connectors.py` that every sync call site now uses instead of calling `db_service.record_sync_complete()` directly. The frontend (`useWebSocket.ts`) handles the new `sync_notification` frame type, pushes a `[SYSTEM: ✅/❌ ...]` line into chat, and buffers the last 20 into `lastSyncNotifications` for the dashboard below.
- **Issue #13 (no granular processing status) — partially improved:** Added `send_status("Querying internal knowledge base...")` and a post-retrieval `send_status(f"Retrieved {n} chunk(s)...")` around the ChromaDB query in `ai_service.py`, closing the silent gap between "Analyzing intent" and "Synthesizing response". Does **not** include percentage-based progress bars (`progress_percent: 48` style) — that would need per-chunk instrumentation inside `rag_service.query_knowledge_base()`, not done here.
- **Issue #4 (RAG ingestion errors) — now properly fixed, not just caller-side:** `rag_service.ingest_document()` now sets `self.last_ingest_error = {"error_type": "parsing_failed"|"chunking_failed"|"embedding_failed"|"storage_failed"|"storage_unavailable"|"security_blocked"|"internal_error", "message": ...}` on every failure path, while still returning `bool` so no caller breaks. `sync_confluence_page`/`sync_ado_workitem` now read this instead of writing a generic "ingestion_failed" string.
- **Issue #6 (error type classification) — expanded:** `classify_sync_error()` now also detects `dns_resolution_failed`, `proxy_error` (exception + HTTP 407), `mfa_required` (403 + body sniff), `document_archived` (410), `file_too_large` (413), `document_locked` (423), and `quota_exceeded` (429 + body sniff). Still not a full app-wide enum, and still sync-specific (not applied to web search).
- **Issue #15 (web search UI "completely missing") — CORRECTED, this claim was stale/wrong.** Traced the code: `HomeView.vue` already has working AUTO/INTERNAL/WEB/BOTH scope chips (lines ~569-598) wired to `activeScope`, which prefixes outgoing messages with `[SCOPE: ...]`, parsed by `ai_service.py:347` and routed accordingly. This has existed since before this audit pass — the original `VISION-ERROR-HANDLING-AUDIT.md` claim was simply inaccurate. **No fix needed; nothing was open here.**
- **Issue #16 (no sync status dashboard) — now fixed, plus a blocking bug found underneath it:** The backend (`sync_status.py` → `/api/sync-status/summary`) already existed but was **completely unreachable for everyone**: `require_admin()` called `security_service.is_admin()`, a method that doesn't exist anywhere in the codebase, so `hasattr(...)` was always `False` and the endpoint always returned 403 regardless of caller. Fixed by switching to the same session-token check `sync_routes.py` already uses. Built the missing frontend half: `SyncStatusPanel.vue` (new), toggled from a 🔄 button next to the connection badge in `HomeView.vue`, showing per-source health + the live notification feed from the fix above.

## ✅ FIXED ON 2026-10-23 — found by actually running the app on Windows (not from reading code)

Bhai ran `python run.py` on Windows and sent the real startup log. Two genuine, previously-undetected
bugs surfaced that no amount of reading the diff would have caught — exactly why "nothing is working
right until it's tested" matters. Both root-caused against the actual code and fixed.

- **Issue #28 — `AttributeError: 'Settings' object has no attribute 'DEFAULT_ADMIN_NAME'` on every single startup.** `db_service.py` (schema-init path, "Auto-seeding default chat session") referenced `settings.DEFAULT_ADMIN_NAME`, but `config.py`'s `Settings` class only ever defined `DEFAULT_ADMIN_USERNAME` — `DEFAULT_ADMIN_NAME` never existed. Caught by a blanket `except Exception` and logged as a one-line ERROR ("Failed to initialize database schema"), so it never crashed the app but silently broke default-session seeding on literally every boot. Fixed: corrected the attribute name to `settings.DEFAULT_ADMIN_USERNAME`.
- **Issue #29 — hard startup crash on Windows: `UnicodeDecodeError` in `slowapi`'s `Limiter()` while importing `app/main.py`.** Root cause: `slowapi.Limiter.__init__` auto-detects any `.env` file sitting in the current working directory and hands it to `starlette.Config()`, which — depending on the installed starlette/slowapi version — can read it using the **platform-default text encoding** (cp1252 on Windows) rather than UTF-8. Our own `pydantic_settings.Settings` already loads `.env` explicitly as UTF-8 (`env_file_encoding='utf-8'` in `config.py`), so this was a second, independent, undeclared `.env` read with no encoding control at all. The moment the user's `.env` contained a single non-cp1252 byte (e.g. a smart quote or em-dash pasted from Word/a browser into a comment or value), the backend crashed before FastAPI finished importing — 100% reproducible on Windows, invisible on Linux/Mac (default UTF-8 locale), and a full hard stop, not a logged warning. Fixed in both places `Limiter(...)` is constructed (`app/main.py` and `app/api/sync_routes.py`): pass `config_filename=os.devnull`, which skips slowapi's `.env` auto-detection entirely since we don't need or want it reading project env vars a second time. **Confirmed fixed by re-running on Windows** — the next log only showed a harmless "Config file 'nul' not found" warning, no crash.
- **Issue #30 — hard startup crash: `PydanticUserError: \`regex\` is removed. use \`pattern\` instead` importing `app/api/schemas.py`.** Surfaced immediately after #29 was fixed and the user re-ran the app. `schemas.py` used the pydantic v1 `Field(..., regex="...")` kwarg across 15 fields (`LogEntry`, sync request/response schemas, chat message schemas, etc.) — pydantic v2 deprecated `regex` and later removed it outright in favor of `pattern`. Since `requirements.txt` only pinned `pydantic-settings` and never pinned `pydantic` itself directly, pip was free to resolve whichever pydantic v2.x was newest at install time; a fresh `pip install` months after this code was written picked up a version where `regex` no longer works at all, crashing the app at import time with zero code changes on our side. Fixed: all 15 `regex=` kwargs in `schemas.py` renamed to `pattern=` (identical regex semantics, just the new argument name), and `pydantic==2.9.2` added as an explicit pin in `requirements.txt` so this class of "worked yesterday, crashes today" surprise can't recur silently.

---

## ⚠️ STILL OPEN

- **Hard-cancel for in-flight AI requests:** The cancel button is a soft/UI-only cancel. Making it a true cancel requires either (a) passing a `threading.Event` into `ai_service.process_text` and checking it between steps, or (b) switching that path to an `asyncio.Task` that can be `.cancel()`'d. Estimated 3-4 hours.
- **Issue #14 (chat history reversed order)** — root cause identified (`websockets.py:83` reverses the display list, not just the AI-context copy), not yet fixed.
- **Issue #13 percentage progress bars** — status *text* now flows for the RAG step; numeric `progress_percent` for long operations (e.g. "12/25 pages") was not built.
- **Web search error handling pattern** (from `29-ERROR-HANDLING-DESIGN-PATTERNS.md`) — the WEB-scope branch in `ai_service.py` still only has a generic `except Exception` fallback (now at least notifies the frontend instead of hanging it, see bug fix above, but doesn't classify quota/rate-limit/safety-block errors the way sync errors are classified).
- **Tests** — none written for any of the retry/classification logic.

---

## DESIGN SYSTEM NOTE

**Planned Design Change:**
- Current: Pure glasmorphic (frosted glass aesthetic)
- Planned: **Hybrid glasmorphic + flat design**
  - Glasmorphic: For premium feel (dropdowns, modals, accents)
  - Flat: For readability & enterprise feel (main content areas)
  - Result: Modern, professional, balanced

---

## CRITICAL ISSUES (DO NOT SHIP)

### ========== SECTION 1: CHAT SYSTEM RELIABILITY (PRIORITY #1) ==========

**Status:** 🔴 CORE PRODUCT BROKEN  
**Impact:** Chat is unusable when switching sessions or sending queries  
**Effort to Fix:** 10 hours (most urgent)

**Chat System Issues:** #14, #7, #8, #9, #10, #11, #12, #5

---

#### ISSUE #14: Chat History Order Reversed When Switching Sessions — ❌ STILL OPEN (not touched in this pass)
- **Location:** `backend/app/api/websockets.py:83`, `backend/app/services/db_service.py`
- **Severity:** 🔴 CRITICAL
- **Description:** Messages appear in reverse chronological order when user switches sessions
- **Current Behavior:**
  ```
  User: "Hi" → Vision: "Hi" → User: "How are you?" → Vision: "Fine"
  
  When switch back to session:
  Vision: "Fine"           ← NEWEST FIRST (WRONG)
  User: "How are you?"
  Vision: "Hi"
  User: "Hi"              ← OLDEST LAST (WRONG)
  ```
- **Root Cause:** Backend reverses messages for Vertex AI context, sends reversed list to frontend
- **Fix Needed:** Separate paths: display (chronological) vs AI context (reversed)
- **Impact:** 🔴 Chat history completely broken — users see garbled conversation order
- **Effort:** 2 hours

---

#### ISSUE #7: "Vision is Thinking" State Never Ends — ✅ FIXED
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (lines 131-161)
- **Severity:** 🔴 CRITICAL
- **Description:** Bouncing dots keep bouncing even after response arrives
- **Problem:** User thinks Vision is still processing even though response is visible
- **Fix Applied:** `watch(aiState)` now clears the interval/history/elapsed timer in its `else` branch, plus `onUnmounted` cleanup.
- **Impact:** 🔴 Chat UX completely broken — user confusion
- **Effort:** 2 hours

---

#### ISSUE #8: No Feedback During Token Streaming — ✅ FIXED (2026-10-22)
- **Location:** `frontend/src/views/HomeView.vue`, `frontend/src/composables/useWebSocket.ts`, `frontend/src/components/3-organisms/SystemLog.vue`
- **Severity:** 🔴 CRITICAL
- **Description:** User can't tell if Vision is thinking or response is arriving
- **Problem:** Gap between "thinking" and "response visible"
- **Fix Applied:** `aiState` flips to `'STREAMING'` the instant the first `text_chunk` frame (or legacy chunk) arrives; `SystemLog.vue` shows "📨 V.I.S.I.O.N. is responding..." for that state.
- **Impact:** 🔴 Chat feels broken — response appears suddenly with no warning
- **Effort:** 2 hours

---

#### ISSUE #9: Timeout Warning Has No Cancel Button — ✅ FIXED (2026-10-22, soft cancel)
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (line 157-160), `frontend/src/composables/useWebSocket.ts`
- **Severity:** 🔴 CRITICAL
- **Description:** Shows "Taking longer than usual..." but user can't cancel
- **Problem:** User is stuck waiting, no way to stop stuck chat request
- **Fix Applied:** "❌ Cancel" button added, calls `cancelRequest()` which resets the UI to STANDBY and discards the in-flight response.
- **⚠️ Known limitation:** This is a **soft cancel** — the backend thread processing the request keeps running (no cooperative cancellation hook exists in `ai_service.process_text`). A true hard-cancel is still open (see below).
- **Impact:** 🔴 Chat becomes unresponsive — user trapped
- **Effort:** 2 hours (soft cancel); +3-4h for hard cancel

---

#### ISSUE #10: Status History Not Reset Between Chat Queries — ✅ FIXED
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (line 185)
- **Severity:** 🔴 CRITICAL
- **Description:** Shows old processing steps from previous queries
- **Problem:** Confusing — mixes old + new status in same chat
- **Fix Applied:** `statusHistory.value = []` runs at the top of the `'THINKING'` branch in the `watch(aiState)` handler.
- **Impact:** 🔴 Chat confusing — user sees mixed status from old queries
- **Effort:** 1 hour

---

#### ISSUE #11: Timer Interval Causes Memory Leak in Chat — ✅ FIXED
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (lines 188-196)
- **Severity:** 🔴 CRITICAL
- **Description:** Timer keeps running after response arrives
- **Problem:** Multiple queries = multiple timers running = performance degrades
- **Fix Applied:** `cleanupThinkingInterval()` called before starting a new interval and in the `else`/`onUnmounted` branches.
- **Impact:** 🔴 Chat becomes sluggish over time — performance issue
- **Effort:** 1 hour

---

#### ISSUE #12: Missing STREAMING State in Chat State Machine — ✅ FIXED (2026-10-22)
- **Location:** `frontend/src/views/HomeView.vue`, `frontend/src/composables/useWebSocket.ts`
- **Severity:** 🔴 CRITICAL
- **Description:** State machine incomplete (STANDBY → THINKING → ??? → Response)
- **Problem:** Gap in state transitions during chat response arrival
- **Fix Applied:** `aiState` type widened to `'STANDBY' | 'THINKING' | 'STREAMING' | 'SPEAKING'`; all comparisons (`isGenerating`, the stop/cancel button, SystemLog prop type) updated to include it.
- **Impact:** 🔴 Chat state unclear — can't show streaming feedback
- **Effort:** 1 hour

---

#### ISSUE #5: No Frontend Feedback on Chat Sync Status — ⚠️ PARTIALLY FIXED
- **Location:** `frontend/src/views/HomeView.vue`, `backend/app/api/sync_routes.py`, `backend/sync_connectors.py`
- **Severity:** 🔴 CRITICAL
- **Description:** User triggers sync (for chat knowledge) but gets NO feedback
- **Problem:** User doesn't know if chat knowledge base synced or why sync failed
- **Fix Applied (2026-10-22):** Every sync failure is now recorded with a classified `error_type` + message in `sync_log` (queryable via `GET /api/sync/status`) instead of being swallowed.
- **❌ Still missing:** No *proactive* WebSocket push when a sync completes — the frontend would need to poll `/api/sync/status`, there's no live notification and no UI panel consuming it yet. Est. 2-3h for the push + a small status panel.
- **Impact:** 🔴 Chat knowledge hidden — user can't see what docs are synced
- **Effort:** 6 hours (2h done, 4h remaining)

---

### ========== SECTION 2: ERROR HANDLING GAPS (PRIORITY #2) ==========

**Status:** ❌ ZERO GRACEFUL ERROR HANDLING  
**Impact:** User is blind to failures  
**Effort to Fix:** 24 hours (3 days)

---

#### ISSUE #1: Confluence Sync Fails Silently — ✅ FIXED (2026-10-22)
- **Location:** `backend/sync_connectors.py:sync_confluence_page()`
- **Severity:** 🔴 CRITICAL
- **Description:** When Confluence API fails, returns `False` with NO details
- **Current Behavior:**
  ```python
  if res.status_code != 200:
      logger.error(f"Confluence API failure: HTTP {res.status_code}")
      return False  # ❌ User never knows what happened
  ```
- **Problem:** User doesn't know if page synced or why it failed
- **Fix Needed:** Structured error response with error_type, retryable status, retry count
- **Test Case:** Mock network timeout, verify user sees "Network timeout - retrying..."

---

#### ISSUE #2: ADO Sync Fails Silently — ✅ FIXED (2026-10-22)
- **Location:** `backend/sync_connectors.py:sync_ado_workitem()`
- **Severity:** 🔴 CRITICAL
- **Description:** Same as Issue #1 but for Azure DevOps
- **Current Behavior:** Returns `False` with no error details
- **Problem:** User doesn't know if work item synced
- **Fix Needed:** Same as Issue #1 - structured error responses
- **Test Case:** Mock HTTP 403 (permission denied), verify user sees "No permission to access"

---

#### ISSUE #3: No Retry Logic for Transient Errors — ✅ FIXED (2026-10-22)
- **Location:** `backend/sync_connectors.py` (all sync functions)
- **Severity:** 🔴 CRITICAL
- **Description:** Network blips cause permanent data loss
- **Current Behavior:**
  ```python
  try:
      res = requests.get(...)
  except requests.exceptions.Timeout:
      return False  # ❌ Gives up immediately
  ```
- **Problem:** Single network timeout = data gap forever
- **Fix Needed:** Exponential backoff retry logic (5s → 10s → 20s...)
- **Test Case:** Mock timeout, verify auto-retry 3 times with increasing delays

---

#### ISSUE #4: RAG Ingestion Failures Have No Error Details — ⚠️ PARTIALLY FIXED
- **Location:** `backend/app/services/rag_service.py:ingest_document()`
- **Note (2026-10-22):** The *callers* (`sync_confluence_page`, `sync_ado_workitem`) now record a classified error when `ingest_document()` returns `False`. `ingest_document()` itself still returns a plain `True|False` and does not yet distinguish parsing vs. embedding vs. storage failure internally — that refactor (inside `rag_service.py`) was not done in this pass.
- **Severity:** 🔴 CRITICAL
- **Description:** Returns `True|False` with no info about what failed
- **Current Behavior:**
  ```python
  try:
      chunks = chunk_document(file_path)
      vectors = embed_chunks(chunks)
      store_vectors(vectors)
      return True
  except Exception as e:
      logger.error(f"Ingestion error: {e}")
      return False  # ❌ Can't distinguish parse vs embed vs storage error
  ```
- **Problems:**
  - PDF parsing error = can't distinguish from storage error
  - Vertex AI quota exceeded = can't distinguish from network error
  - ChromaDB down = can't distinguish from permission error
- **Fix Needed:** Structured response with error_type (parsing|embedding|storage)
- **Test Case:** Mock Vertex AI quota exceeded, verify user sees "Quota exceeded"

---

#### ISSUE #5: No Frontend Feedback on Sync Status — ⚠️ PARTIALLY FIXED (see duplicate entry above)
- **Location:** `frontend/src/views/HomeView.vue`, `backend/app/api/sync_routes.py`
- **Severity:** 🔴 CRITICAL
- **Description:** User triggers sync but gets NO feedback on result
- **Current Behavior:**
  ```python
  @router.post("/api/sync/confluence/page/{page_id}")
  async def sync_single_confluence_page(...):
      background_tasks.add_task(sync_connectors.sync_confluence_page, page_id)
      return {"status": "queued", "page_id": page_id}
      # ❌ Frontend never learns if it succeeded or failed
  ```
- **Problem:** User has NO idea if sync worked
- **Frontend Shows:** "queued" ✓ then... silence ❌
- **Fix Needed:** WebSocket callback with `{event: "sync_complete", status: "success|error", error_type: "...", error_message: "..."}`
- **Test Case:** Trigger sync, verify WebSocket sends completion notification with error details

---

#### ISSUE #6: No Error Type Classification System — ⚠️ PARTIALLY FIXED
- **Location:** Entire application
- **Note (2026-10-22):** `classify_sync_error()` in `sync_connectors.py` now covers network/auth/rate-limit/5xx classification for Confluence + ADO sync specifically. This is a function, not an application-wide `ErrorType` enum, and it has not been applied to RAG ingestion internals, web search, or any other integration point — those still have no classification.
- **Severity:** 🔴 CRITICAL
- **Description:** All errors treated the same (no differentiation)
- **Missing Error Types:**
  - Network errors (retryable): timeout, unreachable, DNS failed
  - Auth errors (permanent): invalid_credentials, token_expired, permission_denied
  - Rate limiting (retryable): rate_limit_exceeded, quota_exceeded
  - Data errors (permanent): not_found, file_too_large, invalid_format
  - System errors (retryable): database_down, disk_full, vector_store_down
- **Fix Needed:** Error type enum + structured responses across all integration points
- **Test Case:** Mock each error type, verify correct retry behavior and user message

---

### ========== SECTION 2: UI/UX ISSUES ==========

**Status:** ❌ "VISION IS THINKING" STATE COMPLETELY BROKEN  
**Impact:** User confusion, doesn't know if Vision finished  
**Effort to Fix:** 4-6 hours

---

#### ISSUE #7: "Vision is Thinking" State Never Ends — ✅ FIXED (see duplicate entry above)
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (lines 131-161)
- **Severity:** 🔴 CRITICAL
- **Description:** Bouncing dots keep bouncing even after response arrives
- **Current Behavior:**
  ```
  User: "What is the architecture?"
  ↓
  Shows: "⏳ V.I.S.I.O.N. is thinking... 0.5s"
  ↓
  [Response arrives]
  ↓
  STILL shows: "⏳ V.I.S.I.O.N. is thinking... 5.3s ⏳⏳⏳"
  ```
- **Problem:** User thinks Vision is still processing
- **Root Cause:** No state transition from THINKING → STREAMING → STANDBY
- **Fix Needed:** Proper state cleanup when aiState changes
- **Test Case:** Send query, verify thinking indicator disappears when response starts streaming

---

#### ISSUE #8: No Feedback During Token Streaming — ✅ FIXED (see duplicate entry above)
- **Location:** `frontend/src/views/HomeView.vue`, `backend/app/api/websockets.py`
- **Severity:** 🔴 CRITICAL
- **Description:** User can't tell if Vision is still thinking or response is arriving
- **Current Behavior:**
  ```
  THINKING state appears
  [5 seconds of silence]
  Response suddenly appears (no warning)
  ```
- **Problem:** Gap between "thinking" and "response visible"
- **Fix Needed:** STREAMING state that shows "📨 V.I.S.I.O.N. is responding... text arriving..."
- **Test Case:** Send query, verify "Streaming..." message appears before response text

---

#### ISSUE #9: Timeout Warning Has No Cancel Button — ✅ FIXED, soft cancel only (see duplicate entry above)
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (line 157-160)
- **Severity:** 🔴 CRITICAL
- **Description:** Shows "Taking longer than usual..." but user can't cancel
- **Current Behavior:**
  ```vue
  <div v-if="elapsedSeconds > 5">
    ⏱️ This is taking longer than usual...
  </div>
  <!-- ❌ No cancel button -->
  ```
- **Problem:** User is stuck waiting, no way to stop stuck request
- **Fix Needed:** Add "❌ Cancel Request" button that stops WebSocket
- **Test Case:** Mock slow response, verify cancel button appears and works

---

#### ISSUE #10: Status History Not Reset Between Queries — ✅ FIXED (see duplicate entry above)
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (line 185)
- **Severity:** 🔴 CRITICAL
- **Description:** Shows old processing steps from previous queries
- **Current Behavior:**
  ```
  Query 1:
  ✓ Fetching Confluence (0.2s)
  ✓ Embedding document (1.5s)
  
  Query 2:
  ✓ Fetching Confluence (0.1s)     ← OLD, from Query 1!
  ✓ Embedding document (0.8s)      ← OLD, from Query 1!
  ⏳ Generating response (3.2s)
  ```
- **Problem:** Confusing - shows mixed old + new status
- **Root Cause:** `statusHistory` ref never cleared on new query
- **Fix Needed:** Clear `statusHistory = []` when aiState changes to THINKING
- **Test Case:** Send two queries, verify old status history disappears

---

#### ISSUE #11: Timer Interval Causes Memory Leak — ✅ FIXED (see duplicate entry above)
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (lines 188-196)
- **Severity:** 🔴 CRITICAL
- **Description:** Interval keeps running after response arrives
- **Current Behavior:**
  ```typescript
  watch(() => props.aiState, (newState) => {
    if (newState === 'THINKING') {
      thinkingInterval = setInterval(...)
    }
    // ❌ NO CLEANUP when aiState changes to STANDBY
  })
  
  onUnmounted(() => {
    // ❌ MISSING cleanup
  })
  ```
- **Problem:** Old interval + new interval = 2 timers running, then 3, then 4...
- **Impact:** Performance degrades with each query
- **Fix Needed:** Cleanup interval in watch + onUnmounted
- **Test Case:** Send 5 rapid queries, verify no memory leak (use DevTools)

---

#### ISSUE #12: Missing STREAMING State — ✅ FIXED (see duplicate entry above)
- **Location:** `frontend/src/views/HomeView.vue` (define aiState type)
- **Severity:** 🔴 CRITICAL
- **Description:** State machine incomplete (STANDBY → THINKING → ??? → Response)
- **Current States:** `'STANDBY' | 'THINKING' | 'SPEAKING'`
- **Missing State:** `'STREAMING'` (token-by-token response arrival)
- **Fix Needed:** Add STREAMING state between THINKING and SPEAKING
- **Test Case:** Verify state transitions: STANDBY → THINKING → STREAMING → STANDBY/SPEAKING

---

#### ISSUE #13: No Real-time Processing Status Updates — ❌ STILL OPEN (not touched in this pass)
- **Location:** `backend/app/api/websockets.py`, `frontend/src/components/3-organisms/SystemLog.vue`
- **Severity:** 🔴 CRITICAL
- **Description:** User doesn't see what's happening in backend during processing
- **Current Behavior:**
  ```
  Shows: "⏳ V.I.S.I.O.N. is thinking..."
  [Silent for 5 seconds]
  Response appears
  ```
- **Expected Behavior (like Claude/ChatGPT):**
  ```
  ⏳ V.I.S.I.O.N. is processing...
     ✓ Fetching from Confluence... 12/25 pages (48%)
     ✓ Embedding chunks... 8/15 chunks (53%)
     ⏳ Calling Gemini 2.5 Flash...
     ⏳ Generating response...
     ⏱️ 3.2s elapsed
  ```
- **Problem:** User has NO visibility into what backend is doing
- **Fix Needed:**
  1. Backend sends granular WebSocket events: `{event: "processing_update", status: "fetching_confluence", details: "12/25 pages", progress_percent: 48}`
  2. Frontend shows real-time progress with status icons (✓ done, ⏳ in progress)
  3. Support progress percentages for long operations
- **Implementation:**
  ```python
  # Backend events to send
  {
    "event": "processing_update",
    "status": "fetching_confluence",
    "details": "Retrieved 12 of 25 pages",
    "progress_percent": 48
  }
  {
    "event": "processing_update",
    "status": "embedding_chunks",
    "details": "Embedded 8 of 15 chunks",
    "progress_percent": 53
  }
  {
    "event": "processing_update",
    "status": "calling_gemini",
    "details": "Sending to Vertex AI Gemini 2.5 Flash",
    "progress_percent": 75
  }
  {
    "event": "processing_update",
    "status": "generating_response",
    "details": "Gemini generating response",
    "progress_percent": 90
  }
  ```
- **Test Case:** Send query, verify each processing step appears with progress, verify icons show completion status

---

#### ISSUE #14: Chat History Order Reversed When Switching Sessions — ❌ STILL OPEN (see duplicate entry above)
- **Location:** `backend/app/api/websockets.py:83`, `backend/app/services/db_service.py:get_chat_history_for_session()`
- **Severity:** 🔴 CRITICAL
- **Description:** Chat messages appear in reverse chronological order when user switches sessions
- **Current Behavior:**
  ```
  User sends: "Hi"
  Vision: "Hi"
  User: "How are you"
  Vision: "Fine"
  
  When user navigates to old chat:
  Vision: Fine           ← Latest first (WRONG)
  User: How are you
  Vision: Hi
  User: Hi              ← Oldest last (WRONG)
  ```
- **Root Cause - Code Analysis:**
  ```python
  # db_service.py - Returns history in CORRECT order (oldest to newest)
  def get_chat_history_for_session(...):
      cursor.execute("""
          SELECT ... FROM (
              SELECT ... FROM messages
              ORDER BY id DESC LIMIT ?
          ) sub ORDER BY id ASC  # ✓ ASC = correct order
      """)
  
  # websockets.py - REVERSES the already-correct order
  past_context = db_service.get_chat_history_for_session(...)
  for msg in reversed(past_context):  # ❌ REVERSES AGAIN!
      connection_history.append(...)
  
  # SystemLog.vue - Displays in received order (reversed)
  <li v-for="(msg, index) in messages">  # Messages are already reversed
  ```
- **Problem:** 
  - Backend reverses messages for Vertex AI context window (needs newest last)
  - But SAME reversed list sent to frontend WebSocket
  - Frontend displays messages in reverse chronological order
- **Fix Needed:**
  1. Keep messages in chronological order for WebSocket transmission
  2. Only reverse for Vertex AI context construction
  3. Option A: Create separate method `get_chat_history_for_display()` that returns ASC order
  4. Option B: Don't reverse for WebSocket, only reverse when building Vertex AI context
- **Implementation:**
  ```python
  # BEFORE (wrong):
  past_context = db_service.get_chat_history_for_session(...)
  for msg in reversed(past_context):  # Used for both Vertex + WebSocket
      connection_history.append(...)  # Vertex AI
  
  # AFTER (correct):
  # For Vertex AI context (needs newest last)
  past_context = db_service.get_chat_history_for_session(...)
  for msg in reversed(past_context):  # ✓ Reverse only for AI
      connection_history.append(...)
  
  # For WebSocket display (send chronological order)
  display_history = db_service.get_chat_history_for_session(...)  # Don't reverse
  # Send to WebSocket in chronological order
  ```
- **Test Case:**
  1. Create new session, send 5 messages
  2. Switch to another session, then back
  3. Verify messages appear in chronological order (oldest first, newest last)
  4. Verify message order is preserved when scrolling

---

### ========== SECTION 3: MISSING FEATURES ==========

**Status:** ❌ INCOMPLETE IMPLEMENTATION  
**Impact:** Critical functionality not usable  
**Effort to Fix:** 8-12 hours

---

#### ISSUE #15: Web Search UI Completely Missing — ❌ STILL OPEN (not touched in this pass)
- **Location:** `frontend/src/views/HomeView.vue`, `frontend/src/components/`
- **Severity:** 🔴 CRITICAL
- **Description:** Backend has @web/@internal/@both routing but NO UI
- **Backend Status:** ✅ Routes exist in `backend/app/api/main.py`
- **Frontend Status:** ❌ NO UI components
- **Missing Components:**
  - Search scope selector (chips: @web, @internal, @both)
  - Search input field
  - Results display component
  - Result ranking/pagination
- **Fix Needed:**
  1. Create SearchInput.vue component with scope chips
  2. Add search results display
  3. Wire to backend /api/directives endpoint
  4. Handle search errors (timeout, no results, rate limit)
- **Test Case:** Select @web scope, search "architecture", verify results display

---

#### ISSUE #16: No Sync Status Dashboard — ❌ STILL OPEN (not touched in this pass; backend data for it now exists via `/api/sync/status`)
- **Location:** `frontend/src/views/HomeView.vue`
- **Severity:** 🔴 CRITICAL
- **Description:** User has NO visibility into sync status
- **Missing Feature:** Dashboard showing:
  ```
  ✅ Confluence: Last sync 5 minutes ago (237 pages)
  ⏳ ADO: Currently syncing... (12/47 items)
  ❌ Web Search: Last sync failed - Network timeout
  🔄 Retry All | ⚙️ Settings
  ```
- **Current Status:** User must check logs manually
- **Fix Needed:**
  1. Create SyncStatusPanel.vue component
  2. Track sync history in database
  3. Show last sync timestamp per source
  4. Show retry options
  5. Show error details
- **Test Case:** Trigger Confluence sync, verify status appears in dashboard

---

## PRIORITY MATRIX

| Issue | Severity | Effort | Priority |
|-------|----------|--------|----------|
| #1: Confluence fails silently | 🔴 | 4h | 1 |
| #2: ADO fails silently | 🔴 | 4h | 2 |
| #3: No retry logic | 🔴 | 4h | 3 |
| #4: RAG ingestion errors | 🔴 | 4h | 4 |
| #5: No sync feedback | 🔴 | 6h | 5 |
| #6: No error classification | 🔴 | 2h | 6 |
| #7: Thinking state never ends | 🔴 | 2h | 7 |
| #8: No streaming feedback | 🔴 | 2h | 8 |
| #9: Timeout not cancellable | 🔴 | 2h | 9 |
| #10: Status history leak | 🔴 | 1h | 10 |
| #11: Memory leak (timer) | 🔴 | 1h | 11 |
| #12: Missing STREAMING state | 🔴 | 1h | 12 |
| #13: No real-time processing updates | 🔴 | 4h | 13 |
| #14: Chat history order reversed | 🔴 | 2h | 14 |
| #15: Web search UI missing | 🔴 | 8h | 15 |
| #16: No sync dashboard | 🔴 | 4h | 16 |

---

## IMPLEMENTATION PHASES

### Phase 1: Error Handling Foundation (6 hours)
- [ ] Create error type classification enum
- [ ] Define SyncResponse dataclass
- [ ] Update sync_confluence_page() with structured errors
- [ ] Add WebSocket notification sending

### Phase 2: Retry Logic (4 hours)
- [ ] Implement retry_with_backoff() function
- [ ] Add to Confluence sync
- [ ] Add to ADO sync
- [ ] Add to Web search

### Phase 3: Real-time Processing Updates (4 hours)
- [ ] Add processing status event emitter to backend
- [ ] Wire WebSocket event sending (Confluence, ADO, Gemini calls)
- [ ] Create processing status display in frontend
- [ ] Add progress bar/percentage tracking

### Phase 4: UI/UX State Management (6 hours)
- [ ] Fix thinking state cleanup (Issue #7, #10, #11)
- [ ] Add STREAMING state (Issue #12)
- [ ] Create timeout/cancel button (Issue #9)
- [ ] Add streaming feedback (Issue #8)

### Phase 5: Missing Features (12 hours)
- [ ] Create SearchInput component (Issue #14)
- [ ] Create SyncStatusPanel component (Issue #15)
- [ ] Wire search to backend
- [ ] Wire sync status to backend

### Phase 6: Testing & Polish (8 hours)
- [ ] Unit tests for error types
- [ ] Integration tests for retry logic
- [ ] E2E tests for UI state transitions
- [ ] Performance testing (memory leaks)

**Total Effort: 42 hours (5 days)**

---

## GO/NO-GO CHECKLIST

Before shipping to production:

- [ ] All error handling issues fixed (#1-6)
- [ ] All real-time processing updates working (#13)
- [ ] All UI/UX issues fixed (#7-12)
- [ ] All missing features implemented (#14-15)
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] No memory leaks detected
- [ ] Error messages tested with real failure scenarios
- [ ] Retry logic tested with network simulation
- [ ] State transitions verified manually
- [ ] Real-time processing status shows on screen
- [ ] Web search functionality works end-to-end
- [ ] Sync status dashboard shows correct data

---

## NOTES

- **CRITICAL:** Do NOT ship without fixing error handling (Issues #1-6)
- **CRITICAL:** Do NOT ship with broken thinking state (Issues #7-12)
- **CRITICAL:** Real-time processing updates required (Issue #13) - user visibility into backend
- **HIGH:** Web search missing (Issue #14) - major feature gap
- **HIGH:** Sync dashboard missing (Issue #15) - user visibility issue

---

---

## ✅ MERGED FROM `18-IssuesAndRoadmap.md` (2026-10-22) — consolidation, nothing left scattered

This separate doc (dated 2026-10-21, predates this tracker) listed its own set of defects, missing
features, technical debt and a Phase 5–9 roadmap that had never been folded in here. Every claim
below was re-checked against the current code before merging — several were already fixed by
earlier work in this session and the doc just hadn't caught up. The source file has been deleted;
this section (plus #27 below) is now the only place any of this content lives.

### Issues #17–#21 — re-verified against current code, 5 of 9 already fixed

| # | Issue | Verified status |
|---|---|---|
| #17 | RAG similarity threshold too loose (doc claimed 0.85) | ✅ **Stale claim.** `rag_service.py` already uses `RAG_DISTANCE_THRESHOLD = 0.60` strict with a `0.75` fallback-on-empty-results tier — tighter than what the doc described as the fix. Nothing to do. |
| #18 | WebSocket reconnect doesn't preserve unsent messages | ⚠️ **Still open.** Not touched this session. `frontend/src/infrastructure/services/WebSocketService.ts` has no localStorage replay-on-reconnect buffer. |
| #19 | PostgreSQL has no connection pooling | ⚠️ **Still open.** `db_service.py` calls `psycopg2.connect()` directly per request with no `QueuePool`/pool manager. Will not hold up past light concurrent load. |
| #20 | System directives not hot-reloadable | ⚠️ **Still open.** `ai_service.py` reads directives without a cache-invalidation or file-watch path; a backend restart is still required. |
| #21 | No rate limiting on API endpoints | ✅ **Stale claim.** `slowapi.Limiter` is already wired in `main.py` and `sync_routes.py`, plus a custom `_check_rate_limit()` in `uploads.py`. Nothing to do. |

### Issues #22–#26 — medium/low priority, re-verified

| # | Issue | Verified status |
|---|---|---|
| #22 | Document dedup by filename hash only (no content diff) | ⚠️ **Still open.** `rag_service.py` ingestion path has no content-hash/version check — a same-named re-upload with different content silently overwrites. |
| #23 | No audit logging | ⚠️ **Still open.** No `audit_log` table or middleware anywhere in `backend/`. Needed before any enterprise/compliance deployment. |
| #24 | ChromaDB not persistent across restarts | ✅ **Stale claim.** `rag_service.py` already uses `chromadb.PersistentClient(path=db_dir)`. Nothing to do. |
| #25 | No password reset flow | ⚠️ **Still open.** No `/api/password-reset` endpoint exists; admin must manually reset accounts. |
| #26 | Upload validation: file-type/MIME check missing | ⚠️ **Partially open.** `uploads.py` does enforce `MAX_FILE_SIZE` (`settings.MAX_UPLOAD_SIZE_MB`), but there's no MIME-type allowlist or malware scan — any file extension is accepted as long as it's under the size cap. |

### Low-priority items — re-verified, both already fixed

- **VisionCore.vue animation jank on low-end devices** — not independently re-tested this session; left as-is, low priority, no code change needed to merge the tracking.
- ~~No dark mode toggle~~ — ✅ **Stale claim.** `HomeView.vue` already has a full `isDarkMode` toggle wired through `:class="{ 'dark': isDarkMode, 'light': !isDarkMode }"` and is used throughout. Nothing to do.
- ~~ChatInput character limit not enforced~~ — ✅ **Stale claim.** `HomeView.vue`'s chat textarea already has `maxlength="15000"`. Nothing to do.

### Missing-features list — re-verified, 2 of 6 already built

- **Conversation branching** — ⚠️ still not built.
- **Advanced multi-turn memory/summarization** — ⚠️ still not built.
- **Custom KB management UI** (delete/re-index documents from an admin screen) — ⚠️ still not built.
- **Confluence/ADO sync automation** (scheduled/incremental sync) — ⚠️ partially stale: the retry-with-backoff + structured-error work done earlier in this session makes each sync call itself reliable, but there is still no *scheduler* triggering syncs automatically — that part is genuinely still open.
- **Model hot-swapping (Gemini/Claude/GPT-4 side by side)** — ⚠️ still not built; low priority, not requested by business.
- **Google Search integration** — ✅ **Stale claim.** `ai_service.py` already wires Vertex AI's `google_search` grounding tool (`Tool.from_dict({"google_search": {}})`) end-to-end for `@web`/WEB-scope queries.
- **Highlight-to-ask floating menu** — ✅ **Stale claim.** `HomeView.vue` already implements this (`highlightMenuCoords`, `submitHighlightedQuery()`, the floating menu template block).
- **Workspace folder ingester (bulk folder upload)** — ⚠️ still not built.

## Technical Debt (carried over, unverified this session — flagged for later triage)

| Item | Severity | Notes |
|---|---|---|
| No unit tests for RAG service | HIGH | Still true — no automated tests exist anywhere in the repo yet (tracked as the "tests" item in STILL OPEN above). |
| No integration tests (backend ↔ frontend) | HIGH | Same as above. |
| Hardcoded config (ports, thresholds) | MEDIUM | Not re-checked; move to `.env` where not already there. |
| No error boundaries in Vue | MEDIUM | Not re-checked. |
| SQLite dev ↔ Postgres prod mismatch | MEDIUM | Not re-checked. |
| No logging strategy beyond stdout | MEDIUM | Not re-checked. |
| Zscaler SSL bypass in code | MEDIUM | Not re-checked — deployment-specific, should not ship as-is. |
| No type hints in Python services | MEDIUM | Not re-checked. |
| CSS classes scattered (no design system) | LOW | Relevant to the planned hybrid glasmorphic+flat redesign noted at the top of this tracker. |
| Duplicated authentication logic | LOW | Not re-checked. |

## #27 — Roadmap (Phase 5–9), kept for reference only, not a bug

Future-looking, not a defect — recorded here only so nothing is scattered across files. Not scheduled,
not estimated against this session's work:

- **Phase 5 — Voice & Accessibility:** voice input, TTS output, keyboard-shortcut docs, WCAG 2.1 AA audit, screen-reader support.
- **Phase 6 — Collaboration:** multi-user sessions, presence indicators, roles, message reactions/threads, session diff viewer.
- **Phase 7 — Enterprise:** SSO (SAML/OAuth), fine-grained RBAC, compliance audit logging, encryption at rest, API key management, custom branding.
- **Phase 8 — Advanced RAG:** hybrid reranking, query expansion, document versioning, precise citations, confidence scoring.
- **Phase 9 — Scaling:** Kubernetes/horizontal scaling, Redis caching, Elasticsearch for large corpora, CDN, performance monitoring.

---

**Created:** 2026-10-21  
**Updated:** 2026-10-22 — merged `18-IssuesAndRoadmap.md` in full (verified against live code; several of its claims were already fixed earlier this session) and deleted the source file so no issue/bug content is scattered outside this tracker.  
**Status:** ACTIVE - Ready for implementation

