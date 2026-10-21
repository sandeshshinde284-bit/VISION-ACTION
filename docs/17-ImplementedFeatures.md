# V.I.S.I.O.N. Suite: Implemented Features & Architecture Log

This document serves as the comprehensive master list of all enterprise-grade features, security mechanisms, and architectural optimizations currently active within the V.I.S.I.O.N. Suite.

---

## 🧠 1. Core AI & LLM Orchestration
*   **Dual-Model Hot-Swapping:** Natively runs on **Gemini 2.5 Flash** (for high-speed, cost-effective RAG), but dynamically hot-swaps to **Gemini 2.5 Pro** if deep reasoning is requested by the user.
*   **Predictive Semantic Routing (The `AUTO` Brain):** Automatically classifies user intent in milliseconds to seamlessly route the query to `CHAT` (social), `WEB` (Google Grounding), `INTERNAL` (RAG Database), or `BOTH` (Hybrid).
*   **Live Google Search Grounding:** Bypasses internal databases on general knowledge queries to fetch real-time public data from the internet.
*   **Phase 5 Synthesis Guardrails (Anti-Copy):** Wraps RAG data in strict XML boundaries (`[SOURCE CONTEXT - SYNTHESIZE ONLY]`) and mathematically audits the AI's response to prevent verbatim copy-pasting and robotic AI templates.
*   **Autonomous ASCII-to-Mermaid Converter:** Detects crude ASCII flowcharts in documentation and automatically translates them into gorgeous, interactive Mermaid.js vector graphics.

## 📚 2. Advanced Enterprise RAG (Retrieval-Augmented Generation)
*   **Parent-Document Collapsing (ADR-004):** Instead of feeding the AI fragmented 1,000-character chunks, the system finds the semantic match in ChromaDB/pgvector and pulls the **entire, unbroken specification document** from SQLite to give the AI 360-degree context.
*   **Safe Autonomous Link Following:** Scans retrieved Confluence pages for links to other pages and fetches them automatically. Protected by a cycle-detector (`visited_docs`), a depth cap (`MAX_DEPTH=2`), and an instant semantic relevance check to prevent context blowouts.
*   **Semantic Recursive Chunking:** Splices documents intelligently by paragraphs (`\n\n`) and sentences, rather than blindly chopping words in half, ensuring Markdown tables and code blocks remain intact.
*   **Data Freshness Tracking:** Injects a live `[Last Updated: 2h ago]` timestamp into the AI's prompt so it knows exactly how stale the internal data is.
*   **RAG Observability API:** Features a `/api/debug/rag-search` endpoint to instantly reveal the mathematical Cosine Distances of matched documents for easy threshold tuning.

## 🔒 3. Enterprise Security & Authentication
*   **True Database-Driven Auth:** Completely eliminated hardcoded frontend tokens. Uses Python's `secrets` module to generate cryptographically secure 64-character session tokens saved to a PostgreSQL `user_sessions` table.
*   **PostgreSQL Fail-Open Architecture:** If the Google Cloud PostgreSQL database goes offline, the backend catches the failure and dynamically hot-swaps to the local SQLite database to keep the API 100% online.
*   **Log Secrets Scrubber:** Aggressive regex interceptors scan all API tracebacks to mask Personal Access Tokens (PATs) and emails (`[TOKEN_REDACTED]`) before they hit the disk logs.
*   **Fail-Fast Startup:** Cloud Run deployments will intentionally refuse to boot if environmental credentials (like `CONFLUENCE_PAT`) are missing, preventing silent data failures.

## ⚙️ 4. Azure DevOps (ADO) & Confluence Integration
*   **Concurrent "Phantom Pre-Flight":** Uses a `ThreadPoolExecutor` to fetch live ADO tickets in the background *while* Gemini is generating its response, completely hiding API latency.
*   **Zero-Latency Keyword Extraction:** Uses a highly tuned Python heuristic to extract system nouns (ignoring action verbs like "show" or "check") in 0ms, falling back to LLM extraction only if necessary.
*   **4-Layer Retrieve-and-Rank Pipeline:** Pulls 10 ADO tickets, embeds them via `text-embedding-004`, mathematically scores them via Cosine Similarity, and only injects the Top 3 most relevant tickets into the AI's context window.
*   **Structural HTML Parsers (`html2text`):** Safely translates rich Confluence pages and ADO comments into pristine Markdown without destroying nested lists or tables.
*   **Distributed Sync Locks:** Utilizes an `is_syncing` database lock to mathematically prevent multiple background sync daemons from running at the same time and corrupting the vector database.

## 💻 5. Real-Time UI/UX (Vue 3 + Tailwind)
*   **Live Telemetry Streaming:** Bypasses the ASGI blocking thread to stream real-time operational statuses (`[SYSTEM_STATUS: Querying Semantic Knowledge Base...]`) to a pulsing indicator above the chat.
*   **Idempotent Session Management:** Safely handles rapid clicks on the "New Session" button, redirecting users to an empty slate without bloating the database with duplicate blank sessions.
*   **Clickable Inline Citations:** Replaces ugly metadata tags with beautiful, clickable Markdown links at the bottom of the AI's response (e.g., `[📄 Payment Specs](url)`) that survive database reloads.
*   **Mermaid Bounding Boxes:** Constrains massive architecture diagrams inside a scrolling `max-h-[400px]` container to prevent them from blooming and destroying the chat layout.
*   **Dark Mode Contrast Polish:** Utilizes dynamic CSS variables (`var(--bg-panel)`) for a flawless, high-contrast, accessibility-friendly glassmorphic UI.

## 💰 6. FinOps & DoS Protection
*   **SHA-256 Deduplication:** Hashes uploaded files on-the-fly. If the hash already exists in the database, it skips the Vertex AI embedding process entirely, saving massive API costs.
*   **Server-Side Streaming Byte Limits:** Reads uploads in 1MB chunks and instantly severs the network connection if a file exceeds 15MB, making the server immune to 50GB OOM (Out of Memory) crash attacks.
*   **Sliding-Window Rate Limiter:** A local dictionary tracks upload frequencies, rejecting users with a `429 Too Many Requests` error if they upload more than 5 files per minute to protect the embedding queue.
*   **Client-Side FinOps Workspace Filter:** Allows users to drag-and-drop entire local code folders, automatically stripping out junk folders (`node_modules`, `.git`, `.venv`) and binary files before hitting the server.
*   **Live Cost Meter:** Parses token usage directly from the Vertex AI metadata and increments a live session cost meter (e.g., `$0.00084`) in the UI.