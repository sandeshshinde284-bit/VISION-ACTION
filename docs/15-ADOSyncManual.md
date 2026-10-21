# V.I.S.I.O.N. Azure DevOps (ADO) Synchronization Manual

Welcome, Administrator. This manual defines the operational guidelines, security configurations, and troubleshooting steps for the Azure DevOps (ADO) Synchronization Engine within the V.I.S.I.O.N. Suite.

---

## 1. Synchronization Architecture
Unlike Confluence, which is crawled recursively page-by-page, the V.I.S.I.O.N. ADO syncer utilizes **WIQL (Work Item Query Language)** and REST APIs to fetch, parse, and semantically index user stories, tasks, bugs, and discussions.

### 💸 1.1. Hybrid ADO Indexing (ADR-004 Compliance)
To prevent your local or cloud vector databases (ChromaDB) from bloating with massive ticket descriptions and comment logs, the syncer operates a **Dual-Storage Split**:
1.  **ChromaDB (Slim Semantics):** Indexes strictly a high-density, lightweight metadata string (e.g. `ADO Ticket ID: #107860 | Title: ... | Status: Active`).
2.  **Relational SQL Store (Full Specifications):** Saves the complete, original HTML description, reproduction steps, and discussion comments inside your SQLite/PostgreSQL `documents` database table.
3.  **The Result:** Perfect semantic search discovery, but clicking "Explain" inside the HUD pulls the complete, raw historical description from SQL, giving you the best of both worlds!

---

## 2. Configuration & Security (Google Secret Manager)
To connect to Magellon's private Azure DevOps server, V.I.S.I.O.N. reads three environment variables:

1.  **`ADO_URL`**: The base URL of your Azure DevOps Organization (e.g. `https://dev.azure.com/worldline`).
2.  **`ADO_PROJECT`**: Your target corporate project name (e.g. `project-vision`). Scopes all crawls strictly to this project.
3.  **`ADO_PAT`** (Sensitive): Your personal access token (PAT).

### 🔐 2.1. Dynamic Token Rotation in Google Secret Manager
During deployment, `ADO_PAT` is declared inside **Google Secret Manager (GSM)** and dynamically mounted to the Cloud Run container.
*   **When your PAT expires:**
    1.  Open GCP Console ➔ Navigate to **Secret Manager**.
    2.  Click on **`ado-pat-token`** ➔ Click **Add New Version**.
    3.  Paste your newly generated Azure DevOps PAT ➔ Click **Save**.
    *   *Cloud Run will dynamically, automatically pick up the new token version on its next request or boot without any code redeployments!*

---

## 3. How to Run & Trigger Syncs (Step-by-Step)

### 📍 3.1. Manual Initial Full Hydration (From Your Computer)
To populate your brand-new, empty Cloud SQL PostgreSQL and ChromaDB databases with all historic sprint tickets from scratch, execute this manual `POST` request from your laptop terminal (pointing to your active Cloud Run Backend URL):
```powershell
# Triggers sync for all tickets modified in the last 100,000 minutes (~2 months)
Invoke-RestMethod -Method Post -Uri "https://vision-action-backend-[xxxxx].run.app/api/sync?minutes=100000"
```

### 📍 3.2. Automated 3-Hour Delta Syncs (Google Cloud Scheduler)
Your automated `vision-confluence-sync-scheduler` runs every 3 hours natively:
*   **Frequency:** `0 */3 * * *` CRON.
*   **Action:** Triggers `POST /api/sync` on Cloud Run.
*   **Result:** Because no `minutes` parameter is passed, V.I.S.I.O.N. automatically defaults `minutes` to `180` (3 hours)—perfectly, cleanly fetching only the delta updates that occurred since the last run!

---

## 4. Verification & Troubleshooting
*   **Check Sync Logs:** In GCP Console, open your Cloud Run service and view logs. Successful ADO crawls will print:
    👉 `[INFO] - Polling ADO for work items modified since [YYYY-MM-DD] using WIQL...`
    👉 `[INFO] - Found [N] ADO work items updated.`
    👉 `[INFO] - Successfully synchronized ADO Work Item [Title]!`
*   **Verify Database Records:** Open the V.I.S.I.O.N. cockpit, choose **Internal Docs** as your search scope, and query an ADO ticket number (e.g., `107860`). If successfully synchronized, V.I.S.I.O.N. will instantly deliver a beautiful, detailed markdown report of the ticket, complete with parent specs and discussion logs!
