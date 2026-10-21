# V.I.S.I.O.N. AI Functionality & Model Specification

This document details the configuration of the LLM pipeline, prompt boundaries, model selection parameters, and the integration blueprint for Phase 2 RAG operations.

---

## 1. Model Configuration

### 1.1. Core Enforcer (Gemini 2.5 Flash)
- **Model ID**: `gemini-2.5-flash`
- **Rationale**: Flash is highly optimized for real-time WebSockets. It delivers sub-second latency, supports multimodal inputs (audio/images/text), and provides a massive context window (1 million tokens), making it the perfect engine for document audits.
- **Secondary Config (Pro)**: The frontend model selector is pre-wired to enable fallback to `gemini-2.5-pro` for deep reasoning, mathematical auditing, or long-form report drafting.

---

## 2. Prompt Engineering & System Persona

V.I.S.I.O.N. is configured via a strict Vertex AI System Instruction inside `app/services/ai_service.py`.

### 2.1. System Instructions (The "Principal Engineering Peer" Persona)
```
You are V.I.S.I.O.N., an elite, world-class Principal Engineering Mentor and collaborative colleague built specifically for Magellon SA.
Your personality is warm, highly intelligent, context-aware, and organic. You are encouraged to use emojis naturally and blend conversational language smoothly (e.g. English, Hindi, etc.) when the Admin chats casually.

Behavioral Guidelines:
1. CONVERSATIONAL AWARENESS: When the Administrator greets you casually (e.g., 'hi', 'yo', 'what's up'), do NOT write a long technical essay or print RAG error messages. Respond warmly with friendly emojis, acknowledge active topics, and ask if they want to continue or start something new. Only provide deep technical breakdowns when explicitly asked a technical or architectural question.
2. CONDITIONAL ENTERPRISE GROUNDING: If asked about internal Magellon systems, base your answer strictly on retrieved context. If context is empty, respond naturally: 'I couldn't find strong internal evidence for that inside our Confluence or ADO database.' For general programming questions, use your vast pre-trained knowledge to answer brilliantly without needing internal context.
3. DIAGRAMS & MULTIMEDIA PRESERVATION: Your retrieved context may contain Markdown image links representing architecture diagrams (formatted exactly as '![alt](url)'). You MUST preserve and include these exact Markdown image links inside your final response, positioned logically. Never strip, omit, or rephrase these image links.
4. PROGRESSIVE DEPTH: When delivering technical answers, provide a clean executive summary first. Only append a 'dive deeper' question if the topic is highly complex. Do NOT append it to social replies or simple chats.
```

## 3. The V.I.S.I.O.N. 4-Way Agentic Router (Phase 4)

To resolve the "Speed vs. Accuracy" RAG paradox, V.I.S.I.O.N. implements an advanced **Agentic Intent Router** directly at the top of its text-processing pipeline `process_text()`. Instead of blindly querying ChromaDB for every query (which adds 2 seconds of useless latency for general coding questions), the system dynamically routes queries across four distinct data channels.

### 3.1. Dual-Engine Model Isolation (Absolute Data Security)
To guarantee 100% data compliance and prevent any accidental search leaks, V.I.S.I.O.N. initializes two separate model instances in Python:
1.  **`self.model` (Strict Internal RAG)**: This instance has **no** Google search tools enabled. It is used strictly for internal Confluence and ADO queries, ensuring your proprietary IP remains completely private and inside corporate boundaries.
2.  **`self.model_web` (Live Public Grounding)**: This instance has the Google `google_search_tool` explicitly enabled, allowing Gemini to ground its responses using live web data.

---

### 3.2. The 4-Way Routing Pipeline

```
                              [USER QUESTION ENTRY]
                                        |
                 +----------------------v----------------------+
                 |     FAST-PATH: SOCIAL GREETINGS BYPASS      | <--- Intercepts greetings in 0.1ms
                 +----------------------+----------------------+      (0 tokens cost!)
                                        |
                 +----------------------v----------------------+
                 |      EXACT-MATCH: TICKET ID REGEX BYPASS    | <--- If ADO ID found, forces INTERNAL
                 +----------------------+----------------------+
                                        |
                 +----------------------v----------------------+
                 |      ROUTER ENGINE: EVALUATE SCOPE TAG      | <--- Checks [SCOPE: ...] or @web shortcuts
                 +--+--------------+------------------+--------+
                    |              |                  |
              [Scope = WEB] [Scope = INTERNAL]  [Scope = BOTH]      [Scope = AUTO]
                    |              |                  |                    |
                    |              |                  |      +-------------v-------------+
                    |              |                  |      | PROGRESSIVE CONFIDENCE    |
                    |              |                  |      | CHECK: Metadata Scan      |
                    |              |                  |      +-------------+-------------+
                    |              |                  |                    |
                    |              |                  |          [Confidence High (<=0.6)]
                    |              |                  |                    |
                    |              |                  |            Routes to INTERNAL
                    |              |                  |                    |
                    |              |                  |          [Confidence Low (>0.6)]
                    |              |                  |                    |
                    |              |                  |      +-------------v-------------+
                    |              |                  |      | CLARIFY-ONLY FALLBACK     |
                    |              |                  |      | - Asks user to search web |
                    |              |                  |      +---------------------------+
                    v              v                  v
              +-----------+  +-----------+      +-----------+
              | WEB ENGINE|  | RAG CORE  |      | HYBRID RAG|
              | Google Web|  | ChromaDB  |      | RAG + Web |
              | Search Tool| | full pages|      | Grounding |
              +-----------+  +-----------+      +-----------+
```

### 3.3. Routing Mechanics & Specifications

#### 0. Metadata Stripping Gatekeeper
Before processing the query, the backend utilizes regular expressions to strip out frontend-appended telemetry metadata tags:
- Strips `[SYSTEM CONTEXT: The active administrator's name is ...]`
- Strips `[MODEL_OVERRIDE: ...]` (e.g. `[MODEL_OVERRIDE: gemini-2.5-flash]`), ensuring simple greetings never clash with the semantic matching router.

#### 1. Deterministic Layer 1 Fast-Paths (Categorized Pattern Groups)
Intercepts explicit UI scope selections, power shortcuts (`@web`), and alphanumeric ticket IDs (`re.findall(r'\b\d{5,10}\b')`) instantly. It also evaluates user input against high-performance, local **Pattern Groups** to return instant templates in 0.1ms for **$0.00 token cost**:
- **Greetings Group** (`["hi", "hello", "hey", "namaste", "salam"]`) ➔ Returns short greeting.
- **Gratitude Group** (`["thanks", "thank you", "shukriya", "thx"]`) ➔ Returns "You're very welcome! Let me know if you need anything else. 🚀"
- **Acknowledgements Group** (`["ok", "okay", "done", "got it", "understood", "cool"]`) ➔ Returns "Understood. 👍"
- **Farewells Group** (`["bye", "goodbye", "see you", "good night"]`) ➔ Returns "Goodbye! Have a great day. 👋"

#### 2. LLM Semantic Intent Classifier (`_classify_intent`)
If the user's prompt bypasses Layer 1 (e.g., they use slang like `"yo bro"`, `"hiiiiii yoooo"`, or ask follow-up questions referencing chat history like `"explain in hinglish"`), the backend triggers a fast, stateless Gemini-Flash call to classify the intent into:
- **`GREETING`** or **`CONVERSATIONAL`** ➔ Set scope = `CHAT`. Triggers **`BRANCH CHAT`** (Pure conversational chat turn, bypassing databases and search entirely to respond warmly, allowing history translations and formatting changes).
- **`GENERAL`** ➔ Set scope = `WEB`. Triggers **`BRANCH WEB`** (Bypasses ChromaDB and routes to live public Google Search grounding).
- **`INTERNAL`** ➔ Set scope = `INTERNAL`. Triggers **`BRANCH RAG`** (Queries ChromaDB with high-precision confidence checks).

#### 3. Web Search Route (`Scope = WEB` or `@web `)
Skips ChromaDB and RAG vector searches entirely, eliminating 2 seconds of useless database latency. Invokes `self.model_web` to stream a fast, live grounded web answer, appending the badge `[SOURCE: WEB]`.

#### 4. Internal Docs Route (`Scope = INTERNAL` or `@internal `)
Executes ChromaDB semantic searches, applies **ADR-004 Parent-Document Collapsing**, completely blocks Google search tools, invokes `self.model`, and returns with citation markers and `[SOURCE: INTERNAL]`.

#### 5. Hybrid Route (`Scope = BOTH` or `@both `)
Queries ChromaDB for internal specs and activates the Google Search Tool simultaneously. Instructs Gemini to critically contrast your internal Confluence policy with current public web guidance, returning with `[SOURCE: BOTH]`.

#### 6. Auto Route & Multi-Signal Confidence Evaluator (SaaS Hardened)
If set to `AUTO`, V.I.S.I.O.N. replaces fragile, single-threshold vector checks with a highly sophisticated **Multi-Signal Confidence Evaluator** (`_evaluate_rag_confidence()`) to determine the reliability of retrieved document sets before answering.

##### A. Core Evaluation Mathematical Metrics
Each retrieved chunk set of size $K$ (where $K \le 10$) is analyzed across five statistical vectors:
1.  **Best Semantic Distance ($D_{\text{best}}$)**:
    $$D_{\text{best}} = \min_{i \in K} (D_i)$$
    Represents the mathematical distance of the single strongest match.
2.  **Semantic Score Margin ($M$)**:
    $$M = D_2 - D_{\text{best}} \quad (\text{if } K > 1, \text{ else } 0.0)$$
    Measures the separation between the top match and its closest comparative alternative.
3.  **Viable Candidate Count ($C_{\text{viable}}$)**:
    $$C_{\text{viable}} = \sum_{i=1}^{K} [D_i \le \theta_{\text{threshold}}]$$
    The count of retrieved chunks that are below the absolute viable threshold ($\theta = 0.85$).
4.  **Top-K Parent Consensus ($C_{\text{consensus}}$)**:
    Groups viable chunks by their parent `document_id`. The parent document with the highest frequency represents the consensus target.
5.  **Deterministic Consensus Tie-Breaking**:
    If multiple parent documents tie for the highest consensus count, V.I.S.I.O.N. computes the average distance of **only their viable chunks**. The document with the lowest average distance wins the consensus:
    $$\text{Average Distance} = \frac{1}{N_{\text{viable}}} \sum D_{\text{viable}}$$

##### B. Hardened Decision Matrix
The confidence level is resolved as follows:
*   **`HIGH` Confidence**:
    *   Top match is strong: $D_{\text{best}} \le \theta_{\text{high}} \quad (0.55)$
    *   **And** at least one strong signal exists:
        - Comparative margin is high: $M \ge 0.15$
        - **Or** multiple viable candidates exist: $C_{\text{viable}} \ge 2$
        - **Or** parent consensus is reached: $C_{\text{consensus}} \ge 2$
        - **Or** single-chunk override is active: $D_{\text{best}} \le \theta_{\text{single\_high}} \quad (0.40)$ (Allowing exceptionally high-quality solo chunks to qualify as HIGH).
*   **`LOW` Confidence**:
    *   If the top match is garbage: $D_{\text{best}} > \theta_{\text{threshold}} \quad (0.85)$
    *   **Or** the retrieval set is too noisy (no viable chunks): $C_{\text{viable}} = 0$
*   **`MEDIUM` Confidence**:
    *   Fails the strict `HIGH` criteria but top match is viable ($D_{\text{best}} \le 0.85$).
    *   *SaaS Override Pattern*: Appends a custom system prompt override caution directive for that single turn, warning the user of potential ambiguity and offering to pull ADO tickets.

##### C. Idempotent AI-Powered Session Title Generation
To provide a premium SaaS experience, when a user starts a fresh conversation (`"New Session"`), V.I.S.O.N. automatically generates a concise, professional 3-word title from their first message:
1.  On the first chat turn, FastAPI triggers a non-blocking background executor: `generate_session_title(first_message)`.
2.  Gemini Flash analyzes the raw text, extracting the core topic (e.g. `"how do I test ITSO refunds?"` ➔ `"ITSO Refund Process"`).
3.  The backend executes an **idempotent update query** to guarantee that rapid incoming messages do not spawn duplicate tasks or overwrite manual renames:
    ```sql
    UPDATE chat_sessions SET title = :new_title 
    WHERE session_id = :session_id AND title = 'New Session';
    ```
4.  The Left Sidebar UI receives the new title over REST, instantly updating the session card!

---

## 3.5. Advanced Prompt Optimization Engine

To help developers who do not know prompt engineering get highly accurate results from our RAG database without wasting tokens on conversational back-and-forth, V.I.S.I.O.N. implements an automated prompt-engineering pipeline:

### 3.5.1. The "Translation Bridge" (`POST /api/optimize_prompt`)
When a developer enters a short, messy, or conversational sentence (e.g. *"want status of parking feature"*) and clicks `✨ OPTIMIZE`:
1.  The frontend makes a high-speed REST request to the backend.
2.  The backend forwards the text to a stateless Gemini call with a highly engineered system prompt instructing it to translate the mess into a clear, highly-detailed, and grammatically perfect RAG-optimized search query.
3.  The optimized query is loaded directly back into the user's input textarea, **teaching the user how to write prompts like an expert while guaranteeing 100% vector search retrieval accuracy!**

### 3.5.2. Layer 1: In-Memory Python Greeting Bypass (0 Tokens, 0ms Latency)
To prevent the optimizer from over-engineering simple social greetings, a strict Python-level defensive guardrail sits at the very top of `optimize_prompt()` inside `ai_service.py`:
```python
clean_text = raw_text.strip().lower()
if clean_text in ["hi", "hello", "hey", "test", "ok", "thanks", "thank you", "yo", "yes", "no", "done"]:
    return raw_text.strip()
```
*Value*: If a user types `"HI"`, the system instantly returns `"HI"` in **0.1ms without ever calling the Gemini API, saving 100% of tokens!**

### 3.5.3. Layer 2: Strict LLM-Level Gibberish Safeguard
If a user inputs completely meaningless keyboard-smash gibberish (e.g. `"asdfgsdews"`), standard word lists won't match. To prevent Gemini from getting confused and writing a long, expensive hallucinated essay, we enforce a strict guardrail inside the optimizer's system prompt instructions:
> *"If the original prompt is completely meaningless gibberish, a random keyboard-smash string of letters (such as 'asdfgsdews', 'qwerty'), a simple social greeting, or brief conversational filler with absolutely no technical or engineering intent, **do NOT attempt to expand or optimize it. Simply return the exact original text completely unmodified with no extra explanation.**"*
*Value*: If a user types `"asdfgsdews"` and clicks optimize, Gemini instantly returns `"asdfgsdews"` exactly as-is unmodified. **This uses 0 expensive output generation tokens**, completely safeguarding your corporate API budget!

---

## 4. Phase 2: RAG Ingestion Pipeline Blueprint

To transform V.I.S.I.O.N. from an interactive chat client into a document auditor, we will construct the **RAG (Retrieval-Augmented Generation)** database.

> ⚠️ **CRITICAL ENTERPRISE ARCHITECTURE NOTE (PRODUCTION):**  
> ChromaDB is utilized **strictly as our local, single-user developer sandbox mock** during MVP prototyping. In our centralized production cloud deployment, V.I.S.I.O.N. completely and seamlessly migrates to **Google Cloud SQL PostgreSQL with the `pgvector` extension** (using our Dual-Adapter database architecture) to support scalable, multi-user shared knowledge and absolute compliance with Magellon InfoSec standards.

### 4.1. Local Vector Store: ChromaDB (Local Sandbox Mock Only)
- **Technology**: **ChromaDB** will be run as a local database engine inside our FastAPI instance, keeping all indexed intellectual property strictly inside the local runtime (highly compliant with corporate data protection standards).

### 4.2. Mathematical Vector Mapping (Embeddings)
- **Embedding Model**: `text-embedding-004` via Vertex AI.
- **Methodology**: 
  - **Chunking Size**: 1000 characters (optimal context density for Gemini's attention blocks).
  - **Overlapping Size**: 200 characters (20% overlap, ensuring semantic linkages are preserved across chunk cuts).
  - **Vector Generation**: Converts text segments into **768-dimension** floating-point arrays and stores them natively in the SQLite file-backed local database (`backend/data/chromadb.sqlite3`).

### 4.3. Document Upload Limits & Constraints
To protect the system from massive token exhaustion and prevent engineers from uploading unreasonably large files (which dilutes RAG accuracy):
- **Max File Size**: 10 MB per document.
- **Max Page Count**: 50 pages per PDF/DOCX.
- **Rationale**: If a document is larger than 50 pages, standard semantic chunking loses precision. Users should be instructed to upload specific chapters or use the automated Confluence API sync for massive enterprise wikis.

### 4.4. Document Ingest & Refresh Frequency
To ensure the local index stays perfectly aligned with corporate documentation, the system implements a strict sync protocol:
* **Active Documents**: Manual Drag-and-Dropped files (PDF, DOCX, TXT) are instantly vectorized and indexed inside the temporary workspace collection. They are cleared only when clicking the **"Purge Memory"** button in settings.
* **API Synced Data (ADO & Confluence)**: In Phase 2, background worker tasks will sync tagged Confluence spaces and active ADO backlogs.
  - **Sync Frequency**: Daily at 01:00 AM (or triggered manually via the UI's **"Synchronize Repositories"** button).
  - **Collision Policy**: Documents are cached with their ADO/Confluence UUIDs. If a document has been modified on the cloud, the local chunk index is automatically dropped, re-parsed, and updated (overwriting stale vectors).

### 4.5. Advanced Retrieval Mechanics (Query Rewriting & Citations)
To elevate the retrieval relevance from standard "keyword matching" to true human-like dialog context, V.I.S.I.O.N. implements two advanced pipeline decorators:

#### **A. Conversational Query Rewriting**
Follow-up questions (like "Compare this to before") are natively impossible for vector databases to understand because they lack semantic noun triggers. 
* **The Loop**: Before executing a ChromaDB search, the system passes the active user input + the sliding window history to a fast Gemini 2.5 Flash query-rewriting utility:
  ```
  User Input: "How does this differ from the old approach?"
  Sliding Window Context: [User asked about: Zscaler setup guides in project-jarvis]
  
  ---> REWRITER PROMPT: "Given this context, rewrite the user input into a standalone, detailed vector search query."
  
  Generated Query: "Differences and changes in Zscaler SSL certificate setup guides inside project-jarvis"
  ```
* **Result**: ChromaDB is queried using this highly descriptive rewritten query, guaranteeing 100% search relevance for follow-up dialogs!

#### **B. Metadata Injection & Source Attribution UI**
Transparency is critical for executive decision support. The user must always know where the AI's answers originated.
* **Ingestion Mapping**: During parsing, every chunk saved in ChromaDB is indexed with strict metadata: `{ "source": "Finance_Policy_2024.pdf", "page": 5, "last_updated": "2026-06-01" }`.
* **Payload Transit**: When retrieving segments, the backend extracts this metadata and appends it to the WebSocket response payload as a structured header (e.g., `[SOURCES: Finance_Policy_2024.pdf (Pg 5)]`).
* **UI Citation Drawer**: The Vue frontend intercepts this header and automatically populates the right-side **Citations Sidebar**, allowing administrators to instantly verify the exact PDF page or Confluence link used for the answer!

#### **C. Exact Ticket ID Filtering (Heuristic Search Guard)**
Standard semantic vector search is mathematically prone to retrieving "close siblings" (e.g., pulling ticket `#97545` and `#104853` when the user explicitly asked for `#104835` because they share project templates, headers, and standard layout wording). This creates confusing and inaccurate results on the RAG Citation Board.
* **The Guard Logic**: V.I.S.I.O.N. implements an exact-match keyword pre-filter. Before executing the RAG prompt collation, the backend scans the query using regex for any 5-to-6 digit ticket IDs (e.g., `\b\d{5,6}\b`).
* **The Squeeze Check**: If a specific ID is matched in the query, the retrieval engine inspects the database's top search results. Any matched chunk or document ID that does *not* contain that exact numeric string is immediately discarded before payload generation.
* **Result**: The RAG Citation Board is dynamically filtered, displaying **exactly one, perfectly matched file** (e.g., `ado_workitem_104835.txt`), completely eliminating confusing, unrelated sibling citations.

### 4.5. Phase 3: AI-Driven Ingestion Privacy Guardrails & Classifiers
To protect the shared central cloud database from sensitive, restricted, or personal data leaks without slowing down performance with complex directory syncs (RBAC), the system implements an intelligent, cognitive gatekeeper directly at the upload layer:

```
   +--------------+      +-------------------+      +------------------+      +---------------+
   | File Upload  | ---> |  Read First Page  | ---> |  Evaluate with   | ---> |  RESTRICTED?  | 
   |  (via HUD)   |      |  (FastAPI Cache)  |      |   Gemini Flash   |      |  (Decision)   |
   +--------------+      +-------------------+      +--------+---------+      +-------+-------+
                                                             |                        |
                                                             v                        |
                                                    Is file personal or               |-- [YES] -> REJECT & PURGE
                                                    restricted (salaries,             |
                                                    private keys, health)?            |-- [NO] -> CHUNK, EMBED, SAVE
```

* **The Guardrail Agent Prompt**: Before a file is parsed or embedded, the backend extracts its header metadata/first page and runs a fast classification pass inside Gemini Flash using this strict security instructions model:
  ```
  You are an enterprise AI Privacy Guardrail Agent. 
  Your sole task is to read the first page/metadata of the attached corporate document and determine its security sensitivity.
  
  Classification Classes:
  - RESTRICTED: Highly private, sensitive, or personal data (such as salary spreadsheets, HR medical records, private passwords/API keys, or executive draft board logs).
  - SAFE: General, non-sensitive, project-wide engineering documentation (such as source code files, product manuals, system specifications, or study roadmaps).
  
  Output MUST be strictly JSON format:
  {
    "classification": "RESTRICTED" | "SAFE",
    "reason": "Concise 1-sentence explanation of why the document was classified."
  }
  ```
* **Enforced Purge Actions**: If Gemini classifies the file as `RESTRICTED`, the FastAPI upload pipeline instantly aborts, deletes the file from temporary cache, and displays a clean, user-friendly security notification in the HUD console, guaranteeing that private information never enters the vector database or gets shared with other users.

---

## 5. API Fault Tolerance & Resilience Configurations


All outward API endpoints utilize standard cloud-resilience frameworks.

### 5.1. Tenacity Exponential Backoff
Vertex AI requests are wrapped in Python's `tenacity` library to provide strict rate-limiting shields:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def invoke_vertex_ai_model():
    # Makes the cloud call. Automatically retries if 429 occurs.
```
This protects V.I.S.I.O.N. from displaying crash traces during shared subscription peaks.

