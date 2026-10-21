# V.I.S.I.O.N. Installation & Operations Runbook

**Audience**: Administrators and Developers familiar with Python, Node.js, and Google Cloud Platform (GCP).  
**Document Status**: **Dynamically Maintained** (Automatically synchronized with every codebase update as mandated by `GEMINI.md`).

---

## 1. System Requirements & Environment Prerequisites

Before compiling or running any components of the V.I.S.I.O.N. cockpit, ensure the host machine meets the following prerequisites:

| Software | Required Version | Verification Command | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | 3.12+ | `python --version` | Powers the FastAPI backend and AI SDK routing. |
| **Node.js** | 18+ | `node --version` | Compiles and hosts the Vue 3 visual HUD. |
| **Google Cloud CLI** | Latest | `gcloud --version` | Handles secure enterprise ADC authentication. |

---

## 2. Secure Enterprise Authentication & Proxy Bypassing

V.I.S.I.O.N. operates strictly under enterprise compliance frameworks. **No raw API keys, passwords, or cloud credentials are permitted inside the codebase.**

### 2.1. GCP Identity Setup (Application Default Credentials - ADC)
V.I.S.I.O.N. uses role-based Cloud OAuth caches. To authenticate your local machine safely with the cloud:
1. Open your terminal.
2. Execute the following command:
   ```bash
   gcloud auth login --update-adc
   ```
3. A browser window will open. Authenticate using your Magellon corporate identity (or personal account).
4. This saves a temporary token in your system's local registry. The Vertex AI SDK reads this token automatically—eliminating password leaks.

### 2.2. Bypassing Magellon SSL Interception (Zscaler)
Corporate proxies perform deep packet SSL inspection, which routinely breaks Python cloud requests. To bypass this, we use the `pip-system-certs` library.
* **How it works**: This library forces the Python virtual environment to read from your **Windows Trusted Root Certificate Store** natively, bypassing proxy handshake blocks.
* **Requirement**: The virtual environment *must* be active before executing any pip or backend run commands to ensure the SSL hooks are loaded.

---

## 3. First-Time Project Setup

### 3.1. Environment Configuration
1. Navigate to the root directory `project-vision/`.
2. Copy the template variables to create your active environment file:
   * **Windows Powershell**:
     ```powershell
     copy .env.example .env
     ```
3. Open the newly created `.env` file and verify your target credentials:
   ```env
   GCP_PROJECT_ID="gbr-mts-wgh-hkt-dev"
   GCP_LOCATION="europe-west1"

   # Enforced Neural Model (Standard Magellon locked standard: gemini-2.5-flash)
   GEMINI_MODEL="gemini-2.5-flash"

   # Token Sliding Window Context Budget configuration
   MAX_CONTEXT_TURNS=10

   # RAG Vector DB Search & Evaluator Thresholds (Phase 4 SaaS Hardened)
   RAG_DISTANCE_THRESHOLD=0.85
   RAG_TOP_K=3
   RAG_USE_NEW_EVALUATOR=True
   RAG_HIGH_THRESHOLD=0.55
   RAG_MARGIN_THRESHOLD=0.15
   RAG_MIN_VIABLE_COUNT=2
   RAG_MIN_CONSENSUS_COUNT=2
   RAG_ALLOW_SINGLE_CHUNK_HIGH=True
   RAG_SINGLE_CHUNK_HIGH_THRESHOLD=0.40
   
   DATABASE_TARGET="LOCAL"  # Options: "LOCAL" (Chroma/SQLite) or "CLOUD" (PostgreSQL/pgvector)
   ```
   *(If corporate cloud approvals are waiting, replace these with your personal fallback sandbox credentials: `GCP_PROJECT_ID=project-vision-498006` and `GCP_LOCATION=us-central1`)*

4. **Verify System Directives File**:
   Ensure the core AI rule book file **`docs/SYSTEM_DIRECTIVES.md`** exists inside your local repository. This file defines the core behavioral persona, standard coding languages, and security guardrails that the AI brain will dynamically load on startup. You can edit this file on the fly from the HUD cockpit.

### 3.2. Backend Python Installation (FastAPI)
1. Open your terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create your isolated Python virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate the virtual environment (highly critical for Zscaler certificates!):
   * **Windows Powershell**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   * **Git Bash / Linux / macOS**:
     ```bash
     source .venv/bin/activate
     ```
4. Install all dependencies (including `pip-system-certs`, `tenacity`, `chromadb`, `pypdf`, `python-docx`, and `python-multipart`):
   ```bash
   pip install -r requirements.txt
   ```

### 3.3. Frontend Ingress Installation (Vue 3 HUD)
1. Open a separate terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install the lightweight Node modules:
   ```bash
   npm install
   ```

---

## 4. Day-to-Day Operation & Run Guide

To start the V.I.S.I.O.N. assistant, you must run both the backend server and the frontend client simultaneously.

### 4.1. Step 1: Start the Backend (FastAPI Web Server)
1. Open a terminal and navigate to `project-vision/backend/`.
2. Ensure your virtual environment is active (indicated by `(.venv)` in your terminal prompt).
3. Start the server using the designated python entry point:
   ```bash
   python run.py
   ```
4. **Verification**: The terminal will print:
   * `Dynamically injected custom prompt directives from docs/SYSTEM_DIRECTIVES.md`
   * `V.I.S.I.O.N. Neural Net active via gemini-2.5-flash`
   * `Uvicorn running on http://127.0.0.1:8000`

### 4.2. Step 2: Start the Frontend (Vite Dev Server)
1. Open a separate terminal and navigate to `project-vision/frontend/`.
2. Start the hot-reloading development server:
   ```bash
   npm run dev
   ```
3. **Verification**: Open your browser and navigate to the URL printed in the terminal:
   ```text
   http://localhost:5173
   ```

### 4.3. Step 3: Secure Cockpit Authentication (Triple-Tier Passcodes)
V.I.S.I.O.N. operates behind a strict, triple-tier authentication gate to protect the AI engine from unauthorized corporate observation, with role-based access control determined by the passcode entered. When presented with the Login gate, you must supply a Name and a designated Passcode.

* **Tier 1: ADMIN Mode**
  * **Passcode:** `vision@1133`
  * **Result:** Routes the user to `/home`. Unlocks the true V.I.S.I.O.N. Principal Engineering AI dashboard with full chat, voice, RAG capabilities, and a clickable, fully interactive Admin Telemetry Cockpit (clicking the green 'Connected' badge opens the Platform Status modal).
* **Tier 2: LEAD Mode**
  * **Passcode:** `vision@lead`
  * **Result:** Routes the user to `/home`. Unlocks the full chat, voice, and RAG capabilities, but the Admin Telemetry Cockpit remains securely locked (cannot open the telemetry modal).
* **Tier 3: GUEST Mode (The Decoy / Honeypot)**
  * **Passcode:** `vision2026`
  * **Result:** Routes the user to `/guest` (decoy screen). Renders a highly realistic, read-only Evoke.Kiosk.RailTVM Fleet Telemetry dashboard, perfectly camouflaging the real application from casual observers or colleagues.

---

## 5. Troubleshooting Matrix

### **Issue 1: "Diagnostic failure: 403 Permission Denied"**
* **Cause**: Your active GCP identity is authenticated but lacks explicit developer roles (`roles/aiplatform.user`) on the designated Google Cloud project.
* **Fix**: Ensure your role role is active. While waiting, toggle the project ID in your `.env` to your personal sandbox project (`project-vision-498006`).

### **Issue 2: "Diagnostic failure: SSL: CERTIFICATE_VERIFY_FAILED"**
* **Cause**: You are running inside the Magellon corporate network, and Zscaler is intercepting the connection without virtual environment cert hooks.
* **Fix**: Ensure you have activated your virtual environment (`.\.venv\Scripts\Activate.ps1`), which loads the system-level certificates hook. Never run python commands globally without activating the env.

### **Issue 3: "429 Resource Exhausted / Quota Limit Exceeded"**
* **Cause**: The Vertex AI Gemini instance has received too many concurrent tokens.
* **Fix**: Wait exactly 60 seconds for Google's sliding window rate-limit to reset.

### **Issue 4: Virtual Environment Activation Fails with ParserError (Unexpected Token)**
* **Cause**: On corporate Windows laptops, Microsoft OneDrive background synchronization frequently locks and mangles the `.venv` script comments (specifically `Activate.ps1`) during initialization, corrupting the code blocks.
* **Fix**: Force-purge the corrupted directory, regenerate a clean environment, and re-activate it by running the following sequential commands inside PowerShell:
  ```powershell
  # 1. Force-delete the corrupted venv folder
  Remove-Item -Recurse -Force .venv

  # 2. Regenerate a clean, uncorrupted virtual environment
  python -m venv .venv

  # 3. Re-activate the pristine scripts
  .\.venv\Scripts\Activate.ps1
  ```

---

## 6. Cloud SQL PostgreSQL & pgvector Migration Guide (Post-Approval Activation)

Once management approves the PostgreSQL Cloud SQL deployment, follow this exact step-by-step, highly detailed procedure to transition V.I.S.I.O.N. from the local single-user sandbox (SQLite/Chroma) to the centralized, shared corporate cloud database:

### Step 6.1: Provision the Google Cloud SQL Instance (GCP Console Guide)
1. **Navigate to Cloud SQL**: Log in to your Google Cloud Console (`console.cloud.google.com`), select project `gbr-mts-wgh-hkt-dev`, and search for **SQL** in the top search bar.
2. **Launch Database Wizard**: Click **Create Instance** and select **PostgreSQL**.
3. **Configure Settings**:
   * **Database Version**: Select **PostgreSQL 14** (or higher).
   * **Instance ID**: Enter `vision-prod-db`.
   * **Password**: Click **Generate** (or enter a strong, custom password). Copy this password immediately to your secure vault!
   * **Database Version / Edition**: Choose **Cloud SQL Enterprise Edition** (Development tier).
   * **Machine Config**: Choose a shared core machine (such as `db-f1-micro` or `db-g1-small` which costs ~$15 - ~$30/month) to keep cost highly optimized.
   * **Storage**: Select **SSD** (10 GB is more than enough for 5,000 pages of text documents), and check **Enable automatic storage increases** so the DB grows automatically as vectors grow.
4. **Configure Connections (Critical Security)**:
   * Expand **Connections**.
   * Uncheck **Public IP** to protect the database from the public internet!
   * Check **Private IP** and select your corporate **VPC network** from the dropdown list. This ensures the database is completely isolated inside your private VPC, accessible only by internal services.
   * **💡 VPC Firewall Configuration:** We have fully unblocked the PostgreSQL Cloud SQL database connectivity by enabling and configuring the required VPC firewall rules directly inside our Terraform templates, ensuring secure and seamless backend-to-database peering.
5. **Create**: Click **Create Instance** and wait 3-5 minutes for the green status checkmark to appear.

---

### Step 6.2: Enable the `pgvector` Extension (The Brain Bootstrapper)
PostgreSQL does not store high-dimensional vectors natively unless the `pgvector` extension is active.
1. **Open Database Query Tool**: Connect to your running Cloud SQL database using your standard corporate database manager (such as **DBeaver** or **pgAdmin**) via a VPN, or use the GCP Cloud Shell.
2. **Execute Bootstrapper**: In your SQL query editor, connect using `postgres` admin credentials and run this single SQL command:
   ```sql
   -- Bootstraps native vector types and cosine similarity algebra
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. **Verify Activation**: Run `SELECT * FROM pg_extension;` to confirm `vector` is listed.

---

### Step 6.3: Update your Production Environment Variables
To hot-swap V.I.S.I.O.N.'s database adapters instantly, update your cloud container's `.env` configuration mapping. You do **not** need to touch or modify any backend code:

1. Open your production environment settings or target `.env` file.
2. Configure the variables exactly as shown below:
   ```env
   # 1. Flip Target from LOCAL (SQLite/Chroma) to CLOUD (PostgreSQL/pgvector)
   DATABASE_TARGET="CLOUD"

   # 2. Add your Private Cloud SQL Database coordinates
   PG_HOST="[YOUR_CLOUD_SQL_PRIVATE_IP_HERE]"  # (e.g. 10.152.0.3)
   PG_PORT="5432"
   PG_DATABASE="vision_knowledge_base"
   PG_USER="postgres"
   PG_PASSWORD="[YOUR_SECURE_CLOUD_SQL_PASSWORD]"
   ```

---

### Step 6.4: Install PostgreSQL Client Drivers on the Host VM/Container
Before running the Python ASGI web application in cloud mode, make sure the PostgreSQL C-connector driver `psycopg2-binary` is installed inside your active Python environment.
1. Open your terminal in the backend directory.
2. Run this pip command to install the required lightweight driver:
   ```bash
   # Installs the pre-compiled, Zscaler-trusted PostgreSQL driver
   pip install psycopg2-binary
   ```

---

### Step 6.5: Bootstrap & Run Cloud Synchronization
When the backend boots up in Cloud Mode, our **Dual-Adapter DB service** will automatically detect the target change, connect to Cloud SQL, and bootstrap the tables dynamically.
1. **Boot Server**: Start the server locally or in the cloud:
   ```bash
   python run.py
   ```
   *The console will log:* `ADR-004 CLOUD: Connecting to Google Cloud SQL PostgreSQL... Successfully bootstrapped database schemas.`
2. **Execute Seeding Sync**: Run the synchronizer script to scrape your target Confluence spaces and ADO projects, vector-embed all pages, and save them directly into the Cloud SQL database:
   ```bash
   # Synchronizes and vectorizes all pages modified in the last 30 days
   python sync_connectors.py --sync-recent 43200
   ```

---

### Step 6.6: Deploy Backend & Frontend to Google Cloud Run (Serverless)

We leverage Google Cloud Run's serverless containers to host both our frontend and backend under a strictly decoupled, highly optimized microservices architecture. Both services are fully configured with the following production features:
*   **Scale-to-Zero (€0.00 Idle Hosting Costs):** The minimum instance count (`min_instance_count`) is explicitly set to `0` for both services, meaning container instances are destroyed when inactive—reducing idle hosting costs to exactly €0.00!
*   **Private VPC Egress (`PRIVATE_RANGES_ONLY`):** Under Cloud Run's VPC connections, egress traffic is configured for `Private IPs Only` (`PRIVATE_RANGES_ONLY`). This routes only private internal database queries to the VPC, while allowing public outbound API requests (such as Atlassian Confluence/ADO calls) to egress directly through the public internet, completely bypassing corporate proxy handshakes!
*   **Secure Secret Mapping:** Production credentials are never hardcoded or saved in environment files. On Cloud Run, Atlassian Personal Access Tokens are mapped securely as `CONFLUENCE_PAT` and `ADO_PAT` using direct Google Secret Manager (GSM) integration.
*   **Structured JSON Cloud Logging:** The python logger (`logging_config.py`) dynamically detects if it is running in the cloud. When deployed, it automatically outputs structured JSON logs optimized for GCP Log Explorer indexing, while continuing to output beautiful, human-readable text logs during local development.

#### 1. Compile & Deploy the Vue 3 Frontend (Nginx Container)
To host the Vue 3 dashboard securely, we compile it locally and wrap it inside a lightweight **Alpine Linux Nginx Web Server** container. This bypasses corporate Firebase blocks and GCS bucket privacy limits!

1. Open your local terminal in `/frontend/` and configure your build environment in `frontend/.env`:
   ```env
   VITE_BACKEND_URL=wss://vision-backend-494928274920.europe-west3.run.app/ws/audio
   VITE_REST_URL=https://vision-backend-494928274920.europe-west3.run.app
   ```
2. Compile and compile the container as version **`v1.1.0`**:
   ```powershell
   # Compile static Vue 3 assets locally
   npm run build-only

   # Build Nginx container (Bypasses Docker Layer Cache)
   docker build --no-cache -t europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-frontend:v1.1.0 -f ./Dockerfile .

   # Push to Artifact Registry
   docker push europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-frontend:v1.1.0
   ```
3. Open your GCP Cloud Run console ➔ Click **Create Service** ➔ Select the `vision-frontend:v1.1.0` image ➔ Set Region to **`europe-west3`** ➔ Enforce **Require authentication** ➔ Set Ingress to **Internal + Load Balancing** ➔ Under Scaling, set Min Instances to **0** and Max Instances to **5** ➔ Under Connections, link to your Serverless VPC Access connector ➔ Click **Create**!

#### 2. Compile & Deploy the Uvicorn FastAPI Backend Container
1. Open your local terminal in `/backend/` and compile the backend container as version **`v1.2.0`**:
   ```powershell
   # Build Uvicorn container
   docker build --no-cache -t europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-backend:v1.2.0 -f ./Dockerfile .

   # Push to Artifact Registry
   docker push europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-backend:v1.2.0
   ```
2. In your GCP Cloud Run console ➔ Click **Create Service** (or edit revision) ➔ Select the `v1.2.0` image ➔ Under Scaling, set Min Instances to **0** ➔ Under Variables, reference Secret Manager secrets to map `CONFLUENCE_PAT` and `ADO_PAT` ➔ Under Connections, select your VPC connector and set Egress to **Route only private IPs to the VPC** (`PRIVATE_RANGES_ONLY`) ➔ Deploy!

#### 3. Secure Production Secret Mapping (Google Secret Manager)
To maintain 100% cloud security compliance, all database passwords and Personal Access Tokens (PATs) are hosted strictly inside **Google Secret Manager (GSM)** and mapped dynamically as container environment variables on Cloud Run startup. 

Use this exact mapping matrix to configure your GCP Secret Manager console:

| GCP Secret Manager Secret ID | Cloud Run Environment Variable | Purpose & Vault Configuration |
| :--- | :--- | :--- |
| **`confluence-api-token`** | `CONFLUENCE_PAT` | Atlassian Confluence Personal Access Token (PAT). Created manually in Atlassian and pasted into GSM. |
| **`ado-pat-token`** | `ADO_PAT` | Azure DevOps Personal Access Token (PAT). Created manually in ADO and pasted into GSM. |
| **`vision-db-password`** | `PG_PASSWORD` | PostgreSQL Database Administrator Password. Automatically synchronized with Terraform's generated database password! |

*Note: For maximum security, the backend container does **not** write or persist these secrets on local disk. They are stored purely in-memory inside the active Cloud Run container workspace!*

---

### Step 6.7: Accessing the App (Double-Proxy Tunnels)
Since both services are locked down inside your VPC under 'Require Authentication' and 'Internal' Ingress, use the double-proxy tunnel command in separate terminal windows to access the app:

```powershell
# Terminal 1: Proxy to Frontend (Port 9090)
gcloud beta run services proxy vision-frontend --project=gbr-mts-wgh-hkt-dev --region=europe-west3 --port=9090

# Terminal 2: Proxy to Backend (Port 8000)
gcloud beta run services proxy vision-backend --project=gbr-mts-wgh-hkt-dev --region=europe-west3 --port=8000
```
Then, open your browser and load **`http://127.0.0.1:9090`**!

---
*(End of Runbook)*
