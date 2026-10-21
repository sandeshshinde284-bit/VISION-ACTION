# V.I.S.I.O.N. Commands & Operations Cheat Sheet

This document contains **every single operational command** required to build, test, deploy, and proxy the V.I.S.I.O.N. Full-Stack platform. 

---

## 1. Local Sandbox Development (Strictly Local)
Run these commands to test the UI and AI brain locally on your laptop using local SQLite and ChromaDB files.

**Prerequisite:** No `frontend/.env` configurations are required anymore! The Vue frontend dynamically resolves the correct target endpoint at runtime (`localhost:8000` locally, or secure custom `https://` / `wss://` in the cloud) using the browser's active hostname.

```powershell
# Step 1: Start your local Python FastAPI Backend
cd backend
.\.venv\Scripts\python.exe run.py

# Step 2: Start your Vue 3 Frontend locally (in a new terminal)
cd frontend
npm run dev

# Step 3: Open your browser
# Navigate to http://localhost:5173 (or the port Vite provides)
```

### Triggering the Serverless Background Sync locally (Phase 4)
To test and verify the Confluence and ADO synchronization locally through your corporate Zscaler SSL proxy:
```powershell
# Trigger a delta sync for the last 30 minutes (FastAPI Background Task)
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/sync?minutes=30"

# Trigger a wide-range historical sync for the last 15 days (21,600 minutes)
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/sync?minutes=21600"
```

---

## 2. Docker Compilation & Building (Decoupled Microservices)
How to compile the production-ready frontend and backend containers cleanly. Always use the `--no-cache` flag to bypass image caching bugs and ensure the latest code is packaged!

### Build the Frontend (v1.2.2)
```powershell
cd C:\SANDESH_AI\AI\vision\project-vision\frontend

# 1. Compile the Vue assets natively (100% environment-agnostic!)
npm run build-only

# 2. Build the Nginx web container
docker build --no-cache -t europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-frontend:v1.2.2 -f ./Dockerfile .
```

### Build the Backend (v1.3.2)
```powershell
cd C:\SANDESH_AI\AI\vision\project-vision\backend

# Build the FastAPI container
docker build --no-cache -t europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-backend:v1.3.2 -f ./Dockerfile .
```

---

## 3. Pushing to Google Artifact Registry (GAR)
Push your compiled images to the secure Magellon cloud registry.

```powershell
# Push Frontend v1.2.2
docker push europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-frontend:v1.2.2

# Push Backend v1.3.2
docker push europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-backend:v1.3.2
```

---

## 4. Deploying to Cloud Run (Browser UI Method)
Once pushed, you must tell Cloud Run to deploy the new tags.

1. Go to **Google Cloud Console -> Cloud Run**.
2. Click on **`vision-frontend`** or **`vision-backend`**.
3. Click **Edit & Deploy New Revision**.
4. In the Container Image URL box, change the tag to the new version (e.g., `:v1.1.0` or `:v1.2.0`).
5. Click **Deploy**.

---

## 5. Live Cloud Proxy Tunnels (The "Zero-Local" Method)
Run these commands to access the 100% cloud-hosted platform without running any code locally! This bypasses the Direct IAP security shield safely.

```powershell
# Terminal 1: Proxy to the Nginx Frontend
gcloud beta run services proxy vision-frontend --project=gbr-mts-wgh-hkt-dev --region=europe-west3 --port=9090

# Terminal 2: Proxy to the FastAPI Backend
gcloud beta run services proxy vision-backend --project=gbr-mts-wgh-hkt-dev --region=europe-west3 --port=8000

# Open your browser and navigate to:
# http://127.0.0.1:9090
```

---

## 6. Local Docker Verification (Debugging)
If the cloud deployment fails or shows a 404, test the container locally to verify files were packed correctly.

```powershell
# Test Frontend Container Locally (Injects the required Cloud Run $PORT)
docker run --rm -p 8080:8080 -e PORT=8080 europe-west1-docker.pkg.dev/gbr-mts-wgh-hkt-dev/vision-repo/vision-frontend:v1.1.0

# Open http://localhost:8080 in your browser to verify it loads!
```