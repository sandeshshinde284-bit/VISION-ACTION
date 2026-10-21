# V.I.S.I.O.N. Issues, Gaps & Roadmap
**Date:** Oct 21, 2026 | **Version:** 1.0 | **Status:** Verified

Known defects, missing features, technical debt, and Phase 5+ roadmap.

---

## 1. KNOWN ISSUES & DEFECTS

### HIGH PRIORITY

#### 1.1 RAG Similarity Threshold Too Loose (0.85)
- **Issue:** ChromaDB cosine similarity threshold of `≤ 0.85` retrieves irrelevant documents
- **Impact:** RAG context polluted with off-topic passages; LLM confused
- **Location:** `backend/app/services/rag_service.py:48`
- **Fix:** Lower threshold to `0.70` or implement adaptive tuning
- **Status:** ⏳ Pending testing in production

#### 1.2 WebSocket Auto-Reconnect Doesn't Preserve Unsent Messages
- **Issue:** When connection drops, buffered messages lost if user clicks away
- **Impact:** User message loss if network hiccup during submission
- **Location:** `frontend/src/infrastructure/services/WebSocketService.ts:85`
- **Fix:** Persist pending messages to `localStorage`; replay on reconnect
- **Status:** ⏳ Medium effort, low frequency

#### 1.3 PostgreSQL Connection Pooling Not Configured
- **Issue:** Backend spawns new DB connection per request (no pool)
- **Impact:** Will fail under load (>50 concurrent users)
- **Location:** `backend/app/services/db_service.py:12`
- **Fix:** Add `sqlalchemy.pool.QueuePool(max_overflow=20)`
- **Status:** ⏳ Required for production

#### 1.4 System Directives Not Reloadable Without Restart
- **Issue:** Updating directives via UI requires manual backend restart
- **Impact:** Admin can't hot-reload AI personality without downtime
- **Location:** `backend/app/services/ai_service.py:40`
- **Fix:** Implement cache invalidation + file watch
- **Status:** ⏳ Low priority (workaround: restart)

#### 1.5 No Rate Limiting on API Endpoints
- **Issue:** No protection against brute-force login, API abuse
- **Impact:** Vulnerable to DDoS, credential attacks
- **Location:** `backend/app/main.py:15`
- **Fix:** Add `slowapi` middleware with per-IP rate limits
- **Status:** ⏳ Required for production security

### MEDIUM PRIORITY

#### 2.1 Document Deduplication by Hash Only (No Content Diff)
- **Issue:** If same filename with different content uploaded, treated as same doc
- **Impact:** Old versions overwrite new versions silently
- **Location:** `backend/app/services/rag_service.py:120`
- **Fix:** Include content hash + version tracking in metadata
- **Status:** ⏳ Low frequency issue

#### 2.2 No Audit Logging (Compliance Gap)
- **Issue:** No record of who accessed/modified what data
- **Impact:** Failed compliance audits, no forensics trail
- **Location:** `backend/app/main.py` (missing)
- **Fix:** Add audit log table + middleware to track user actions
- **Status:** ⏳ Required for enterprise deployment

#### 2.3 ChromaDB Not Persistent Across Restarts
- **Issue:** Vector embeddings stored in memory; lost on restart
- **Impact:** Users must re-upload documents after backend restart
- **Location:** `backend/app/services/rag_service.py:35`
- **Fix:** Configure ChromaDB with persistent directory: `ChromaDB(persist_directory="/data/chroma")`
- **Status:** ⏳ Easy fix, high impact

#### 2.4 Password Reset Flow Missing
- **Issue:** No way for users to recover forgotten passwords
- **Impact:** Locked accounts; admin must manually reset
- **Location:** `backend/app/main.py` (missing)
- **Fix:** Add `/api/password-reset` endpoint + email verification
- **Status:** ⏳ Low priority (small user base)

#### 2.5 No Input Validation on RAG Document Upload
- **Issue:** No file type validation; accepts any file type
- **Impact:** ZIP bombs, malicious documents may crash server
- **Location:** `backend/app/main.py:120`
- **Fix:** Validate MIME type, file size (`>15MB`), scan with virus engine
- **Status:** ⏳ Medium priority

### LOW PRIORITY

#### 3.1 VisionCore.vue Animation Performance
- **Issue:** Concentric rings animation jerks on low-end devices
- **Impact:** Poor UX on mobile/Chromebooks
- **Location:** `frontend/src/components/2-molecules/VisionCore.vue:24`
- **Fix:** Use `will-change: transform` CSS; consider SVG optimization
- **Status:** ⏳ Polish issue

#### 3.2 No Dark Mode Toggle
- **Issue:** UI hard-coded to dark theme; no light mode option
- **Impact:** Users prefer light mode during daytime
- **Location:** `frontend/src/App.vue` (missing)
- **Fix:** Add theme toggle + `prefers-color-scheme` media query
- **Status:** ⏳ Nice-to-have

#### 3.3 ChatInput Character Limit Not Enforced
- **Issue:** Users can paste 100KB+ messages; backend accepts
- **Impact:** Gemini API rejects; poor UX
- **Location:** `frontend/src/components/ChatInput.vue:45`
- **Fix:** Add max-length validation (recommend 8000 chars)
- **Status:** ⏳ Low impact (rare edge case)

---

## 2. MISSING FEATURES

### Phase 3 (Never Implemented)
These were planned but never built:

#### 3.1 Conversation Branching
- **Description:** Allow users to "branch" a conversation and explore alternative responses
- **Example:** User asks Q1 → AI gives A1 → User clicks "Try Different Answer" → Branches conversation
- **Effort:** Medium (UI + backend state management)
- **Priority:** Medium (valuable feature)

#### 3.2 Advanced Message Memory
- **Description:** Multi-turn context with summarization; remember past conversation summaries
- **Example:** User: "I mentioned my favorite tool earlier" → AI recalls from earlier messages
- **Effort:** High (requires context summarization, chunking)
- **Priority:** High (core conversational AI feature)

#### 3.3 Custom Knowledge Base Management UI
- **Description:** Admin UI to manage uploaded documents (delete, versions, search index)
- **Example:** Admin dashboard showing all RAG documents, delete buttons, re-index controls
- **Effort:** Medium (CRUD UI + backend)
- **Priority:** Medium (needed for document maintenance)

### Phase 4 (Partial)

#### 4.1 Confluence Sync (Incomplete)
- **Status:** Routes exist (`/api/sync/confluence`) but automation not implemented
- **What's Missing:** 
  - Scheduled sync (every 6 hours?)
  - Incremental sync (only changed docs)
  - Conflict resolution (local vs. Confluence edits)
- **Effort:** Medium
- **Priority:** High (Worldline uses Confluence heavily)

#### 4.2 Azure DevOps Sync (Incomplete)
- **Status:** Routes exist (`/api/sync/ado`) but automation not implemented
- **What's Missing:**
  - Fetch work items + descriptions
  - Sync comments + discussions
  - Link to RAG documents
- **Effort:** Medium
- **Priority:** High (Worldline uses ADO for project tracking)

#### 4.3 Model Hot-Swapping (Not Implemented)
- **Status:** Docs claim it; code locked to Gemini 2.5 Flash only
- **What Would Be Needed:**
  - Abstract LLM interface (currently hardcoded Vertex AI calls)
  - Support for Gemini/Claude/GPT-4 side-by-side
  - User preference settings for model selection
- **Effort:** High (refactoring entire ai_service.py)
- **Priority:** Low (business hasn't requested; not standard feature)

#### 4.4 Google Search Integration (Not Implemented)
- **Status:** Intent routing claims `@web` searches Google; not integrated
- **What Would Be Needed:**
  - Google Custom Search API or SerpAPI integration
  - Snippet extraction from search results
  - Citation attribution
- **Effort:** Medium
- **Priority:** Medium (valuable for current-event questions)

#### 4.5 Highlight-to-Ask Floating Menu (Not Implemented)
- **Status:** Docs claim this feature; not found in code
- **What Would Be Needed:**
  - Text selection detection (mouseup + selection listener)
  - Floating "Ask about this" menu
  - Send selection + context to RAG
- **Effort:** Low (50 LOC)
- **Priority:** Low (nice-to-have)

#### 4.6 Workspace Folder Ingester (Not Implemented)
- **Status:** Docs claim bulk folder upload; not found in code
- **What Would Be Needed:**
  - File picker for folders (using WebFile API)
  - Batch upload with progress bar
  - Auto-chunk all files
- **Effort:** Medium
- **Priority:** Medium (faster document onboarding)

---

## 3. TECHNICAL DEBT

| Item | Severity | Effort | Notes |
|------|----------|--------|-------|
| No unit tests for RAG service | HIGH | Medium | Critical for reliability |
| No integration tests (backend ↔ frontend) | HIGH | High | Can't verify end-to-end flows |
| Hardcoded config (ports, thresholds) | MEDIUM | Low | Move to .env |
| No error boundaries in Vue | MEDIUM | Low | Crashes affect entire app |
| SQLite dev ↔ Postgres prod mismatch | MEDIUM | High | Data type inconsistencies |
| No logging strategy (stdout only) | MEDIUM | Medium | Can't debug production issues |
| Zscaler SSL bypass in code | MEDIUM | Medium | Should be deployment-specific |
| No type hints in Python services | MEDIUM | Low | Makes refactoring risky |
| CSS classes scattered (no design system) | LOW | High | Visual consistency issues |
| Duplicated authentication logic | LOW | Low | Extract to middleware |

---

## 4. PHASE 5+ ROADMAP

### Phase 5: Voice & Accessibility
**Timeline:** Q1 2027 | **Effort:** 2 weeks | **Priority:** Medium

- [ ] Voice input (Web Audio API)
- [ ] Text-to-speech output (Web Speech API or Google Cloud TTS)
- [ ] Keyboard shortcuts documentation
- [ ] WCAG 2.1 AA accessibility audit
- [ ] Screen reader compatibility

### Phase 6: Collaboration
**Timeline:** Q2 2027 | **Effort:** 3 weeks | **Priority:** Medium

- [ ] Multi-user sessions (shared chat)
- [ ] Real-time presence indicators
- [ ] User roles (viewer, editor, admin)
- [ ] Message reactions & threaded replies
- [ ] Session history with diff viewer

### Phase 7: Enterprise Features
**Timeline:** Q2-Q3 2027 | **Effort:** 4 weeks | **Priority:** High

- [ ] SAML/OAuth integration (SSO)
- [ ] Role-based access control (RBAC) with fine-grained permissions
- [ ] Audit logging (compliance: SOC2, ISO 27001)
- [ ] Data encryption at rest (AES-256)
- [ ] API key management for integrations
- [ ] Custom branding (logos, colors)

### Phase 8: Advanced RAG
**Timeline:** Q3 2027 | **Effort:** 3 weeks | **Priority:** High

- [ ] Reranking (semantic + keyword hybrid)
- [ ] Query expansion (synonyms, related terms)
- [ ] Document versioning (track changes)
- [ ] Citation precision (page numbers, line numbers)
- [ ] Confidence scoring (tell user when uncertain)

### Phase 9: Scaling & Performance
**Timeline:** Q3-Q4 2027 | **Effort:** 4 weeks | **Priority:** High

- [ ] Horizontal scaling (Kubernetes, auto-scaling groups)
- [ ] Caching layer (Redis for responses, embeddings)
- [ ] Search optimization (Elasticsearch for large corpora)
- [ ] CDN for frontend assets
- [ ] Performance monitoring (Datadog, New Relic)

---

## 5. DEFECT PRIORITY MATRIX

```
        Quick to Fix          Hard to Fix
Quick   3.1 (animation)       1.3 (pooling)
Win     3.3 (char limit)      1.5 (rate limiting)
        2.2 (audit logging)   2.3 (ChromaDB persist)

High    1.1 (threshold)       1.4 (directives reload)
Impact  1.2 (reconnect)       2.1 (dedup)
        2.4 (pwd reset)       2.5 (file validation)
```

**Recommended Fix Order (by ROI):**
1. ✅ 2.3 (ChromaDB persist) — Easy, high impact
2. ✅ 1.5 (Rate limiting) — Required for prod
3. ✅ 1.3 (Pooling) — Required for prod
4. ⏳ 1.1 (Threshold tuning) — Test in staging first
5. ⏳ 1.2 (Reconnect messages) — Medium effort, good UX
6. ⏳ 2.2 (Audit logging) — Compliance requirement

---

## 6. SUMMARY TABLE

| Phase | Status | Features | Gaps | Priority |
|-------|--------|----------|------|----------|
| 1 | ✅ Complete | Auth, chat, directives, sessions | None | — |
| 1.5 | ✅ Complete | Persistence, reconnect, telemetry | None | — |
| 2 | ✅ Complete | RAG, upload, semantic search | None | — |
| 4 | ⚠️ Partial | Intent routing, @shortcuts | Search integration, sync automation | High |
| 3 | ❌ Missing | (Never built) | Branching, memory, doc mgmt | Medium |
| 5 | 🗺️ Backlog | Voice, accessibility, collaboration | All | Q1+ 2027 |

**Production Readiness:** 70% (Phases 1, 1.5, 2 solid; Phase 4 partial; Phase 3 missing; defects need fixing)
