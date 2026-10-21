# V.I.S.I.O.N. System Architecture & Technical Specifications

This document outlines the system architecture, component boundaries, stateful communication protocols, and corporate infrastructure adaptations.

---

## 1. System Architecture Diagram (Decoupled Cloud Run Microservices)

```
+-----------------------------------------------------------------------------------+
|                                  CORPORATE CLIENT                                 |
|                                                                                   |
|     +-------------------------+                 +---------------------------+     |
|     |  BROWSER VUE 3 FRONTEND |                 |   gcloud SECURE PROXY     |     |
|     |  - Loads UI via port    | <-------------> |   - Directs REST/WS to    |     |
|     |    9090 from Cloud      |                 |     Backend on port 8000  |     |
|     +-------------------------+                 +---------------------------+     |
+------------------^--------------------------------------------|-------------------+
                   |                                            |
         PORT 9090 PROXY TUNNEL                       PORT 8000 PROXY TUNNEL
                   |                                            |
+------------------v------------------+      +------------------v-------------------+
|      GOOGLE CLOUD RUN FRONTEND      |      |       GOOGLE CLOUD RUN BACKEND       |
|                                     |      |                                      |
|  +-------------------------------+  |      |  +--------------------------------+  |
|  |     Alpine Nginx Server       |  |      |  |      FastAPI API Instance      |  |
|  |  - Serves compiled static     |  |      |  |  - WebSocket /ws/audio channels|  |
|  |    Vue 3 /dist files on boot  |  |      |  |  - /api/upload ingestion routes|  |
|  +-------------------------------+  |      |  +--------------------------------+  |
|                  |                  |      |                  |                   |
|   PROTECTED BY DIRECT IAP           |      |   PROTECTED BY DIRECT IAP            |
+-------------------------------------+      +------------------|-------------------+
                                                                |
                                                      VPC ACCESS CONNECTOR
                                                                |
                                             +------------------v-------------------+
                                             |       CLOUD SQL POSTGRESQL DB        |
                                             |       - Relational Multi-Sessions    |
                                             |       - pgvector RAG embeddings      |
                                             +--------------------------------------+
```

---

## 2. Technical Stack & Component Boundaries

### 2.1. Client-Side (Frontend)
- **Framework**: **Vue 3 (TypeScript)** utilizing the modern **Composition API** (`<script setup>`) for robust, clean reactivity.
- **Style Engine**: **Tailwind CSS** with dynamic class compilation to handle fluid responsive typography and layout stacking.
- **Production Server**: **Nginx on Alpine Linux** hosted as a dedicated, decoupled Cloud Run service (`vision-frontend`) in `europe-west3`, listening dynamically on the container's designated `$PORT`.
- **State Management**: Encapsulated state composables (`useWebSocket.ts`) to isolate state links from Vue UI templates.
- **SaaS Sidebar Dialogue Sessions**: Left Sidebar connected dynamically to `/api/sessions`. Users can create concurrent chats, rename topics on-the-fly (`✏️`), and trigger atomic `ON DELETE CASCADE` deletions (`🗑️`).
- **Layout Architecture (Non-Absolute Flexbox Column Layout):** 
  - Restructured the workspace from an absolute floating overlay into a strict, non-absolute **Flexbox Column (`flex flex-col h-full w-full`)**.
  - **The Chat Feed Block (`flex-1 overflow-y-auto`)** sits cleanly above the **Console block (`shrink-0 relative`)**. 
  - **Zero-Pixel Overlap:** Since the console is a separate flex sibling at the bottom, the scrollable chat feed physically ends at the top boundary of your status bar. When scrolling, text is structurally blocked from passing behind controls, permanently solving all visual overlaps!
- **Soft SaaS Borders (Premium Aesthetic):**
  - Converted the global application styling from rigid 2px borders to standard, flat, and thin 1px lines (`--border-w: 1px` in `main.css`). This implements a sleek, modern, low-contrast dark theme with highly polished divider aesthetics.
- **Staggered, Immersive Chat Flow:**
  - Redesigned the chat thread in `SystemLog.vue` with a beautiful staggered layout. 
  - Message bubbles are structurally narrower and styled with custom avatars (a glowing 'V' badge representing the V.I.S.I.O.N. AI engine, and personalized initials for the active user). Each message includes a 1px border, creating a premium, conversational HUD environment.

### 2.2. Server-Side (Backend)
- **Framework**: **FastAPI** (Python 3) hosted as a dedicated, decoupled Cloud Run service (`vision-backend`) in `europe-west3`, listening on `$PORT`.
- **Server**: **Uvicorn** serving FastAPI over stateful TCP sockets.
- **Relational History & Vector Store**: Google Cloud SQL PostgreSQL database with the `pgvector` extension enabled, accessed securely via Serverless VPC Access.

### 2.3. SaaS Relational Database Schema (SaaS Core)
V.I.S.I.O.N. utilizes a relational, user-isolated schema to partition dialogue sessions and messages:

#### **Table 1: `chat_sessions` (Conversational Threads)**
Stores concurrent saved dialogue sessions.
```sql
CREATE TABLE chat_sessions (
    session_id VARCHAR(100) PRIMARY KEY, -- Cryptographically secure browser-native UUID
    title VARCHAR(255) NOT NULL,        -- Idempotently generated by Gemini Flash
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin_name VARCHAR(100) NOT NULL     -- Token-validated JWT claimant
);
```

#### **Table 2: `messages` (Partitioned Chat Logs)**
Tracks chat turn logs linked atomically via foreign key cascade to active sessions.
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender VARCHAR(50) NOT NULL,         -- 'ADMIN' or 'VISION'
    text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin_name VARCHAR(100) NOT NULL,
    session_id VARCHAR(100) DEFAULT 'default_session',
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);
```

#### **Table 3: `system_settings` (Dynamic Configuration & Directives Store)**
Stores persistent runtime environment settings, system-wide directives, and configuration overrides. This table has perfect parity between local SQLite and cloud PostgreSQL schemas.
```sql
CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY, -- Configuration setting key (e.g., 'system_directives')
    value TEXT NOT NULL           -- Configuration setting text/payload
);
```

### 2.4. Concurrency-Safe WebSocket Memory Queues
To prevent shared-singleton leaks where concurrent cloud users contaminate each other's memories, V.I.S.I.O.N. instantiates its sliding context window **strictly per-connection inside the WebSocket event handler loop**:
1.  On WebSocket connect (`/ws/audio?session_id=UUID`), the backend instantiates a local, thread-safe memory array: `connection_history = []`.
2.  It queries `db_service.get_chat_history_for_session(session_id, limit=10)` to populate `connection_history` with Vertex AI compatible `Content` and `Part` objects on-the-fly.
3.  Each incoming message is processed with this private, isolated array, keeping memory 100% concurrent and leak-free!

---

## 3. Stateful Communication Specifications

### 3.1. WebSocket Connection Setup
The WebSocket connection is established when `HomeView.vue` is mounted, parameterized by the active session ID to bind real-time handshakes securely:
- **Endpoint**: `ws://localhost:8000/ws/audio?session_id=UUID&admin_name=Sanjeev`
- **Reconnection Logic**: Exponentially decaying retry mechanism with 10ms thread locks during session swapping.

### 3.2. Data Payload Schemas
To handle chat traffic and streaming replies over a single TCP connection, we utilize a unified packet structure.

#### **Payload A: Chat Message (Client -> Server)**
Fired when the user hits Send.
```json
"Hello V.I.S.I.O.N.!"
```
*Server Action*: FastAPI receives raw text strings and forwards them directly to the AI Chat Session.

#### **Payload B: AI Status & Response (Server -> Client)**
Streamed from FastAPI as the AI processes or writes.
```json
"I have audited the system specifications.\n\n[SOURCES: spec-sheet.pdf]\n\n[TOKENS: 412,85]"
```
*Frontend Action*: The raw text is received by `useWebSocket.ts`. The custom markdown parser inside `SystemLog.vue` uses regex to dynamically strip the bracket metadata tags `[SOURCES: ...]` and `[TOKENS: ...]` so they are hidden from chat bubbles. The `[SOURCES: ...]` populates the progressive disclosure Citation Board, and the `[TOKENS: ...]` increment values inside the cumulative FinOps Token Cost Meter.

#### **Payload C: Voice Recording Buffer (Client -> Server)**
Binary WebM stream containing raw microphone audio captured in the browser.
```binary
[ArrayBuffer: raw audio waves]
```
*Server Action*: FastAPI intercepts the binary array, generates a unique file, writes the buffer, invokes Gemini's native transcription, and purges the file right after generation.

---

## 3.3. Advanced Cockpit Communication Pipelines (Idea E & Idea G)

### 3.3.1. HTML5 Workspace Folder Ingester Pipeline (Idea G)
To support whole-directory ingestion with zero server-side directory traversal risks, V.I.S.I.O.N. implements an elegant Client-Side Directory Traversal pipeline:
1.  **Selection**: The user clicks the Folder button (`📁`) triggering an input element decorated with `webkitdirectory` and `directory` attributes.
2.  **Recursion**: The browser recursively traverses the selected local workspace folder, reading all nested code and text files, capturing their filenames, sizes, and relative paths.
3.  **Encapsulation**: The files are consolidated into a single, compact "Folder Chip" inside the cockpit, preventing visual clutter.
4.  **Bulk Transmission**: On submit, the files are dynamically attached to a standard multipart/form-data payload, transmitted over the high-speed `/api/upload` REST gateway, and vectorized inside ChromaDB in bulk.

### 3.3.2. "Highlight-to-Ask" Cursor Calculation System (Idea E)
To allow context-aware questions on specific lines of AI text responses without native overlay collisions:
1.  **Tracking**: A global `selectionchange` listener tracks active highlighted text selections inside the viewport.
2.  **Boundary Isolation**: It verifies that the highlighted selection belongs strictly to an element with the class `.ai-message-bubble`, ignoring general selections.
3.  **Viewport Anchoring**: Captures the selection's active bounding box coordinates:
    ```typescript
    const rect = range.getBoundingClientRect();
    const x = rect.left + window.scrollX + (rect.width / 2) - 100; // Centered horizontally
    const y = rect.top + window.scrollY - 54; // Floated 54px directly above selection row
    ```
4.  **Viewport Guardrail**: If `window.innerWidth < 640`, the custom floating menu is disabled. This prevents native iOS/Android selection menus from overlapping or colliding with V.I.S.I.O.N.'s floating controls, ensuring a flawless mobile experience.

---

## 4. Voice Uplink Pipeline Architecture

The Voice Uplink allows high-fidelity spoken interactions, completely bypassing external commercial speech-to-text translators for absolute corporate privacy.

```
+--------------------+        +---------------------+        +--------------------+
|  1. USER UTTERANCE |        |  2. WEBAUDIO API    |        |  3. WEBSOCKET PIPE |
|  - Mic reads waves | ---->  |  - Records in WebM  | ---->  |  - Streams raw     |
|                    |        |  - Detects Silence  |        |    binary buffers  |
+--------------------+        +---------------------+        +--------------------+
                                                                        |
                                                                        v
+--------------------+        +---------------------+        +--------------------+
|  6. FRONTEND PLAY  |        |  5. GEMINI MODEL    |        |  4. FASTAPI DAEMON |
|  - TTS speaks text | <----  |  - Transcribes WebM | <----  |  - Generates webm  |
|    on-brand        |        |  - Generates reply  |        |  - Triggers SDK    |
+--------------------+        +---------------------+        +--------------------+
```

1. **Capture**: The browser's `navigator.mediaDevices.getUserMedia` captures raw audio.
2. **Detection**: `AudioRecorder.vue` monitors volume thresholds. It records in standard WebM, detecting silence to trigger auto-transmission.
3. **Transport**: The recorded WebM blob is pushed over the binary-enabled WebSocket (`socket.binaryType = 'blob'`).
4. **Ingestion**: The backend FastAPI saves the raw byte chunk into a secure local file (`temp_audio/<uuid>.webm`).
5. **Transcription & Core Generation**: The backend passes the WebM file to Google Cloud Vertex AI via `Part.from_data()`. Gemini 2.5 Flash natively transcribes the audio and generates the executive text reply.
6. **Playback**: The frontend receives the text reply over WebSockets and uses the browser's `SpeechSynthesisUtterance` to read it back in a British Male accent (strictly triggered only when the voice session is active).

---

## 5. API Resilience & Automated Testing Specifications

To ensure corporate-grade stability, V.I.S.I.O.N. implements strict API protection patterns.

### 5.1. Exponential Backoff (Tenacity)
To safeguard V.I.S.I.O.N. from quota bottlenecks inside Magellon's shared Google Cloud space:
* **Implementation**: Backend Vertex AI SDK calls are wrapped in Python's **`tenacity`** retry handler.
* **Logic**: On receiving a `429 Rate Limit` or standard connection timeout, the backend halts, waits an exponentially scaling duration (e.g., 2s, 4s, 8s), and automatically retries the API call. The user is shielded from seeing any error cards during transient network spikes.

### 5.2. Testing and CI/CD Framework
* **Unit Testing**: 
  - **Backend**: Uses `pytest` and `httpx.AsyncClient` to mock and validate API routes and stateful WebSocket handshakes.
  - **Frontend**: Uses `vitest` to verify Vue component lifecycle states and reactive composable synchronization.
* **Continuous Integration**: Uses a standard runner (such as GitHub Actions or GitLab CI) configured to execute automated unit tests on every Git push, preventing architectural regression.

---

## 6. Corporate Infrastructure Adaptations

### 6.1. Zscaler SSL Decryption Bypass
In enterprise corporate networks (like Magellon), Zscaler interceptors perform SSL decryption, which breaks standard Python HTTP handshakes due to missing root certificates.
- **Bypass Solution**: Added `pip-system-certs` to the Python runtime.
- **Mechanism**: Automatically forces Python's standard `urllib3` and `ssl` modules to utilize the **Windows Trusted Root Certificate Store** rather than standard bundled PEM folders. This enables secure, native corporate handshakes.

### 6.2. IAM Project Authentication
Corporate cloud infrastructure enforces strict Role-Based Access Control (RBAC). 
- **Corporate Project**: `gbr-mts-wgh-hkt-dev` in region `europe-west1`.
- **Role Requirement**: `gcp-mts-wgh-hkt-developer` assigned via Active Directory.
- **Local Fallback Mode**: The system checks `.env`. If corporate authorizations are waiting, it falls back seamlessly to personal POC spaces (`project-vision-498006` in `us-central1`) to prevent engineering blockages.

### 6.3. Cloud Run Scale-to-Zero & Cost Efficiency
- **Configuration**: The backend and frontend Google Cloud Run configurations utilize a setting of `min_instances = 0` (Scale-to-Zero).
- **FinOps Advantage**: When no users or developers are actively using the platform, the container instances fully shut down, reducing idle hosting fees to exactly **€0.00** per month.

### 6.4. VPC Egress & Port Routing (PRIVATE_RANGES_ONLY)
- **VPC Egress Configuration**: The serverless Cloud Run instances are set to **"Route only private IPs to the VPC"** (`PRIVATE_RANGES_ONLY` egress routing).
- **Resolution of Timeout Blocks**: Routing only private ranges through the Serverless VPC Access Connector ensures that database connections (directed to Cloud SQL's private IP) route securely over the corporate internal VPC, while outbound HTTP/HTTPS calls to the Atlassian REST APIs (such as Confluence Cloud) bypass the restrictive VPC proxy entirely and route directly over the internet. This permanently resolves and unblocks the 20-second connection timeout previously triggered by routing all traffic through the corporate VPC.

### 6.5. Structured JSON Cloud Logging
- **Standardized Production Output**: When deployed to GCP, all application logs are automatically converted from standard multi-line strings to single-line **Structured JSON Cloud Logging**.
- **Log Explorer Indexing**: The JSON serializer standardizes payloads by mapping key attributes directly to GCP Log Explorer indexed fields:
  - `severity`: Standard Syslog logging levels (e.g., `INFO`, `WARNING`, `ERROR`) mapped directly to GCP Log Viewer severity tags.
  - `module`: The specific Python file or package where the entry originated.
  - `line`: The exact line number of the log call.
  - `message`: The actual log text content.
  - `timestamp`: High-precision ISO-8601 timestamps.
  This structured format allows operations teams to perform granular database-style queries on logs inside Google Cloud operations suite, drastically lowering mean-time-to-repair (MTTR) during network and API incidents.

---

## 7. Phase 3: Centralized Cloud & Shared Knowledge Architecture

As the V.I.S.I.O.N. platform scales to production in Phase 3, the architecture transitions from a local single-user sandbox to a centralized, cloud-hosted platform:

```
  User A (Dev laptop)         User B (QA Laptop)
      |                            |
      |-- WS / REST Ingest (Port 80) --|
      |                            |
      v                            v
  +------------------------------------------------+
  |         CENTRALIZED MAGELLON CLOUD SERVER     |
  |         (Docker Containerized ASGI App)        |
  |                                                |
  |   +--------------------+  +----------------+   |
  |   |  FastAPI Backend   |  | AI Privacy     |   |
  |   |  - WS / Telemetry  |  | Ingest Filter  |   |
  |   +--------------------+  +--------+-------+   |
  +------------------------------------|-----------+
          |                            |
          |                      Is file RESTRICTED?
          |                      - YES -> Abort & Purge
          |                      - NO  -> Save & Embed
          v                            |
  +------------------------------------v-----------+
  |         CENTRALIZED VECTOR DATABASE (RAG)       |
  |         (Vertex Vector Search / PGVector)      |
  |                                                |
  |   - Stores shared mathematical embeddings      |
  |   - User A's uploads instantly benefit User B  |
  +------------------------------------------------+
```

### 7.1. Component Scalability & Shared Memory
* **Central Cloud Server**: The FastAPI backend is containerized inside Docker and deployed to a centralized Magellon cloud virtual machine.
* **Centralized Shared Vector DB**: In production, the system migrates to a cloud-native vector database (such as Google Vertex AI Vector Search or PostgreSQL with the `pgvector` extension) to support 2,000+ concurrent user connections.
* **Local Sandbox Dual-Layer Simulation**: In the local dev environment, PostgreSQL is seamlessly simulated using **ChromaDB + SQLite**. Relational metadata fields link vector chunks (ChromaDB) to raw parent-text records (SQLite `documents` table).

### 7.2. Automated Background Polling (VPC Firewall Bypass)
* **Strategy**: Rejecting public webhooks due to strict VPC ingress firewalls and Atlassian Administrator credential limits.
* **Implementation**: The backend runs a scheduled background daemon (`sync_connectors.py`) that polls Confluence and ADO endpoints every 30 minutes, fetching only recently updated items.
* **Authentication**: Engineered with a hot-swappable configuration inside `.env` to seamlessly transition from a Personal Access Token (PAT) during MVP local testing to a Corporate Service Account once approved by IT Security.

### 7.3. Parent-Document Collapsing Retrieval
To prevent fragmented, shallow, or incomplete answers from long-form engineering documents (PRDs, specs, functional wikis), the platform implements **Parent-Document Collapsing**:
1. **The Vector Match**: The database identifies the most relevant 1,000-character vector chunks based on query similarity.
2. **Document Mapping**: The backend extracts the unique parent `document_id` metadata tag associated with those chunks.
3. **Full Spec Reconstruction**: The backend queries the raw document store (SQLite locally, PostgreSQL in cloud production) to retrieve the *entire, unbroken Markdown text* of those parent documents.
4. **Massive Context Synthesis**: The complete specifications (schemas, requirements, tables, error codes) are fed into Gemini 2.5's massive 1-Million token context window for flawless, holistic, and cross-referenced reasoning in a single pass.

### 7.4. Cognitive Security Ingest Filter
To protect the shared cloud database from private or restricted data leaks without the latency of complex Active Directory RBAC syncs:
* **Pre-Ingestion Scan**: Before any file is embedded or stored, a background agent extracts the first page/metadata and evaluates it using Gemini Flash.
* **The Security Gate**: If classified as `RESTRICTED` (such as salary spreadsheets or passwords), the backend aborts the upload, notifies the client UI, and deletes the file from cache—mathematically guaranteeing that sensitive data never enters the shared cloud database!
