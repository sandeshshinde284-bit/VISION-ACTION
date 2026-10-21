# V.I.S.I.O.N. Database-Driven Confluence Sync Manual

This document contains the complete architectural specifications, database schemas, sequence flows, local/cloud running instructions, and testing commands for the **V.I.S.I.O.N. Database-Driven Confluence Synchronization Engine**.

---

## 1. Core Architectural Theory & Pipeline Flow

The Confluence Ingestion Engine is designed to solve the critical enterprise challenges of **RAG context accuracy, data-hygiene compliance, and FinOps cost efficiency**.

```text
  +-------------------------------------------------------------------------+
  |                        MAGELLON CUSTOMER DOMAIN                        |
  +-------------------------------------------------------------------------+
                                       |
                     [POST /api/sync/confluence?minutes=N]
                                       |
                                       v
         +-----------------------------------------------------------+
         |                 V.I.S.I.O.N. FastAPI Core                 |
         +-----------------------------------------------------------+
                                       |
                        1. Query Active Space Targets
                                       |
                                       v
         +-----------------------------------------------------------+
         |            Database config_sync (PROJWT, ERK)             |
         +-----------------------------------------------------------+
                                       |
                   2. Sequential Paginated Atlassian Requests
                                       |
                                       v
         +-----------------------------------------------------------+
         |                 Atlassian Confluence REST                 |
         +-----------------------------------------------------------+
                                       |
                  3. Clean Markdown & Data-Hygiene Blocks
                                       |
                                       v
         +-----------------------------------------------------------+
         |    Filter out 'draft', 'archived', 'deleted', 'trashed'   |
         +-----------------------------------------------------------+
                                       |
                     4. FinOps Match-Version Check
                                       |
                                       v
         +-----------------------------------------------------------+
         |      If version matches existing database doc -> SKIP      |
         |      (Saves 100% token embedding costs and latency!)      |
         +-----------------------------------------------------------+
                                       |
                     5. Generate Summary & Embed
                                       |
                    +------------------+------------------+
                    |                                     |
                    v                                     v
       +-------------------------+           +-------------------------+
       |   knowledge_base Table  |           |     documents Table     |
       |  (Postgres/Chroma RAG)  |           | (SQLite/Postgres Docs)  |
       +-------------------------+           +-------------------------+
```

### 💎 The 4 Pillars of the Sync Architecture:

1.  **Database-Driven Space Selection (`config_sync` table):**
    Instead of hardcoding Confluence spaces inside `.env` variables (which require container restarts and downtime to update), we store target spaces in a dedicated `config_sync` table. You can add, toggle, or delete spaces inside your database on-the-fly, and the background loop will dynamically execute over the active list with **0% downtime**.
2.  **Strict Data-Hygiene Filter:**
    To protect the RAG brain from retrieving outdated specifications or draft notes, the python engine inspects the `status` field of each document. Any page with a status of `"draft"`, `"archived"`, `"deleted"`, or `"trashed"` is **instantly blocked and ignored**. Only active, `"current"` live production pages are indexed.
3.  **Strict FinOps Token Saving (Skip unchanged files):**
    Before executing expensive Vertex AI embedding calls, the sync loop queries the database. If the page is already vectorized and the version matches, **it skips vectorization instantly**, saving 100% of your token costs!
4.  **Flexible Dual Ingestion (Surgical Delta vs. Full Hydration):**
    *   *Delta Ingestion:* If `minutes` is provided, it runs a highly-efficient CQL (Confluence Query Language) search for pages modified inside that exact window (e.g. last 1 day, last 2 days), running in milliseconds.
    *   *Full Hydration:* If `minutes` is omitted/None, it runs a deep recursive space crawl, following Atlassian's `_links.next` pagination headers to ingest **100% of the pages** in your spaces.

---

## 2. In-Depth Confluence-to-RAG Pipeline Mechanics

How does a live Confluence document become a contextual reference in V.I.S.O.N.'s brain? Here is the exact step-by-step mathematical and logical lifecycle of a Confluence page:

### 🔄 Stage 1: Extraction & Handshake
*   **The Action:** The backend initiates an authenticated HTTPS request against your live corporate Confluence cloud endpoint (`https://worldline.atlassian.net/wiki/rest/api/content`).
*   **The Handshake:** Authenticates using your **Atlassian Personal Access Token (PAT)** or `email:api_token` format.

### 🧹 Stage 2: Native HTML-to-Markdown Parsing
*   **The Problem:** Confluence stores page contents as raw, nested, and noisy XML/HTML body storage. Sending this raw markup directly to Gemini explodes token costs and ruins chunking alignments.
*   **The Solution:** Our native **`HTMLToMarkdownParser`** (inheriting Python's native, highly stable `html.parser.HTMLParser`) parses the HTML tree locally with **zero external dependencies** (no `BeautifulSoup4` overhead). 
*   **The Conversion:**
    *   Converts headings, paragraphs, and list items into clean, readable Markdown syntax.
    *   Surgically extracts `<img src="...">` source strings and compiles them into standard markdown image tags (`![Diagram](src)`) so **your visual diagrams and flowcharts render natively inside V.I.S.I.O.N.'s chat bubbles!**

### 🧠 Stage 3: Generative LLM Summarization
*   **The Action:** Spawns a fast, stateless Gemini 2.5 Flash call. 
*   **The Prompt:** *"Summarize the core purpose and key architectural deliverables of the following technical document in exactly 2 professional sentences."*
*   **The Purpose:** This dynamic summary is stored inside the relational `documents` table. It provides a lightweight semantic summary of the entire document, enabling exceptionally fast indexing and quick-reference queries!

### 📈 Stage 4: Semantic Chunking & Vertex AI Embeddings
*   **The Action:** The clean markdown text is split into semantic, overlapping chunks using the recursive character text splitter.
*   **The Vectorization:** Each chunk is sent to the Google Vertex AI **`text-embedding-004`** model, which translates the raw text into a highly precise **768-dimension mathematical Float Array (Vector)** representing its exact semantic meaning.
*   **The Storage:** 
    *   The vector floats and lightweight metadata (source path, document ID) are saved in the **`knowledge_base`** table (Chroma DB locally, or PostgreSQL pgvector in the cloud).
    *   The raw full-text markdown is saved in the **`documents`** table (SQLite locally, or PostgreSQL in the cloud) to support **ADR-004 Parent-Document Collapsing RAG** (allowing V.I.S.I.O.N. to read the full page context rather than just a cut-off chunk!).

    ### 🏷️ Stage 5: Descriptive Filename Generation & Frontend Formatting
    *   **The Problem:** Raw page downloads and sync files on disk are highly difficult to debug if they are only stored by numeric ID (e.g., `54321.txt`).
    *   **The Solution**: When crawling Atlassian endpoints, `sync_connectors.py` generates highly descriptive text filenames containing the Space Key, the Page Title, and the original page ID (e.g., `confluence_page_PROJWT_PageTitle_ID.txt`).
    *   **The UI Experience**: In the Admin Cockpit (`HomeView.vue`), these raw filenames are parsed in real-time using regular expressions, stripping out raw IDs and underscores, and rendering them cleanly to the administrators as 📄 `[Confluence] PROJWT Page Title`.

---

## 3. Database Table Schemas (PostgreSQL & SQLite Parity)

V.I.S.O.N. maintains perfect schema parity between SQLite (local development) and PostgreSQL (cloud production). The tables are **automatically created and bootstrapped on bootup** (no manual SQL commands needed!).

### 🗃️ Table 1: `config_sync` (Database-Driven Targets)
Stores the active workspaces, space keys, and projects to synchronize.

| Column Name | Data Type (Postgres) | Data Type (SQLite) | Key Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`id`** | `SERIAL` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique row identifier. |
| **`target_type`** | `VARCHAR(50)` | `TEXT` | `NOT NULL` | The source system type (`CONFLUENCE_SPACE` or `ADO_PROJECT`). |
| **`target_key`** | `VARCHAR(100)` | `TEXT` | `NOT NULL` | The specific space key or project (e.g. `PROJWT`, `ERK`, `WLMTSConsole`). |
| **`is_active`** | `BOOLEAN` | `INTEGER` | `DEFAULT TRUE` / `1` | Enables/Disables syncing a specific target without deleting it. |
| **`last_synced_at`** | `TIMESTAMP` | `DATETIME` | `NULL` | Timestamp of when this workspace last completed a successful sync run. |

### 🗃️ Table 2: `documents` (Parent-Document Storage)
Stores the raw, full-text parent documents to support Parent-Document Collapsing RAG (ADR-004).

| Column Name | Data Type (Postgres) | Data Type (SQLite) | Key Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`document_id`** | `VARCHAR(100)` | `TEXT` | `PRIMARY KEY` | Unique ID of the parent page (e.g., `confluence_page_54321`). |
| **`title`** | `VARCHAR(255)` | `TEXT` | `NOT NULL` | The readable title of the document. |
| **`content`** | `TEXT` | `TEXT` | `NOT NULL` | The complete, cleaned raw Markdown content of the page. |
| **`source_system`** | `VARCHAR(50)` | `TEXT` | `NOT NULL` | Origin system (`CONFLUENCE` or `ADO`). |
| **`space_key`** | `VARCHAR(50)` | `TEXT` | `NOT NULL` | Associated Space or Project Key. |
| **`summary`** | `TEXT` | `TEXT` | `NULL` | The dynamic 2-sentence Gemini-generated summary. |
| **`status`** | `VARCHAR(50)` | `TEXT` | `NULL` | Ingestion status (`Active`). |
| **`doc_type`** | `VARCHAR(50)` | `TEXT` | `NULL` | Document category (`Confluence`, `User Story`, etc.). |
| **`version`** | `INTEGER` | `INTEGER` | `DEFAULT 1` | The numerical version of the document (used for FinOps skips). |
| **`timestamp`** | `TIMESTAMP` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Time this record was written. |

### 🗃️ Table 3: `knowledge_base` (Vector Embeddings Store)
Stores the vectorized semantic slices for high-speed multi-dimensional searches.

| Column Name | Data Type (Postgres) | Data Type (ChromaDB) | Key Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`chunk_id`** | `VARCHAR(255)` | `String ID` | `PRIMARY KEY` | Unique identifier of the semantic text slice. |
| **`embedding`** | `vector(768)` | `Float Array` | `NOT NULL` | **768-dimension Vector Array** generated by Vertex AI. |
| **`content`** | `TEXT` | `Document` | `NOT NULL` | The raw text of the semantic chunk. |
| **`source_system`** | `VARCHAR(50)` | `Metadata string` | `NULL` | Origin system metadata. |
| **`space_key`** | `VARCHAR(50)` | `Metadata string` | `NULL` | Target space metadata. |
| **`document_id`** | `VARCHAR(100)` | `Metadata string` | `NULL` | Foreign key referencing the parent `documents` table. |

---

## 4. Visual GUI Database Viewer Guides (Local vs. Cloud)

As a developer or administrator, you do not have to write raw console commands to manage your data! You can use beautiful, free, and industry-standard GUI database tools to visually browse, edit, and audit your tables.

### 💻 A. Locally (Viewing SQLite):
Your local SQLite database is stored on your laptop disk at `C:\Users\w114216\.gemini\tmp\vision\data\chat_history.db`.

*   **The Recommended Tool: VS Code SQLite Viewer Extension**
    1.  Open VS Code on your machine.
    2.  Go to **Extensions** (Ctrl + Shift + X) and search for **"SQLite Viewer"** by *Florian*. Install it!
    3.  Go to your file explorer, right-click `chat_history.db`, and select **"Open with SQLite Viewer"**.
    4.  **The Experience:** VS Code will render your tables (messages, documents, config_sync) in a beautiful, visual spreadsheet! You can view, search, and filter columns instantly!
*   **The Standalone Tool: DB Browser for SQLite (Free Desktop App)**
    1.  Download and install **DB Browser for SQLite** (completely free and open-source).
    2.  Open the app, click **"Open Database"**, and select your `chat_history.db` file.
    3.  Go to the **"Browse Data"** tab to view all of your tables visually!

### ☁️ B. In the Cloud (Viewing Cloud SQL PostgreSQL):
Your cloud database is a fully managed PostgreSQL instance running inside Magellon's private GCP network.

*   **The Recommended Tool: DBeaver Community (Free Universal GUI)**
    1.  Download and install **DBeaver Community Edition** (the absolute standard for database managers).
    2.  Click **"New Connection"** and select **PostgreSQL**.
    3.  **Establish Secure VPC Tunneling:** Because your Cloud SQL has a **Private IP** for enterprise compliance, you cannot connect to it directly from your home internet. You must use DBeaver's native **SSH / Socks Proxy** tab to tunnel through your corporate bastion host or VPC network connector!
    4.  Input your secret database credentials:
        *   **Host:** `[Your private Cloud SQL PostgreSQL IP]`
        *   **Database:** `vision_knowledge_base`
        *   **Username:** `postgres`
        *   **Password:** `[Your secure database administrative password]`
    5.  Once connected, you can browse tables, alter rows, and audit RAG vectors visually!

---

## 🔒 5. Google Cloud Secret Manager (GSM) Integration

You asked: *"Secret Manager Credentials: this what is this?"*

In enterprise applications, **never write plain text passwords or API keys inside code files or standard `.env` files on disk!** If a hacker breaches your server, they can read those files instantly and steal your corporate data.

**Google Secret Manager (GSM)** is a secure, cloud-native vault (like a physical safe) provided by GCP to store your sensitive credentials (passwords, PAT keys, DB ports).

```text
  +-----------------------------------------------------------+
  |              GCP Secret Manager (Secure Vault)            |
  |  - Store 'vision-confluence-pat' => "email:token"         |
  |  - Store 'vision-db-password'    => "SecretPassword123"   |
  +-----------------------------+-----------------------------+
                                |
                     Secure Internal Reference
                                |
                                v
  +-----------------------------------------------------------+
  |               Google Cloud Run Backend Service             |
  |  - Bind 'CONFLUENCE_PAT' => Secret 'vision-confluence-pat'|
  |  - Bind 'PG_PASSWORD'    => Secret 'vision-db-password'   |
  +-----------------------------------------------------------+
```

### ⚙️ How the Security Binding works:
1.  You upload your Atlassian PAT key to Secret Manager and name it `vision-confluence-pat`.
2.  In your **GCP Cloud Run Console**, you edit your container variables.
3.  Instead of typing the value of `CONFLUENCE_PAT` as plain text, you select **"Reference a Secret"** and bind it directly to `vision-confluence-pat`.
4.  **At Runtime:** When Cloud Run boots up, Google's cloud hypervisor securely injects the password straight into the memory of your running container. **There is never a plaintext password stored on your server disk, making your architecture 100% compliant with Magellon's strict InfoSec regulations!**

---

## 🚀 6. Local Setup, Execution, & Testing

Follow these steps to run and test the database-driven Confluence sync locally on your laptop:

### Step 1: Bootstrap the Local SQLite Database
We will delete any old database logs so the system boots fresh, initializes the new schema, and auto-seeds your live Magellon spaces (`PROJWT` and `ERK`):
```powershell
# Navigate to your backend directory
cd C:\SANDESH_AI\AI\vision\project-vision\backend

# Wipe old local database file
Remove-Item -Path "app/data/chat_history.db" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "data/chat_history.db" -Force -ErrorAction SilentlyContinue

# Boot the Python local FastAPI backend
.\.venv\Scripts\python.exe run.py
```
*Verify in your terminal logs that you see:*
> `[INFO] - Auto-seeding default corporate Confluence Space Keys: PROJWT and ERK.`
> `[INFO] - V.I.S.I.O.N. database schema initialized successfully for [LOCAL] mode.`

### Step 2: Verify Seeded Spaces locally
In a new PowerShell window, run this Python one-liner to verify SQLite has registered your default spaces:
```powershell
cd C:\SANDESH_AI\AI\vision\project-vision\backend
.\.venv\Scripts\python.exe -c "from app.services.db_service import db_service; print('Active Local Spaces:', db_service.get_active_sync_targets('CONFLUENCE_SPACE'))"
```
*Expected Output:*
> `Active Local Spaces: ['PROJWT', 'ERK']`

### Step 3: Trigger a Manual Delta Sync locally
We will trigger a manual delta sync to pull only pages modified in the last **24 hours (1440 minutes)**:
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/sync/confluence?minutes=1440"
```
*Expected API Response:*
```json
{
  "status": "success",
  "message": "Confluence delta sync for last 1440 minutes successfully scheduled in the background."
}
```
*Watch your Python terminal logs! You will see V.I.S.I.O.N. query your active SQLite table, find PROJWT and ERK, connect to Atlassian over HTTPS, skip drafts, and embed updated pages!*

### Step 4: Trigger a Deep Full Hydration Sync locally
To crawl, paginate, and pull **100% of all historical pages** inside `PROJWT` and `ERK`:
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/sync/confluence"
```

---

## 🏆 7. Comprehensive Testing Commands Cheat Sheet

Here is a copy-paste reference sheet of all operations commands for testing and managing your Confluence RAG Sync:

### 📡 A. Manual Ingestion Trigger Commands (REST API):

```powershell
# 1. Trigger delta sync for the last 30 minutes
Invoke-RestMethod -Method Post -Uri "https://[YOUR_PROD_URL]/api/sync/confluence?minutes=30"

# 2. Trigger delta sync for the last 1 day (1440 minutes)
Invoke-RestMethod -Method Post -Uri "https://[YOUR_PROD_URL]/api/sync/confluence?minutes=1440"

# 3. Trigger delta sync for the last 2 days (2880 minutes)
Invoke-RestMethod -Method Post -Uri "https://[YOUR_PROD_URL]/api/sync/confluence?minutes=2880"

# 4. Trigger deep, full paginated space hydration (crawls 100% of pages!)
Invoke-RestMethod -Method Post -Uri "https://[YOUR_PROD_URL]/api/sync/confluence"
```

### 💻 B. Local SQLite Database Administration (PowerShell):

```powershell
# 1. View all currently active spaces inside local SQLite
python -c "from app.services.db_service import db_service; print('Active Spaces:', db_service.get_active_sync_targets('CONFLUENCE_SPACE'))"

# 2. Add a new Confluence Space dynamically (e.g., Key: MAGELLAN)
python -c "from app.services.db_service import db_service; conn = db_service._get_connection(); cursor = conn.cursor(); cursor.execute(\"INSERT INTO config_sync (target_type, target_key) VALUES ('CONFLUENCE_SPACE', 'MAGELLAN')\"); conn.commit(); print('Space MAGELLAN added locally!')"

# 3. Pause/Disable a space locally (e.g., Key: ERK)
python -c "from app.services.db_service import db_service; conn = db_service._get_connection(); cursor = conn.cursor(); cursor.execute(\"UPDATE config_sync SET is_active = 0 WHERE target_type = 'CONFLUENCE_SPACE' AND target_key = 'ERK'\"); conn.commit(); print('Space ERK paused locally!')"

# 4. Resume/Enable a space locally (e.g., Key: ERK)
python -c "from app.services.db_service import db_service; conn = db_service._get_connection(); cursor = conn.cursor(); cursor.execute(\"UPDATE config_sync SET is_active = 1 WHERE target_type = 'CONFLUENCE_SPACE' AND target_key = 'ERK'\"); conn.commit(); print('Space ERK resumed locally!')"
```

### ☁️ C. Cloud SQL PostgreSQL Database Administration (PowerShell / psql):

If connected to your corporate cloud database (via local proxy tunnel or bastion host), you can manage your cloud sync spaces directly using **`psql`**:

```sql
-- 1. View all active cloud sync spaces
SELECT target_key, last_synced_at FROM config_sync WHERE target_type = 'CONFLUENCE_SPACE' AND is_active = TRUE;

-- 2. Add a new corporate cloud space dynamically (Zero-Downtime, no redeploys!)
INSERT INTO config_sync (target_type, target_key, is_active) VALUES ('CONFLUENCE_SPACE', 'SEC_AUDIT', TRUE);

-- 3. Pause a cloud space temporarily
UPDATE config_sync SET is_active = FALSE WHERE target_type = 'CONFLUENCE_SPACE' AND target_key = 'PROJWT';
```

---

## 8. Real-Time Cockpit Telemetry & Platform Status Modal

To provide administrators with complete, real-time diagnostic visibility across the platform, V.I.S.I.O.N. implements a high-fidelity **Platform Status Modal**:

### 🟢 The "Connected" Status Badge
- **Visual Feedback**: Located in the bottom status panel of the V.I.S.I.O.N. cockpit, a pulsing green "Connected" badge provides immediate validation that backend database connections and websocket sync sockets are live and healthy.
- **Role-Based Interaction**:
  - **ADMIN (`vision@1133`)**: The green badge is fully interactive. Clicking it opens a secure, glassmorphic **Platform Status Modal**.
  - **LEAD (`vision@lead`)**: The status badge renders as green and active, but is strictly **unclickable** to prevent exposure of deep system configurations and toggle switches to non-administrative leads.

### 🎛️ Inside the Glassmorphic Admin Status Cockpit
Clicking the badge opens a secure, premium modal overlay displaying real-time platform diagnostics:
1.  **Database Connection Health**: Green validation indicators representing active Cloud SQL PostgreSQL (cloud) or SQLite (local) pool health.
2.  **Separate Resource Counters**: Real-time totals showing exact synchronized assets partitioned by system type:
    - **Confluence Pages Ingested**: The total number of valid Confluence documents indexed in the relational `documents` table.
    - **ADO Tickets Synchronized**: The exact count of active, tracked Azure DevOps items.
3.  **Active Sync Targets**: A scrollable sub-pane displaying all space and project keys active in the database (`config_sync` table), allowing operators to instantly see what environments are being tracked and their last synchronization run timestamps.