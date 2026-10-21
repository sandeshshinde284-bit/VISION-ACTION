# V.I.S.I.O.N. - MASTER ISSUES & BUGS TRACKER

**Date:** 2026-10-21  
**Status:** CRITICAL PRODUCTION ISSUES  
**Version:** 1.0

---

## SUMMARY

Total Issues Found: **16 CRITICAL + HIGH PRIORITY BUGS**

| Priority | Category | Count | Status |
|----------|----------|-------|--------|
| 🔴 MUST FIX | Chat System | 5 issues | BLOCKS EVERYTHING |
| 🔴 MUST FIX | Error Handling | 6 issues | User blind to failures |
| 🟠 SHOULD FIX | Real-time Feedback | 1 issue | User doesn't see progress |
| 🟡 NICE TO HAVE | Missing Features | 2 issues | Incomplete product |
| 🟡 NICE TO HAVE | Design System | — | Glasmorphic → Flat/Hybrid |
| **TOTAL** | — | **16** | **DO NOT SHIP** |

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

#### ISSUE #14: Chat History Order Reversed When Switching Sessions
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

#### ISSUE #7: "Vision is Thinking" State Never Ends
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (lines 131-161)
- **Severity:** 🔴 CRITICAL
- **Description:** Bouncing dots keep bouncing even after response arrives
- **Problem:** User thinks Vision is still processing even though response is visible
- **Fix Needed:** Proper state cleanup when aiState changes
- **Impact:** 🔴 Chat UX completely broken — user confusion
- **Effort:** 2 hours

---

#### ISSUE #8: No Feedback During Token Streaming
- **Location:** `frontend/src/views/HomeView.vue`, `backend/app/api/websockets.py`
- **Severity:** 🔴 CRITICAL
- **Description:** User can't tell if Vision is thinking or response is arriving
- **Problem:** Gap between "thinking" and "response visible"
- **Fix Needed:** STREAMING state showing "📨 V.I.S.I.O.N. is responding..."
- **Impact:** 🔴 Chat feels broken — response appears suddenly with no warning
- **Effort:** 2 hours

---

#### ISSUE #9: Timeout Warning Has No Cancel Button
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (line 157-160)
- **Severity:** 🔴 CRITICAL
- **Description:** Shows "Taking longer than usual..." but user can't cancel
- **Problem:** User is stuck waiting, no way to stop stuck chat request
- **Fix Needed:** Add "❌ Cancel Request" button
- **Impact:** 🔴 Chat becomes unresponsive — user trapped
- **Effort:** 2 hours

---

#### ISSUE #10: Status History Not Reset Between Chat Queries
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (line 185)
- **Severity:** 🔴 CRITICAL
- **Description:** Shows old processing steps from previous queries
- **Problem:** Confusing — mixes old + new status in same chat
- **Fix Needed:** Clear history when aiState changes to THINKING
- **Impact:** 🔴 Chat confusing — user sees mixed status from old queries
- **Effort:** 1 hour

---

#### ISSUE #11: Timer Interval Causes Memory Leak in Chat
- **Location:** `frontend/src/components/3-organisms/SystemLog.vue` (lines 188-196)
- **Severity:** 🔴 CRITICAL
- **Description:** Timer keeps running after response arrives
- **Problem:** Multiple queries = multiple timers running = performance degrades
- **Fix Needed:** Cleanup interval in watch + onUnmounted
- **Impact:** 🔴 Chat becomes sluggish over time — performance issue
- **Effort:** 1 hour

---

#### ISSUE #12: Missing STREAMING State in Chat State Machine
- **Location:** `frontend/src/views/HomeView.vue`
- **Severity:** 🔴 CRITICAL
- **Description:** State machine incomplete (STANDBY → THINKING → ??? → Response)
- **Problem:** Gap in state transitions during chat response arrival
- **Fix Needed:** Add STREAMING state between THINKING and SPEAKING
- **Impact:** 🔴 Chat state unclear — can't show streaming feedback
- **Effort:** 1 hour

---

#### ISSUE #5: No Frontend Feedback on Chat Sync Status
- **Location:** `frontend/src/views/HomeView.vue`, `backend/app/api/sync_routes.py`
- **Severity:** 🔴 CRITICAL
- **Description:** User triggers sync (for chat knowledge) but gets NO feedback
- **Problem:** User doesn't know if chat knowledge base synced or why sync failed
- **Fix Needed:** WebSocket callback with sync completion + error details
- **Impact:** 🔴 Chat knowledge hidden — user can't see what docs are synced
- **Effort:** 6 hours

---

### ========== SECTION 2: ERROR HANDLING GAPS (PRIORITY #2) ==========

**Status:** ❌ ZERO GRACEFUL ERROR HANDLING  
**Impact:** User is blind to failures  
**Effort to Fix:** 24 hours (3 days)

---

#### ISSUE #1: Confluence Sync Fails Silently
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

#### ISSUE #2: ADO Sync Fails Silently
- **Location:** `backend/sync_connectors.py:sync_ado_workitem()`
- **Severity:** 🔴 CRITICAL
- **Description:** Same as Issue #1 but for Azure DevOps
- **Current Behavior:** Returns `False` with no error details
- **Problem:** User doesn't know if work item synced
- **Fix Needed:** Same as Issue #1 - structured error responses
- **Test Case:** Mock HTTP 403 (permission denied), verify user sees "No permission to access"

---

#### ISSUE #3: No Retry Logic for Transient Errors
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

#### ISSUE #4: RAG Ingestion Failures Have No Error Details
- **Location:** `backend/app/services/rag_service.py:ingest_document()`
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

#### ISSUE #5: No Frontend Feedback on Sync Status
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

#### ISSUE #6: No Error Type Classification System
- **Location:** Entire application
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

#### ISSUE #7: "Vision is Thinking" State Never Ends
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

#### ISSUE #8: No Feedback During Token Streaming
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

#### ISSUE #9: Timeout Warning Has No Cancel Button
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

#### ISSUE #10: Status History Not Reset Between Queries
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

#### ISSUE #11: Timer Interval Causes Memory Leak
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

#### ISSUE #12: Missing STREAMING State
- **Location:** `frontend/src/views/HomeView.vue` (define aiState type)
- **Severity:** 🔴 CRITICAL
- **Description:** State machine incomplete (STANDBY → THINKING → ??? → Response)
- **Current States:** `'STANDBY' | 'THINKING' | 'SPEAKING'`
- **Missing State:** `'STREAMING'` (token-by-token response arrival)
- **Fix Needed:** Add STREAMING state between THINKING and SPEAKING
- **Test Case:** Verify state transitions: STANDBY → THINKING → STREAMING → STANDBY/SPEAKING

---

#### ISSUE #13: No Real-time Processing Status Updates
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

#### ISSUE #14: Chat History Order Reversed When Switching Sessions
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

#### ISSUE #15: Web Search UI Completely Missing
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

#### ISSUE #16: No Sync Status Dashboard
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

**Created:** 2026-10-21  
**Updated:** —  
**Status:** ACTIVE - Ready for implementation

