# V.I.S.I.O.N. Full-Stack AI & Cloud Specialist Curriculum

**Document Status:** Active Study Syllabus & Roadmap  
**Target:** Senior AI & Cloud Platform Architect  
**How to use:** This document contains strictly the exhaustive list of Topics and Subtopics we have implemented in V.I.S.I.O.N., alongside the advanced concepts you must study separately to master Python, Vue 3, AI, Databases, Google Cloud, and DevOps (Terraform/CI/CD). Use this as your personal checklist to guide your self-study and career progression.

---

## 🔲 Domain 1: Frontend Engineering & UI Architecture

### 1.1. Core Framework: Vue 3 (Composition API)
*   **Implemented in V.I.S.I.O.N.:**
    *   Stateful script setup compilation (`<script setup lang="ts">`)
    *   Reactive primitives (`ref()`, `reactive()`)
    *   Cached derived states (`computed()`)
    *   State-change observation and callbacks (`watch()`)
    *   Component lifecycle hooks (`onMounted()`, `onUnmounted()`)
    *   DOM repaint deferral & synchronization (`nextTick()`)
    *   Global Composable Singletons (Shared websocket and chat states)
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Virtual DOM diffing algorithms and rendering mechanics
    *   [ ] Custom directives (`v-custom`) and plug-in compilation
    *   [ ] Dynamic and Async Components (`defineAsyncComponent`)
    *   [ ] Custom hook authoring and abstract business composables
    *   [ ] Memory leak detection and garbage collection on unmounted hooks

### 1.2. Type Safety: TypeScript in Vue
*   **Implemented in V.I.S.I.O.N.:**
    *   TypeScript strictly typed Vue Single File Components (SFC)
    *   Strict response interface contracts (`interface`)
    *   Type casting and conditional guard checks
    *   Vue compiler type checks (`vue-tsc --build`)
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Advanced Types (Generics, Keyof, Mapped Types, Discriminated Unions)
    *   [ ] Type assertions vs Type Guards (`is` keyword)
    *   [ ] Module resolution configurations inside `tsconfig.json`
    *   [ ] Integration of external ambient declarations (`.d.ts`)

### 1.3. Utility Styling: Tailwind CSS & Responsive UX
*   **Implemented in V.I.S.I.O.N.:**
    *   Responsive layout breakpoints (`sm:`, `md:`, `lg:`, `xl:`, `2xl:`)
    *   Symmetrical centering translations (`left-1/2 -translate-x-1/2`)
    *   Collapsible mobile actions drawer layout (progressive disclosure)
    *   Theme-aware glassmorphic overlays (`backdrop-blur-sm`)
    *   Pulsing notification keyframes (`animate-pulse`, `animate-ping`)
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] CSS Custom Variables (`var(--name)`) integration with Tailwind configs
    *   [ ] Custom utility plugins inside `tailwind.config.ts`
    *   [ ] Fluid layout calculations (`calc()`, `clamp()`) for dynamic viewports
    *   [ ] Hardware-accelerated GPU transitions and transform animations

### 1.4. Lexical Compiling, Layouts & DOM Control
*   **Implemented in V.I.S.I.O.N.:**
    *   Dynamic client-side timezone clock synchronizer
    *   Strict viewport boundary lock (`h-screen overflow-hidden`)
    *   Scroll height tracking & auto-snapping scroll containers
    *   Local regex markdown parser with GitHub-style syntax highlighting
    *   Base64 string encoding (`btoa()`) for code snippet copying
    *   Carriage Return & CRLF standardizations (`\r\n` vs `\n`)
    *   Decoupled CSS-variables styling for strict theme-contrast consistency
    *   **Vue Router Navigation Guards (`beforeEach`)**: To intercept page requests and block unauthenticated users from seeing the cockpit.
    *   **Inline SVG Favicon Data URIs**: The DevOps hack to bypass binary `.ico` file caches using inline `data:image/svg+xml` vectors in `index.html`.
    *   **Geometric CSS/SVG Keyframe Animations**: Designing slowly spinning outer dashed rings and active neural core blurs natively.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Writing custom Abstract Syntax Tree (AST) markdown parsers
    *   [ ] Dynamic CSS-in-JS vs Static Scoped CSS performance
    *   [ ] Web APIs: Intersection Observer, Resize Observer, Mutation Observer
    *   [ ] DOM event delegation and event bubbling interception
    *   [ ] Single Page Application (SPA) routing, route guards, and DOM-unmounting life-cycles

### 1.5. Advanced Web APIs: Selection & Directory Ingestion (COMPLETED)
*   **Implemented in V.I.S.I.O.N.:**
    *   **Text Selection Ranges**: Capturing highlighted characters (`window.getSelection()`) inside active message blocks (`.ai-message-bubble`).
    *   **Selection Bounding Rectangles**: Tracking precise absolute screen coordinates of active selections (`range.getBoundingClientRect()`) to float dynamic glassmorphic capsules centered above cursors.
    *   **Directory Ingestion**: Utilizing HTML5 `webkitdirectory` and `directory` upload parameters to trigger recursive workspace folder selection.
    *   **Compact File Compression**: Collapsing massive multi-file arrays into a single, elegant folder chip on the UI, preventing file-card bloating.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Browser Selection objects, Ranges, Node Anchors, and Focus Offsets
    *   [ ] Browser layout bounding boxes, scroll-offset coordinate calculations, and stacking context indices (`z-index`)
    *   [ ] HTML5 drag-and-drop and directory-traversal file handle APIs
    *   [ ] Viewport responsiveness constraints: hiding, scaling, or disabling floating hover menus on mobile displays (< 640px) to prevent native mobile keyboard/overlay collisions

---

## 🔲 Domain 2: Backend Engineering & Concurrency

### 2.1. Python 3 Concurrency (Asyncio)
*   **Implemented in V.I.S.I.O.N.:**
    *   Asynchronous execution routines (`async def`)
    *   Awaiting non-blocking I/O operations (`await`)
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Python Event Loop mechanics, task scheduling, and coroutines
    *   [ ] Parallel execution: ThreadPoolExecutor vs ProcessPoolExecutor
    *   [ ] Asynchronous Generators and Async Context Managers (`async with`)
    *   [ ] Race conditions and thread-safety locks (`asyncio.Lock`)

### 2.2. Web API Frameworks (FastAPI & ASGI)
*   **Implemented in V.I.S.I.O.N.:**
    *   Asynchronous server routing with FastAPI
    *   CORS middleware configuration for origin sandboxing
    *   Local ASGI server hosting via Uvicorn
    *   FastAPI automatic OpenAPI/Swagger interactive documentation
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Dependency Injection patterns in FastAPI (`Depends()`)
    *   [ ] FastAPI custom background tasks (`BackgroundTasks`)
    *   [ ] Custom request validation, schemas (`Pydantic v2`), and error handlers
    *   [ ] High-performance ASGI servers (Hypercorn, Gunicorn with Uvicorn workers)

### 2.3. Real-Time Streaming Protocols
*   **Implemented in V.I.S.I.O.N.:**
    *   Stateful, bi-directional WebSockets (`ws://`) communication
    *   Real-time system telemetry streaming (CPU, RAM, Disk) using `psutil`
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] WebSocket connection handshake, framing, and close codes
    *   [ ] Server-Sent Events (SSE) vs WebSockets for AI streaming
    *   [ ] WebSocket horizontal scaling via Redis Pub/Sub backplanes
    *   [ ] Handling raw binary streams, chunks, and network fragmentation

---

## 🔲 Domain 3: Relational Databases, Vector Math & Storage

### 3.1. Relational Databases & Schemas (SQL)
*   **Implemented in V.I.S.I.O.N.:**
    *   Local sqlite3 database integration and queries
    *   Relational schema modeling (`users`, `messages`, `documents` tables)
    *   Cloud SQL PostgreSQL schema bootstrapping
    *   Relational table joins and foreign keys
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] SQL Query Optimization: Indexes, EXPLAIN PLAN, and Query Analyzers
    *   [ ] Database transaction isolation levels (ACID compliance)
    *   [ ] Connection pooling configurations (SQLAlchemy, PgBouncer)
    *   [ ] Database migration versioning (Alembic)

### 3.2. Vector Storage & Search Extensions (pgvector)
*   **Implemented in V.I.S.I.O.N.:**
    *   Persistent local vector collection in ChromaDB
    *   `pgvector` extension activation: `CREATE EXTENSION IF NOT EXISTS vector;`
    *   High-dimensional vector storage: `embedding vector(768)`
    *   Approximate Nearest Neighbor (ANN) search via cosine distance `<=>`
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Vector Distance Algorithms: Cosine vs L2 (Euclidean) vs Inner Product
    *   [ ] Database Vector Indexing: HNSW (Hierarchical Navigable Small World) vs IVFFlat
    *   [ ] Metadata pre-filtering vs post-filtering database index optimization
    *   [ ] Cloud Vector search engines (Vertex Vector Search, Pinecone, Milvus)

---

## 🔲 Domain 4: Artificial Intelligence, LLMs & High-Precision RAG (Masterclass Syllabus)

### 4.1. Core LLM & Multimodal AI Routing (Vertex AI)
*   **Implemented in V.I.S.I.O.N.:**
    *   Google Vertex AI integration (Gemini 2.5 Flash)
    *   Multimodal input handling (processing raw text and audio bytes simultaneously)
    *   Local gRPC vs. cloud REST transport fallback configurations
    *   Dynamic prompt instruction injection
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] LLM Hyperparameters: Temperature (creativity), Top-K (vocabulary pruning), Top-P (nucleus probability), and Max Output Tokens
    *   [ ] Function Calling and Tool use execution lifecycles (how models emit JSON schemas for local tool run calls)
    *   [ ] Streaming LLM responses (Server-Sent Events streaming chunks for low perceived latency)
    *   [ ] High-reasoning models (Gemini Pro, GPT-4o) and their specific architectural strengths

### 4.2. Vector Algebra, Embeddings & Vector Storage
*   **Implemented in V.I.S.I.O.N.:**
    *   Continuous multi-dimensional mappings inside local databases (ChromaDB) and enterprise relational engines (pgvector).
    *   Dynamic embeddings generation via `text-embedding-004` (768-dimensional float arrays).
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **Understanding Dimensions**: What does a "768-dimensional float array" represent? (Semantic vectors mapping coordinates in an abstract concept space).
    *   [ ] **Distance Metrics (Cosine Similarity vs. Euclidean Distance vs. Dot Product)**: Learn why Cosine Similarity (measuring vector angle) is the gold standard for text matching, while Euclidean Distance (measuring physical distance) is better for absolute values.
    *   [ ] **Vector Compression (Quantization)**: How scalar quantization compresses 32-bit floats into 8-bit integers, saving 75% memory with negligible accuracy loss.
    *   [ ] **Vector Indexing (HNSW vs. IVFFlat)**: Understanding Hierarchical Navigable Small World (HNSW) graphs for sub-millisecond semantic retrieval across millions of rows.

### 4.3. High-Precision Retrieval-Augmented Generation (RAG)
*   **Implemented in V.I.S.I.O.N.:**
    *   Multi-format document parsing (PDF, DOCX, TXT)
    *   **Zero-Dependency HTML-to-Markdown Parsing**: Native `html.parser.HTMLParser` inside `sync_connectors.py` to safely extract ADO code/lists without third-party libraries (bs4/beautifulsoup4)
    *   Semantic text slicing: 1,000 characters with 200-character overlaps
    *   High-speed batch REST embeddings generation (text-embedding-004)
    *   Conversational Query Re-writing (contextual search translation)
    *   **Parent-Document Collapsing RAG**: Locating chunks but retrieving 100% full PRD spec sheets
    *   **Autonomous Link Following**: Regular expression extraction of Confluence links inside ADO tickets with automated child ingestion
    *   **Descriptive Ingestion Filenames & UI Formatting**: `sync_connectors.py` generates highly descriptive text file names on disk mapping original Atlassian metadata (e.g., `confluence_page_PROJWT_PageTitle_ID.txt`). These structures are cleanly parsed by the frontend (`HomeView.vue`) using regex patterns to render sleek, readable titles in the dashboard (e.g., 📄 `[Confluence] PROJWT Page Title`).
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **Advanced Chunking Strategies**: 
        *   *Semantic Chunking:* Analyzing sentences and splitting paragraphs dynamically only when semantic distance transitions occur.
        *   *Hierarchical (Parent-Child) Chunking:* Chunking small 200-token snippets for high-accuracy vector searching, but linking them to 2,000-token parent paragraphs for rich model reading context.
    *   [ ] **Hybrid Search (BM25 + Dense Vectors)**: Blending standard keyword matching (BM25, perfect for alphanumeric product IDs, variables, and ticket numbers) with Dense Semantic Vector matching (perfect for abstract meanings).
    *   [ ] **Context Re-ranking (Cross-Encoders / Cohere Re-rank)**: Retrieving 50 document chunks from vector search, passing them through a lightweight "Re-ranker" network to score relevance, and sending only the Top-5 most relevant chunks to the LLM.
    *   [ ] **Graph RAG (Knowledge Graphs)**: Extrapolating unstructured documents into nodes (entities) and edges (relations, e.g., "Feature A -- [depends on] --> Feature B") and querying the relationship graph alongside vector spaces.

### 4.4. Conversational Context & Memory Management
*   **Implemented in V.I.S.I.O.N.:**
    *   **Token-Aware Context sliding window**: Slicing oldest conversation turns
    *   **Dynamic Context Compression**: Condensing past chat history via LLM summaries
    *   **Interactive Depth Toggling**: Executive Summaries ➔ Standalone call-to-action ➔ Spec detail expander
    *   **Query-Rewriter Bypass Pattern**: Scanning raw original queries for IDs to prevent search lockouts
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Token counting libraries (`tiktoken`, Google's token counter APIs)
    *   [ ] Long-context management (Gemini 1M/2M token window architectures)
    *   [ ] State-aware session management in Redis

### 4.5. Production-Grade Semantic Intent Routing vs. Dialogflow CX (Masterclass)
*   **Implemented in V.I.S.I.O.N.:**
    *   **Hybrid Semantic Routing Architecture:** Building Layer 1 cheap deterministic checks (Regex checks for ticket IDs), Layer 2 lightweight LLM semantic intent classification (`_classify_intent`), and Layer 3 execution policy routing.
    *   **Dynamic Slang & Typo Recognition:** Classifying slang (e.g. `"yo bro"`, `"hiiiiii yoooo"`) as `GREETING` to route directly to conversational models, bypassing vector search latency completely.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **The Cost/Latency Trade-offs of Agent Orchestration:** Why calling an LLM for intent routing on *every* message adds ~500ms and quota overhead, and how a Hybrid System (Regex pre-checks + LLM fallbacks) solves it.
    *   [ ] **Decision Matrix (Dialogflow CX vs. Custom Semantic Router):** 
        - Choose *Dialogflow CX* for heavy, multi-turn customer support lines where visual flowcharts are required. 
        - Choose *Custom Router + Gemini Embeddings* for narrow, low-latency (<100ms) developer tool routing inside existing software codebases.
    *   [ ] **Vector-based Semantic Routing (HuggingFace / sentence-transformers):** How to match user queries with static "Intent Clusters" using cosine similarity on pre-computed local embeddings.

### 4.6. Vue Router Role-Based Navigation Guards (Three-Tier Passcode Gating)
*   **Implemented in V.I.S.I.O.N.:**
    *   **Three-Tier Passcode Authentication Clearance:**
        1.  **ADMIN (`vision@1133`):** Unlocks the full workspace with interactive real-time chat, telemetry, and a fully interactive, clickable green "Connected" status badge that opens the secure Admin Cockpit modal.
        2.  **LEAD (`vision@lead`):** Unlocks the full interactive chat interface but locks the status badge, rendering it unclickable to prevent modifications or deeper configuration insights.
        3.  **GUEST (`vision2026`):** Redirects securely to the **Honeypot Decoy view** (a simulation dashboard displaying visual platform stats, but blocking any real database/chat connections).
    *   **Honeypot Camouflage Redirects:** Navigation guards intercept attempts to type active URLs (like `/` or `/about`) directly into the browser search bar. If authenticated as a GUEST, the router instantly force-redirects the user back to the decoy `/guest` dashboard to maintain visual confidentiality.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **Vue Router Hook Lifecycles (`beforeEach`):** Understanding `to`, `from`, and `next()` parameters and resolving execution locks (preventing infinite redirect loops).
    *   [ ] **Session Roles vs. Persistent Cookies:** Why temporary roles stored in `sessionStorage` are superior for workstation-level auto-locking when compared to `localStorage` or permanent session cookies.
    *   [ ] **Client-Side vs. Server-Side Authentication:** Why Vue Router guards are *visual navigation* gates only, and how they must be supported by API-level JWT token verification on the backend for absolute security.

### 4.7. Fluid Non-Absolute Flexbox CSS layouts (Zero-Overlap HUDs)
*   **Implemented in V.I.S.I.O.N.:**
    *   **Non-Absolute Stacking:** Converting overlapping screens into strict Flexbox columns (`flex flex-col h-full w-full relative`).
    *   **Dynamic Scroll Boundaries (`flex-1 overflow-y-auto`):** Allowing the chat feed block to expand dynamically, but physically bounding its height exactly where the console block starts, mathematically preventing text overlaps.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **CSS Flexbox Stacking vs. Absolute Positioning (`z-index`):** Why `position: absolute` is highly prone to screen overlaps on varying monitor heights, and how Flexbox natural parent layouts solve this permanently.
    *   [ ] **The Flexbox Shorthands (`flex-grow`, `flex-shrink`, `flex-basis`):** How `flex-1` dynamically takes up all available remaining height, while `shrink-0` holds a footer's height perfectly stationary regardless of viewport resizing.

### 4.8. Smart Client-Side Ingestion Filters (FinOps Guardrails)
*   **Implemented in V.I.S.I.O.N.:**
    *   **Browser-Side Directory Filtering:** Instantly scanning folder uploads in the browser and skipping folders like `node_modules`, `.git`, `bin`, `obj`, and `.venv` in under 30ms before any network upload.
    *   **Extension Whitelisting:** Discarding binary assets (.exe, .dll, .zip, media) and only allowing raw code and text-based formats (.cs, .vue, .ts, .py, etc.).
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **The Cost & Network Advantages of Client-Side Pre-Filtering:** Why discarding garbage files in Javascript in the browser is infinitely superior to uploading them and filtering on the backend (saves 99% of upload latency and vector API costs!).
    *   [ ] **Recursive Folder Ingestion via HTML5 APIs:** Understanding `webkitRelativePath` and preserving full directory hierarchies during multipart FormData transmission.

### 4.9. Hot-Swappable Model Selector Binding (GenerativeModel Caching)
*   **Implemented in V.I.S.I.O.N.:**
    *   **Dynamic Engine Swapping:** Intercepting the `[MODEL_OVERRIDE]` tag on the backend and swapping model pointers dynamically.
    *   **On-the-Fly GenerativeModel Caching:** Instantiating and caching a `GenerativeModel` instance for Gemini Pro dynamically only on first use, keeping response times instant for subsequent turns.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **Dynamic Model Initializations vs. Static Global Pointers:** How to write highly modular, dynamic generative pipelines that easily support multiple hot-swappable models without restarting servers.
    *   [ ] **Memory & Latency Optimization of Model Caching:** Why caching model initializations inside class properties prevents memory leaks and sub-second generation delays.

### 4.10. Stateless WebSocket Concurrency & Per-Connection History (SaaS Core)
*   **Implemented in V.I.S.I.O.N.:**
    *   **The Singleton Concurrency Trap:** Recognizing that storing context history inside a singleton class causes multi-user memory leaks, and moving it strictly to the WebSocket connection handler loop.
    *   **Per-Connection Memory Queues:** Declaring a local `connection_history = []` inside the socket handshake, and pre-populating it with Vertex AI Content objects dynamically on the fly.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **The Architecture of Stateless Backends:** Why stateful singletons fail horizontally under cluster load, and how decoupling state to the connection context or Redis locks solves concurrency permanently.
    *   [ ] **Reconstructive Context Restoration Loops:** Rebuilding full Vertex AI model dialogue histories dynamically from database logs on connection switches.

### 4.11. Multi-Signal Consensus-Driven RAG Evaluator (Data Science Math)
*   **Implemented in V.I.S.O.N.:**
    *   **Multi-Signal Evaluation Matrices:** Analyzing retrieval sets across Best Distance ($D_{\text{best}}$), Comparative Score Margin ($M$), Viable Chunk Counts ($C_{\text{viable}}$), and Top-K Parent Document Consensus.
    *   **Consensus Tie-Breaking Algorithms:** Deterministically grouping chunks by their parent document IDs and resolving ties by calculating the average distance of **only their viable chunks**.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **Vector Search Failure Modes (Sibling Hallucinations):** Why single-distance thresholds retrieve confusing siblings, and how margin score filters protect responses.
    *   [ ] **The Math of Consensus-Driven RAG:** Using consensus arrays to elevate search relevancy from raw fragment matching to holistic document reasoning.

### 4.12. Idempotent Background DB Updates (Race-Condition Safeguards)
*   **Implemented in V.I.S.I.O.N.:**
    *   **Idempotent Title Updates:** Executing database-native writes: `UPDATE chat_sessions SET title = :new_title WHERE session_id = :session_id AND title = 'New Session'`.
    *   **The Gating Lock:** This ensures that subsequent incoming messages do not spawn duplicate Gemini background tasks or overwrite manual title modifications.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **Idempotence in Distributed Systems:** Why operations must be safe to execute multiple times, and how database-level `WHERE` filters act as locks without using heavy lock managers.
    *   [ ] **Non-Blocking Background Tasks:** Spawning background runners dynamically in FastAPI without interrupting the real-time WebSocket communication loop.

### 4.13. Browser-Native Cryptographically Secure UUIDs (Zero-Dependency Design)
*   **Implemented in V.I.S.I.O.N.:**
    *   **Crypto Random UUIDs:** Generating highly secure session UUIDs in Javascript using the browser-native `crypto.randomUUID()` API.
    *   **Zero-Dependency Design:** Eliminating heavy external NPM packages (like `uuid` or `uniqid`), keeping the compiled build folder tiny and light.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] **Cryptographic Randomness vs. Math.random():** Why `Math.random()` is mathematically insecure and predictable, and how Web Crypto APIs utilize hardware entropy to generate secure hashes.
    *   [ ] **Webpack/Vite Dependency Tree-Shaking:** Understanding how eliminating redundant third-party libraries improves page load speeds and minimizes browser bundle bloating.

---

## 🔲 Domain 5: Security, Compliance & Network Bypassing

### 5.1. Corporate Proxy Bypassing (InfoSec Focus)
*   **Implemented in V.I.S.I.O.N.:**
    *   Zscaler corporate proxy interception analysis
    *   Windows Trust Store hooking using `pip-system-certs`
    *   BoringSSL gRPC C++ proxy bypass research
    *   Custom Selective-Append Registry Compiler: der bytes extraction of `"zscaler"` certs and PEM compilation
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] SSL/TLS Handshake steps, Public Key Infrastructure (PKI), and Certificate Authorities
    *   [ ] Corporate proxy decryptions: SSL Interception and intermediate CA certificates
    *   [ ] Configuring custom proxy variables (`HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`)
    *   [ ] Networking: VPC, subnets, firewalls, and proxy routing

### 5.2. Data Loss Prevention (DLP) & Compliance
*   **Implemented in V.I.S.I.O.N.:**
    *   **Cognitive DLP Gatekeeper**: Pre-ingestion sensitivity classification (DLP) using Gemini Flash
    *   Instant cache purging of restricted data payloads
    *   Strict session database isolation (chats are never saved to the global vector space)
    *   GCP Service Account least-privilege OAuth 2.0 Bearer Token generation
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] RegEx-based vs Cognitive-based DLP scanning comparison
    *   [ ] OWASP Top 10 for LLMs: Prompt Injection, Insecure Output Handling, Data Leakage
    *   [ ] Encryption at rest (AES-256) and Encryption in transit (TLS 1.3)
    *   [ ] Enterprise Compliance Frameworks: SOC2, GDPR, HIPAA, and ISO 27001

---

## 🔲 Domain 6: DevOps, Cloud Hosting & IaC

### 6.1. Google Cloud Platform (GCP) Architecture
*   **Implemented in V.I.S.I.O.N.:**
    *   **Google Cloud Run**: Serverless container hosting with Scale-to-Zero configuration for both backend and frontend.
    *   **Google Cloud SQL**: Managed database instances with pgvector support inside a private VPC.
    *   **Google Artifact Registry (GAR)**: Private Docker registry hosting backend and frontend images under synchronized tags (e.g. `v1.2.0`/`v1.1.0`).
    *   **Direct Identity-Aware Proxy (IAP) on Cloud Run**: Enforcing strict, managed authentication gates directly on Cloud Run services without a GCLB load balancer.
    *   **Google IAM**: Service Accounts and roles configuration (Cloud Run Invoker, IAP-secured Web App User) for secure proxy tunnel connections.
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] GCP VPC Network Peering and Cloud NAT
    *   [ ] Google Cloud Identity-Aware Proxy (IAP) for corporate single sign-on (SSO)
    *   [ ] Direct IAP vs Load Balancer-connected IAP configuration differences on Cloud Run
    *   [ ] GCP Cloud Logging, Cloud Monitoring, and Alerting Policies
    *   [ ] Multi-region highly available server setups

### 6.2. Infrastructure as Code (IaC) with Terraform
*   **Implemented in V.I.S.I.O.N.:**
    *   Declaring provider blocks (Google)
    *   Configuring input parameters (`variables.tf`)
    *   Declaring resource blocks (GCS Buckets, Cloud SQL, Cloud Run)
    *   Terraform core commands (`init`, `plan`, `apply`, `destroy`)
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Terraform State Management: Remote State backend storage (GCS/S3) and State Locking
    *   [ ] Terraform Modules: Authoring dry, reusable infrastructure modules
    *   [ ] Terraform Provisioners (`local-exec`, `remote-exec`)
    *   [ ] Advanced HCL functions: `for_each`, `count`, `dynamic` blocks, and conditionals

### 6.3. Containerization & CI/CD Pipelines
*   **Implemented in V.I.S.I.O.Y.:**
    *   Multi-stage Docker builds (`backend/Dockerfile`) utilizing `python:3.12-slim` and psycopg2 system compilations.
    *   **1-Stage Nginx Alpine Frontend Container (`frontend/Dockerfile`)**: serving compiled static Vue 3 `/dist` assets straight into public web directories, utilizing native `sed` port swappers to bind dynamically to Cloud Run's `$PORT`.
    *   GitHub Actions CI/CD workflow automation (.github/workflows/ci.yml)
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Writing optimized, secure, scratch/alpine-based Docker images
    *   [ ] Dynamically adjusting Nginx listening parameters inside `default.conf` using Unix shell commands (`sed`, `envsubst`) on container bootup
    *   [ ] Bypassing local Docker cache layers during builds using the `--no-cache` flag
    *   [ ] Container security scanning (Trivy, Snyk)
    *   [ ] GitHub Actions, GitLab CI, or ADO Pipelines advanced multi-stage deployments

---

## 🔲 Domain 7: Advanced Engineering Patterns & Multi-Agent Systems

### 7.1. IDE Extension Development (Future Roadmap)
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] VS Code Extension API: Webview Panels, Command Registrations, Sidebar Providers
    *   [ ] VS Code TreeView API for file outline navigation
    *   [ ] Inter-process communication (IPC) via Webview postMessage

### 7.2. Multi-Agent Orchestration (Future Roadmap)
*   **Required for Mastery (Self-Study Checklist):**
    *   [ ] Agentic Frameworks: LangGraph, CrewAI, AutoGen
    *   [ ] State-aware multi-agent communication routers and loops
    *   [ ] ReAct (Reasoning and Acting) prompt loops and execution planning
    *   [ ] Human-in-the-loop (HITL) manual intervention steps inside automated agent pipelines

---

## 🔲 Domain 8: The 4-Hour Terraform & IaC Bootcamp (Specialist Training)

Welcome to your **Dedicated 4-Hour Terraform Bootcamp**, Sandesh! This syllabus is structured specifically to take you from a absolute beginner to a confident Infrastructure as Code (IaC) engineer. Each hour is a focused block of study—use this guide to learn the exact concepts, syntaxes, and commands needed to create your own cloud deployments from scratch.

---

### ⏱️ Hour 1: The Building Blocks of HCL (Syntax Mastery)
In Hour 1, you will master **HCL (HashiCorp Configuration Language)**, the language used to write Terraform blueprints. You only need to learn **5 core blocks** to write any configuration:

#### 1. The `provider` Block (The Connection)
Tells Terraform which cloud platform you are targeting, which credentials to use, and where to build.
```hcl
provider "google" {
  project = "gbr-mts-wgh-hkt-dev" # Your GCP project ID
  region  = "europe-west1"        # Physical server hosting region
}
```

#### 2. The `resource` Block (The Construction)
Describes the actual infrastructure you want Google Cloud to build. Syntax: `resource "resource_type" "your_local_name" { ... }`.
```hcl
resource "google_storage_bucket" "my_bucket" {
  name     = "vsn-prod-assets-bucket"
  location = "europe-west1"
}
```

#### 3. The `variable` Block (The Inputs)
Declares input parameters so you don't have to hardcode sensitive values (like passwords or project IDs) inside your main files.
```hcl
variable "db_password" {
  type      = string
  sensitive = true # Tells Terraform never to print this password in plain text logs!
}
```

#### 4. The `locals` Block (In-File Calculations)
Like local variables in a Python function. Used to calculate and format strings dynamically within your file.
```hcl
locals {
  # Automatically formats service names to lowercase and replaces underscores
  service_name_formatted = lower(replace(var.service_name, "_", "-"))
}
```

#### 5. The `output` Block (The Outputs)
Prints important results (like your Cloud Run server URL or Cloud SQL IP address) on your terminal screen once the deployment completes.
```hcl
output "backend_url" {
  value = google_cloud_run_v2_service.this.uri
}
```

---

### ⏱️ Hour 2: The Core Lifecycle & The State File (`.tfstate`)
In Hour 2, you will learn how Terraform compiles your HCL text files, tracks what is running in the cloud, and executes deployments.

#### 1. The 4 Core Commands (Your Daily Workflow)
You operate Terraform entirely using these four commands in sequence inside your terminal:
1.  **`terraform init`**: Scans your local files, notices you are targeting GCP, and downloads the official Google provider plugins onto your machine.
2.  **`terraform plan`**: The "Dry Run". Compares your local code against the live cloud, printing exactly what it will add, change, or destroy, **without making any changes yet**.
3.  **`terraform apply`**: Executes the plan. Connects to GCP APIs and builds the resources, asking you to type `yes` to confirm.
4.  **`terraform destroy`**: Erases everything created by this template in 1 click, protecting your GCP budget.

#### 2. The `.tfstate` File (Terraform's Brain Memory)
*   **What is it?** When Terraform runs `apply` and builds a database, it automatically generates a local JSON file called **`terraform.tfstate`**.
*   **Why is it critical?** This state file is the exact database memory map linking your code resources to actual cloud IDs. If you delete or lose this file, Terraform loses its memory—it won't know that your Cloud SQL database exists and might try to build a duplicate!
*   **Enterprise Best Practice (State Locking):** In a team environment (like Magellon), multiple developers cannot have their own local state files. Instead, the state file is stored in a shared **Google Cloud Storage (GCS) Bucket** with **State Locking** enabled. This prevents two developers from running `terraform apply` at the exact same second and corrupting the cloud database.

---

### ⏱️ Hour 3: Sourcing Modules (Code Reusability)
In Hour 3, you will learn how to read and call pre-written corporate modules (like the `ccc` modules provided by your Lead), completely bypassing the need to write complex resources from scratch.

#### 1. What is a `module` block?
A module is a pre-written Terraform folder. Instead of you writing 200 lines of complex security code to build a secure Cloud SQL instance, you simply use a `module` block to "call" their pre-vetted template.

#### 2. Sourcing Corporate Git Repositories
The **`source`** argument tells Terraform where to download the module template. In enterprise setups, we source them straight from private GitLab repositories:
```hcl
module "my_database" {
  # Tells Terraform to pull the module code from Kazan GitLab, branch 'main'
  source = "git::https://gitlab.kazan.mywordline.com/ccc/terraform/modules/gcp/cloudsql.git?ref=main"

  # We pass our variables to fill in their empty placeholders!
  project  = var.project_id
  region   = "europe-west1"
  password = var.db_password
}
```

#### 3. Resolving Variable Contracts
When calling a corporate module, you **must** pass all required variables defined inside their `variables.tf` file (like passing proper argument variables to a Python function). If you miss a required variable, your plan will fail to compile.

---

### ⏱️ Hour 4: Hands-on Sandbox & Diagnostic Lab
In Hour 4, you will learn how to bootstrap your own infrastructure from scratch and troubleshoot common errors.

#### 1. How to Bootstrap a New Project Alone (Your 5-Step Recipe)
1.  Create a clean folder (e.g. `my-infra/`).
2.  Create **`00-providers.tf`** and declare your provider (`google`).
3.  Create **`01-variables.tf`** to hold your project inputs.
4.  Create **`06-managed-services.tf`** to declare your GCS buckets, servers, and databases.
5.  Open your terminal, run `terraform init`, then `terraform plan` to verify your syntax!

#### 2. Common Terraform Errors & How to Fix Them:
*   **Error: `Variable has no default value and is not set.`**
    *   *Why:* You declared a variable block but didn't supply a value.
    *   *Fix:* Add a `default = "value"` to the variable block, or supply it during planning: `terraform plan -var="db_password=MyPass!"`.
*   **Error: `Resource already exists`**
    *   *Why:* You are trying to build a resource (like a storage bucket) with a name that is already taken in Google Cloud. GCS bucket names must be globally unique!
    *   *Fix:* Update the bucket `name` variable to include your unique project ID or initials.
*   **Error: `Error locking state: Active state lock detected.`**
    *   *Why:* Another team member is running a deployment, or your previous deployment crashed midway, leaving the state lock frozen.
    *   *Fix:* Run `terraform force-unlock [LOCK_ID]` to safely release the lock and resume deployments.

---

## 🌟 New Advanced Topics Implemented in V.I.S.I.O.N.

### 1. Pydantic Validation Guardrails (`extra = "forbid"`)
*   **What is it?** Pydantic uses strict data models to parse configurations. By default, or when configured, Pydantic's `BaseSettings` checks if your `.env` contains any variables that are NOT declared inside your Python `Settings` class. If it finds any, it throws a `ValidationError` (Extra inputs are not permitted).
*   **Why did we use it?** This enforces strict fail-fast rules, preventing developers from passing undocumented environment configurations that could lead to silent failures or security misconfigurations.
*   **How does it work?** We updated `config.py` to declare both `CONFLUENCE_SPACES` and `ADO_PROJECT` as formal, typed fields inside the `Settings` class:
    ```python
    CONFLUENCE_SPACES: str = "PROJWT,ERK"
    ADO_PROJECT: str = "WLMTSConsole,Genoa Kiosk"
    ```

### 2. Theme-Aware Native CSS Variable Bindings
*   **What is it?** In modern responsive SPAs, some elements must change color dynamically between light and dark themes (e.g. text changing from white to black). While Tailwind utility classes like `dark:text-white` can do this, they rely on Tailwind's compiler settings which may fail to compile if your environment has custom toggling hooks.
*   **Why did we use it?** To completely bypass compiler limitations, we bound the central greeting text directly to browser-native CSS variables (`text-[var(--text-primary)]`), which are declared inside our global stylesheet `main.css`.
*   **How does it work?** 
    *   In `main.css` (Light Mode `:root`): `--text-primary: #000000;` (pure black).
    *   In `main.css` (Dark Mode `.dark`): `--text-primary: #ffffff;` (pure white).
    *   In `HomeView.vue`: `class="text-[var(--text-primary)]"`
    This is highly efficient, browser-native, and guarantees 100% real-time theme hot-swapping instantly!

