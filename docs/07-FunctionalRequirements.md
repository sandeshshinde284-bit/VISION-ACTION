# V.I.S.I.O.N. Functional Requirements & TODO Roadmap

**Project:** Virtual Intelligent System for Integrated Operational Networks (V.I.S.I.O.N.)
**Version:** 1.5 (SaaS Multi-Session Production Release)
**Status:** **100% Fully Built & Deployed on GCP | Local Sandbox Complete & Verified**

This document is the **Single Source of Truth (SSoT)** for functional specifications and active deliverables. It tracks implemented milestones, current task states, and future planning.

---

## 1. Project Milestone Tracker (TODO List)

### 🟩 Phase 1: Interactive HUD & Infrastructure (COMPLETED)

#### **1.1. Core Frontend UI/UX**
- [x] **2-Column Responsive Layout**: Streamlined HUD consisting of collapsible Hardware Metrics (left) and the Unified Workspace (center).
- [x] **Branding Integration**: Custom **Magellan Blue** corporate styling with the **"Vision in Action"** tagline.
- [x] **Accessible Sliding Drawers**: Replaced tiny text toggles with prominent, touch-friendly SVG chevrons and floating edge triggers.
- [x] **Scientific Light Mode**: High-contrast "Laboratory" theme with perfect visibility and softened slate text (`#1e293b`). Hardened with strict HTML root theme classes (`.light`) to guarantee high-contrast legibility of bullet lists, headings, bold text, and code badges.
- [x] **Tactical Command Console**: Modular footer containing the Privacy Lock, Voice Uplink, and Command input.
- [x] **Full-Dialogue Chat History**: Displaying user commands (`[ADMIN]`) and AI responses (`[V.I.S.I.O.N.]`) in a beautiful, styled feed.
- [x] **Export Capabilities**: Multi-format session logs (Markdown and Text) and single Analysis Result downloads.
- [x] **Fluid Responsive Typography**: Dynamic font-sizes (e.g., textarea scales from `15px` on mobile to `18px` on desktop) and responsive button padding to eliminate overlaps.
- [x] **Custom Theme-Aware Dropdowns**: Sleek Vue flyout menus replacing ugly, native browser select inputs.
- [x] **Executive SaaS UI/UX Overhaul**: Injected premium **Inter** (body) and **JetBrains Mono** (monospace) web fonts via Google Fonts. Overhauled the markdown parsing regex to be fully robust across Windows CRLF line endings. Redesigned the conversational feed into a standard **User Right (Glassmorphic Accent Bubbles) and AI Left (Solid Panel Bubbles)** layout. Developed an ultra-fast, conflict-free, regex-based **Local Code Syntax Highlighting Engine** to colorize code blocks with GitHub-style keywords, strings, comments, numbers, and constants. Hardened the backend vector search with a strict **Semantic Similarity Threshold** (`distance <= 0.85`) and redesigned the **RAG Citation Board** into a non-disruptive, glassmorphic floating overlay drawer—completely eliminating layout shifting during conversation turns. Fixed all inline code contrast and container width constraints (`max-w-4xl`) for an elite, spacious executive reading experience.

#### **1.2. Backend & System Link**
- [x] **FastAPI WebSocket Link**: Stateful, bi-directional, real-time pipeline between Vue 3 and Python.
- [x] **Real-Time Telemetry**: Real CPU, RAM, and Disk metrics gathered using the `psutil` library and streamed every 2 seconds.
- [x] **Corporate Security Compliance**: Configured Google Cloud Application Default Credentials (ADC) to bypass the need for unsafe API keys.
- [x] **Proxy Bypass (Zscaler)**: Integrated `pip-system-certs` to automatically inject the Windows Certificate Store for secure SSL Handshakes.
- [x] **Model Enforcer**: Locked the backend strictly to the `gemini-2.5-flash` model.

---

### 🟧 Phase 1.5: Critical Pre-RAG Infrastructure (COMPLETED)

Before introducing heavy document contexts (RAG), the system has been hardened against token limits, rate caps, and local memory resets.

#### **1.5.1. Production-Grade Memory Manager & History**
- [x] **Token-Aware Conversational Window**: Replace Google's native `model.start_chat()` (which appends endlessly) with a custom Python array manager (Sliding Window).
- [x] **Dynamic Compression**: Automatically summarize historical conversations when context limits are approached to prevent `429 Resource Exhausted` errors.
- [x] **Persistent User History Database**: Integrate local SQLite to permanently store chat history. Create `Users` and `Messages` schemas to isolate history per employee.

- [x] **Self-Learning Hydration**: Upon WebSocket connection, query SQLite and push the user's historical chat transcript to the frontend, providing a continuous, "ChatGPT-style" memory experience.

#### **1.5.2. API Resilience & Error Handling**
- [x] **Retry Logic**: Wrap Vertex AI calls in an exponential backoff loop (e.g., using Python's `tenacity` library) to automatically recover from `429 Too Many Requests` without crashing the UI.
- [x] **Circuit Breakers**: Implement graceful degradation if GCP goes offline (e.g., returning a clear "Service Unavailable" message instead of a raw traceback).
- [x] **Offline Model Robustness**: Hardened auto-title generation (`generate_session_title`) and ADO keyword extraction (`extract_ado_search_keyword`) with model presence guards to gracefully handle offline brain states without raising traceback exceptions.
- [x] **Relational Schema Consistency**: Aligned local SQLite database with PostgreSQL schema by bootstrapping the `system_settings` table locally, resolving startup config synchronization warnings.


---

### 🟨 Phase 2: Knowledge Ingestion & RAG (COMPLETED)

#### **2.1. Local Vector Database**
- [x] **ChromaDB Integration**: Install and initialize a persistent, local ChromaDB instance in the FastAPI backend.
- [x] **Vertex AI Embeddings**: Wire `text-embedding-004` to convert text chunks into mathematical vectors.

#### **2.2. Document Ingestion Pipeline**
- [x] **HTTP Upload Gateway**: Build `POST /api/upload` endpoint in FastAPI to accept PDF, DOCX, and TXT files from the frontend.
- [x] **Multi-File Frontend Link**: Connect the UI's drag-and-drop / 📎 Attach buttons to transmit the actual files to the new API.
- [x] **Python Document Parsers**: Integrate `pypdf` and `python-docx` to extract raw text.
- [x] **Smart Chunking**: Split extracted text into overlapping 1000-character segments (with 200-character overlaps) before vectorization.

#### **2.3. Semantic Search & Injection**
- [x] **Context Retrieval**: Convert user questions into vectors, query ChromaDB for the Top-3 most relevant paragraphs.
- [x] **Prompt Injection**: Dynamically inject recovered paragraphs into the system context before sending the query to Gemini 2.5 Flash.
- [x] **Conversational Query Rewriting**: Pre-process follow-up questions (e.g., "how is that different?") with chat history to generate standalone search queries for accurate database retrieval.
- [x] **Source Attribution UI**: Extract metadata (filename, page/section) from retrieved chunks and populate the right-side 'RAG Citations' panel to build executive trust.

---

### 🟩 Phase 4: Production-Grade Security & Agentic Routing (COMPLETED - PARTIAL)

**⚠️ CLARIFICATION: Honeypot Guest Mode NOT IMPLEMENTED**

The following honeypot features were planned but NOT found in code:
- ❌ **GuestView.vue** — Does not exist
- ❌ **Double-Passcode Login** — NOT implemented (hardcoded passcodes `vision@1133` and `vision2026` do NOT appear in code)
- ❌ **Honeypot Dashboard** — Does not exist

**✅ What IS Implemented:**
- [x] **Database-Driven Login** (`LoginView.vue`) — Secure credentials stored in SQLite, NOT hardcoded passcodes
- [x] **Role-Based Access Control** — Roles stored in database (`admin`, `user`, `guest`)
- [x] **Router Navigation Guards** (`router/index.ts`) — Restricts unauthenticated access
- [x] **Secure Session Tokens** — 64-char cryptographic tokens (NOT passcodes)

#### **4.2. Pure LLM Semantic Intent Router (`ai_service.py`) - VERIFIED COMPLETE**
- [x] **Hybrid Decision-Tree Routing:** Implemented intelligent, multi-layered Python router:
  - **Layer 1 (Deterministic Fast-Paths):** Regex checks intercept explicit scope shortcuts (`@web`, `@internal`, `@both`).
  - **Layer 2 (LLM Intent Classification):** Call `_classify_intent()` to classify intent into `GREETING`, `GENERAL`, `INTERNAL`, or `AMBIGUOUS`.
  - **Layer 3 (Execution Policy):** Routes based on classification:
    - **`GREETING`** ➔ **`CHAT`** (no RAG, no external search)
    - **`GENERAL`** ➔ **`WEB`** (intended for web search; not yet wired to Google API)
    - **`INTERNAL`** ➔ **`RAG`** (ChromaDB semantic search)
    - **`AMBIGUOUS`** ➔ Ask user for clarification
- [x] **Context-Aware Persona:** System prompt (SYSTEM_DIRECTIVES.md) defines V.I.S.I.O.N.'s conversational style
- [x] **Visual Metadata Filter (`SystemLog.vue`):** Regex strips backend routing tags (`[SOURCE: ...]`) before rendering

#### **4.3. Smart Scroll & Responsive UI - VERIFIED COMPLETE**
- [x] **Smart Scroll Anchoring:** Scroll position listener maintains user's place when reading history
- [x] **Smooth Scrolling Animations:** Browser-native smooth scroll to bottom
- [x] **Flexbox Layout:** Responsive 2-column HUD (sidebar + chat)
- [x] **Chat Display:** Messages rendered with proper spacing and alignment
- [x] **WebSocket Streaming:** Real-time token streaming display

**⚠️ NOT IMPLEMENTED (Docs Claimed):**
- ❌ **Model Selector UI** — Feature not found in code (locked to Gemini 2.5 Flash only)
- ❌ **Scope Selector Chips** — Feature not found in code (routing is functional but no UI chips)
- ❌ **Token Cost Meter** — Not visible in UI (backend doesn't expose token counts)
- ❌ **Workspace Folder Ingester** — Feature not found in code
- ❌ **Highlight-to-Ask Menu** — Feature not found in code

---

## 2. Completed Features In This Session (Dynamic Sync)
The following 5 documentation guides have been updated in lockstep synchronization to reflect all of our new production-grade security, routing, and scrolling features:
1.  **`docs/07-FunctionalRequirements.md`**: Upgraded TODO Milestones, added Phase 4 security specs.
2.  **`docs/08-Architecture.md`**: Updated role-based routing architecture and Non-Absolute Flexbox layout maps.
3.  **`docs/09-AIEngine.md`**: Documented our LLM Semantic Intent Router and Context-Aware Persona.
4.  **`docs/10-LearningGuide.md`**: Added a dedicated study guide on Semantic Routing vs. Dialogflow CX, Vue Router Navigation Guards, and Flexbox layouts.
5.  **`docs/04-Runbook.md`**: Documented the new Guest passcode (`vision2026`) and Admin passcode (`vision@1133`) inside the Operations Manual.

---

### 🟪 Phase 4: Developer Tooling, Extensibility & Agentic Routing (COMPLETED)

*Transform V.I.S.I.O.N. into a state-aware, self-routing Agentic platform with advanced developer shortcuts, UI selectors, and progressive clarifications.*

#### **4.1. The V.I.S.I.O.N. 4-Way Agentic Router (COMPLETED)**
- [x] **State-Aware Intent Routing Engine**: Refactored the core text processing loop `process_text()` in `ai_service.py` into an intelligent traffic controller, dynamically branching queries across fast-paths, exact-matches, internal RAG databases, and live web search grounding.
- [x] **Secure Dual-Engine Model Isolation**: Set up two separate model instances: `self.model` (strictly has **no** external search tools, guaranteeing 100% corporate data privacy) and `self.model_web` (has the Google search grounding tool explicitly enabled), ensuring zero-leak routing safety.
- [x] **Sleek UI Scope Selector Chips**: Integrated 4 selectable glassmorphic chips above the chat console: `Auto`, `Internal Docs`, `Web Search`, and `Both (Hybrid)`. The selected state is appended to the WebSocket payload as `[SCOPE: currentScope]`.
- [x] **Real-Time Route Reason Badge**: Configured the frontend to capture `[SOURCE: currentScope]` from incoming messages and render a glowing, tech-accented Routing Reason status ribbon above the chat cockpit.
- [x] **Power-User Keyboard Shortcuts**: Engineered regex interceptors in Python to immediately override the scope and bypass database queries if the user starts their sentence with `@web `, `@internal `, or `@both `.
- [x] **Progressive Clarification Fallback Loop**: In `Auto` mode, if the database returns 0 high-confidence matches on a query, the backend pauses, stays within secure bounds, and explicitly asks: *"Would you like me to query the public web instead?"* If the user replies "yes", V.I.S.I.O.N. automatically executes the web-grounded route.

#### **4.2. Command Line Interface (CLI)**
- [ ] **`vision-cli` Tool**: A standalone Python CLI allowing engineers to run headless tasks (e.g., "vision audit ./src") directly from their terminal using the V.I.S.I.O.N. brain.

#### **4.3. IDE Integration (VS Code Extension)**
- [ ] **V.I.S.I.O.N. VS Code Extension**: An official editor side-car letting developers highlight code locally and consult the V.I.S.I.O.N. RAG engine.

#### **4.4. Gated Security & Brand Polish (COMPLETED)**
- [x] **Secure Application-Level Login Gate**: Created a premium, glassmorphic login panel (`LoginView.vue`) enforcing a secure, single-key entrance password (`vision2026`) before allowing any interface interaction.
- [x] **Strict Router Navigation Guards**: Integrated a `router.beforeEach` routing guard in `router/index.ts` to block unauthenticated users, immediately redirecting any page requests back to the secure login gate.
- [x] **Dynamic Session Auto-Locking**: Switched all active token storage from persistent `localStorage` to temporary **`sessionStorage`**. The session is instantly wiped the second the browser tab is closed, enforcing robust workstations security.
- [x] **Dynamic Identity & RAG Binding**: Linked the login username text field directly to the active `adminName` Vue state, enabling V.I.S.I.O.N. to address the user by name and automatically log all chat turns in SQLite under their actual name!
- [x] **Bespoke Cybernetic SVG Core Logo**: Designed a breathtaking, multi-layered visual logo on the login card featuring a slowly spinning outer dashed geometric ring, pulsing ambient blurs, a holographic "V" path, and a pinging active emerald-green neural core.
- [x] **Inline SVG Browser Tab Favicon**: Replaced the default Vue icon inside `index.html` with a custom inline SVG data URI representing your corporate logo, ensuring 100% brand immersion in the browser tab.
- [x] **One-Click manual Console Lock**: Injected a red-glowing `[ 🔒 Lock Console ]` button at the bottom of the Left Panel sidebar, allowing users to manually lock their session in a single click.
- [ ] **Sidebar Webview Extension**: Embed the Vue 3 HUD directly into a VS Code sidebar.
- [ ] **Context Highlighting**: Right-click to send highlighted code files or terminal logs directly to V.I.S.I.O.N. for automated review.

#### **4.3. Multi-Agent Orchestration & Testing**
- [ ] **Specialized Sub-Agents**: Break down tasks into specialized agents (e.g., Confluence Reader, ADO Sync, Code Reviewer) managed by a central supervisor LLM.
- [ ] **CI/CD Integration**: Create GitHub Actions / GitLab CI pipelines to enforce linting, type-checking, and passing tests before deployment.

#### **3.6. Advanced UX & Intelligent Cockpit Polish (COMPLETED)**
- [x] **Automatic Time-Based Themes**: Automatically toggle Dark Mode at night and Light Mode during the day based on the client's local clock to minimize eye strain.
- [x] **Optimistic UI Clearing**: Empty the text area and file attachment list instantly upon clicking send to ensure 0ms perceived response latency.
- [x] **Persistent Composable Singletons**: Restructure useWebSocket to share states globally, completely preventing multi-connect collisions and unmount disconnects.
- [x] **AI Prompt Optimizer (✨ Optimize)**: Add a backend prompt-refactoring engine and frontend action button to polish messy thought inputs into grammatically perfect RAG-ready queries, saving tokens and maximizing retrieval accuracy.
- [x] **Clean Startup Default Layout**: Hide hardware sidebars by default, keeping the cockpit workspace completely clean, spacious, and maximized.
- [x] **Premium Font Scaling & Bold Headings**: Scaled base dialogue text from 15px/16px to 16px/17.5px, increased markdown lists/tables to 15px/16px, explicitly enforced bold weights/larger scales on headings for elite readability, and replaced the weird RAG trash-can button with a clean standard close dismiss icon.
- [x] **First-Start Onboarding Welcome Modal**: Present an elegant welcome overlay strictly on the very first start of the application (tracked via `localStorage`), explaining Core Guidelines/Directives and letting the user customize `SYSTEM_DIRECTIVES.md` on-the-fly with dynamic light/dark contrast classes.
- [x] **Dynamic Prompt Optimizer Guardrails**: Defensive Python check instantly bypasses simple conversational greetings (costs 0 tokens, instant speed) and strict prompt rules return meaningless keyboard-smash gibberish (like "asdfgsdews") unmodified, saving 100% of output tokens.
- [x] **Real-Time Token FinOps Cost Meter**: Backend extracts raw prompt and candidate token counts from response metadata, streams them via WebSocket `[TOKENS: in,out]`, and frontend parses/aggregates them to display running billing session cost in fractions of a cent ($0.075/1M input, $0.30/1M output).
- [x] **Workspace Folder Ingester**: Desktop-only 1-click project directory upload utilizing HTML5 `webkitdirectory` attributes, collapsing files into a sleek visual Folder Chip on the UI and vectorizing the workspace folder in bulk recursively, completely hidden on mobile viewports (< 640px).
- [x] **"Highlight-to-Ask" Response Refiner**: Desktop-only selectionchange listener tracking text bounding-boxes in V.I.S.I.O.N. chat bubbles, sliding up an ultra-premium, dark-glassmorphic, text-only capsule (`Explain` and `Code` action keys) centered perfectly above cursors, disabled on mobile viewports (< 640px) to prevent iOS/Android native overlays conflict.

---

### 🟥 Phase 3: Conversation Memory & Context (MISSING - NOT IMPLEMENTED)

**Status:** ❌ Never built. Planned but deprioritized.

- ❌ **Conversation Branching** — Allow users to branch conversation threads; not in code
- ❌ **Advanced Context Memory** — Multi-turn context summarization; not in code
- ❌ **Document Management UI** — Admin interface for uploaded documents; not in code

---

## 2. Functional Specification Overview

### 2.1. The User Interface (HUD)
The V.I.S.I.O.N. HUD operates as a single-page corporate operating cockpit. 
- **Strict Viewport Boundary (100vh)**: To prevent chaotic scrollbars on the browser window, the HUD fits exactly inside 100% of the viewport height. All scrollbars are contained inside inner scroll columns (such as the middle chat feed or the sidebar lists), giving the platform a tight, native application feel.
- **Fluid Grid Scaling**: Built on a highly flexible, responsive Flexbox layout (rather than rigid CSS grids). Sidebar panels shrink and grow dynamically with fluid liquid transitions, maintaining absolute content alignment and perfect centering across all monitor widths.
- **Unified Workspace Timeline**: Handles simple text chats, multi-line commands, file upload attachment chips, and dynamic API streaming state cards in a single, cohesive, chronological timeline.

---

### 2.2. Interactive Controls
- **System Security (Mic Live / Muted)**: Provides immediate, high-visibility client-side visual validation of the microphone recording status using distinct colors and custom Microphone / Microphone-Slash SVG indicators.
- **Voice Uplink**: Initializes local browser audio recording stream and fires it to the backend via WebSocket binary buffers, converting spoken commands into instant text.
- **Model Selector**: Allows selection between standard and high-reasoning Gemini configurations via a completely custom, theme-aware glassmorphic flyout menu.
- **AI Prompt Optimizer (✨ Optimize)**: Processes fragmented or conversational thought text with our backend re-writing engine, outputting grammatically perfect, RAG-ready queries instantly.

---

### 2.3. Collapsible Sidebar Rail (The Left Panel)
Inspired by gold-standard modern layouts, the left sidebar features a dual-state collapsible architecture:
*   **State 1: Collapsed Icon Rail (Pristine View)**: When minimized, the sidebar contracts into a sleek `w-16 md:w-20` vertical glass rail on the absolute left of the screen. This rail houses compact icon action buttons (Expand `>`, New Session `+`, and Active Chat `💬`). It keeps the interface 100% minimal and clean while keeping essential controls immediately visible and accessible.
*   **State 2: Expanded Sidebar (Full Context)**: Clicking expand (`>`) smoothly slides open the full `w-80` sidebar pane, revealing the "Dialogue Sessions" title, full text labels, and the list of "Recent Chats."
*   **Aesthetic Alignment**: When expanded, the center chat feed gracefully and fluidly resizes itself to accommodate the panel, keeping your conversation perfectly aligned and centered without any overlapping or jumping.

---

### 2.4. Always-Visible "New Session" Button
To ensure developers can start fresh conversations at any instant, the "New Session" (chat reset) button is strategically integrated in both states:
*   **Inside the Top Header**: A dedicated, bordered glassmorphic button sits in the top header. On desktop monitors, it displays `+ New Session`. On mobile devices, it automatically collapses into a compact circle containing only `+`, saving precious screen space while remaining completely visible.
*   **Inside the Collapsed Icon Rail**: An active plus (`+`) button sits near the top of the rail for 1-click resets.
*   **Inside the Expanded Sidebar**: A large, prominent, full-width button styled with `+ New Session` sits right at the top of the panel (above your Recent Chats list), matching standard modern user flow.

---

### 2.5. Dynamic RAG Citation Board & Folder Icon (Progressive Disclosure)
To keep the dashboard clutter-free, the platform enforces "Progressive Disclosure" on all citation metrics:
*   **RAG Folder Icon (Left Rail)**: A folder icon (`📁`) is integrated inside your collapsed left rail. It is conditionally rendered: it remains **completely hidden** from the sidebar during general conversations (such as typing *"hello"*).
*   **The Reveal**: The very second V.I.S.I.O.N. executes a semantic search and matches verified files, the folder icon **automatically pops into your left rail**, featuring a **glowing, pulsing blue notification dot** to alert you that active references have been found.
*   **Floating Citation Board (The Right Panel)**: Expanding the folder (or clicking the right-edge circular tab) slides open the right RAG Citation Board. This floating pane displays verified document cards, source system badges (Confluence or ADO), and the exact highlighted text blocks that V.I.S.I.O.N. read from the database, building ultimate executive trust in the AI's responses.

---

### 2.6. Interactive Depth Toggling (Executive vs. Deep-Dive Modes)
To prevent "information overload" and conserve Gemini token quotas, V.I.S.I.O.N. implements an interactive conversation pattern:
*   **Stage 1: Executive Summary**: When asked a broad question (e.g., *"What is the Car Parking feature?"*), the AI retrieves the top 5 database documents but outputs only a clean, concise, high-level Executive Summary (outlining core purpose, state, assignee, and key requirements using clean bullets).
*   **The Call-to-Action**: At the absolute end of the summary, V.I.S.I.O.N. appends a standalone, spacious paragraph asking: *"Would you like me to dive deeper and provide the exhaustive technical details, step-by-step specifications, or discussion history for this feature?"*
*   **Stage 2: Technical Deep Dive**: If the developer replies with *"yes"*, *"go deeper"*, or *"deep dive"*, V.I.S.I.O.N. fully releases its Principal Engineering capabilities, generating complete step-by-step specifications, code examples, database layouts, and full developer discussion comment history.

---

### 2.7. Query-Rewriter Bypass Pattern (High-Precision Follow-Up)
Conversational search often gets locked out of Confluence specs due to LLM query re-writing:
*   **The Problem**: If a user asks a follow-up (such as *"What about Confluence?"*), the Query-Rewriter includes past ADO ticket IDs in its generated prompt to maintain context. If the RAG engine scans that rewritten prompt, it locks the search space *only* to those specific ADO tickets, blocking Confluence page retrieval.
*   **The Bypass**: V.I.S.I.O.N. is engineered to **scan the user's original raw input** for explicit document and ticket IDs instead of scanning the rewritten prompt. If your raw follow-up has no specific IDs, it executes a broad, unrestricted semantic search, successfully loading Confluence specs alongside ADO tickets and allowing you to transition between tracking systems seamlessly.

---

### 2.8. Real-Time FinOps Cost Meter (Cost Transparency)
API cost anxiety can prevent enterprise-wide LLM adoption. V.I.S.I.O.N. integrates an active, subtle, real-time Token Cost Meter right above your cockpit console:
*   **The Metrics Hook**: The backend (`process_text` and `transcribe_audio`) parses Gemini response metadata, capturing exact prompt and candidate token counts, and streams them over the WebSocket pipeline as a safe metadata tag `[TOKENS: in,out]`.
*   **Strict Sanitization**: Your custom markdown parser in `SystemLog.vue` sanitizes this tag dynamically using regex, completely hiding it from visual chat bubbles.
*   **FinOps Accumulator**: The frontend UI watches incoming replies, parses token counts, aggregates them, and calculates real-time Gemini 2.5 Flash pricing ($0.075 / 1M input tokens, and $0.30 / 1M output tokens). It renders the live, cumulative, estimated dollar cost of your session, building massive executive trust.

---

### 2.9. Workspace Folder Ingester (Bulk Codebase Ingestion)
To facilitate whole-directory indexing without complex manual file zipping:
*   **Directory Picker**: Desktop-only folder uploader button (`📁`) next to the file attachment clip trigger, launching an HTML5 input with `webkitdirectory` and `directory` attributes.
*   **Compact Folder Chip**: Instead of bloating the input console with 100 individual file chips, V.I.S.I.O.N. collapses the directory files into a single, sleek glassmorphic Folder Ingestion Chip displaying the folder name, total file counts, and total KB size.
*   **Mobile Hiding**: Because mobile viewports (iOS/Android Safari/Chrome) do not support directory-level file selectors, the Folder uploader utilizes Tailwind `hidden sm:inline` styles, keeping it strictly desktop-only.

---

### 2.10. "Highlight-to-Ask" Response Refiner (Context-Aware Follow-Up)
Instead of forcing developers to manually write follow-up questions detailing which sentence of V.I.S.I.O.N.'s response they are asking about:
*   **Selectionchange Listener**: Registers a custom global selectionchange event tracker. When you highlight any text inside a V.I.S.I.O.N. chat card (`.ai-message-bubble`), the system extracts the text selection and calculates its screen coordinates dynamically using native browser Bounding APIs (`getBoundingClientRect()`).
*   **Tactile Floating Menu**: Slides up an ultra-user-friendly, dark-glassmorphic context capsule right above your highlighted text, featuring two prominent, high-tactility pill keys:
    *   `[ 🔍 Explain ]` ➔ Asks for deep architectural context, specs, and definitions.
    *   `[ 💡 Code ]` ➔ Asks for a step-by-step copy-pasteable code snippet or script.
*   **Auto-Submit**: Clicking any key instantly clears your highlighted selection, packages the text inside a pre-written high-context prompt, and submits it over your active WebSocket stream.
*   **Mobile Viewport Guardrail**: On mobile devices, native OS overlays (Copy/Share/Look Up) collide with custom floating divs. V.I.S.I.O.N. strictly disables the custom popup on viewport widths < 640px, guaranteeing a clean, conflict-free mobile experience.

- It features an **Active Workspace** central feed that handles simple text chats, multi-line command prompts, dynamic loading spinners, and visual file upload chips in a single, unified timeline.

### 2.2. Interactive Controls
- **System Security (Mic Live / Muted)**: Provides immediate client-side visual validation of the mic status using standard Microphone and Microphone-Slash indicators.
- **Voice Uplink**: Initializes local browser audio recording stream and fires it to the backend via WebSocket binary buffers.
- **Model Selector**: Allows selection between standard and high-reasoning Gemini configurations via a completely custom, theme-aware glassmorphic flyout menu.

---

## 3. Phase 5+ Roadmap: Advanced Features (FUTURE BACKLOG - Not Implemented)

**Status:** 🗺️ **Planned for future releases** (Q1+ 2027). These features were aspirational but are NOT yet in code.

The following high-value features are recorded for the next major release cycles:

### **3.1. Git-Aware Ingestion (.gitignore Automated Parsing)**
- **The Concept**: Automatically exclude dependencies and compiler garbage without manual config.
- **How it works**: When a folder is selected or dropped, the browser automatically scans the root of the folder for a `.gitignore` file, parses its rules, and dynamically applies them to the browser's ignore list on-the-fly, ensuring that if it's ignored in git, it's ignored in V.I.S.I.O.N.!

### **3.2. Dedicated CLI Ingestion Tool (`vision-cli`)**
- **The Concept**: Provide a Node.js/Python CLI utility for developers who work primarily inside the terminal.
- **How it works**: Developers can run commands like `vision ingest ./my-project --exclude node_modules --include "*.cs, *.ts"`. This supports local watch-modes, automatically uploading and re-indexing modified files in the background as you code!

### **3.3. Multi-Workspace Repository Scoping**
- **The Concept**: Prevent cross-contamination of code when developers are working on multiple independent projects.
- **How it works**: Allow developers to create and toggle separate "Workspaces" in the UI (e.g., Workspace A: `Evoke.Kiosk.RailTVM`, Workspace B: `vision-ui`). All uploaded files are tagged with their specific workspace ID, and queries are strictly scoped to that active workspace, preventing RAG hallucinations!

### **3.4. Language-Specific AST Structure Parsing**
- **The Concept**: Index your code's import relationships, call graphs, and classes, rather than just raw code chunks.
- **How it works**: Run an AST (Abstract Syntax Tree) analyzer over the files to extract modules and imports. When you query *"Which files import from auth.cs?"*, V.I.S.I.O.N. delivers a 100% mathematically accurate call graph, completely bypassing vector matching boundaries.
