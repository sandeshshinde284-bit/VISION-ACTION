# V.I.S.I.O.N. Deployment & Commands Guide
**Date:** Oct 21, 2026 | **Version:** 1.0 | **Status:** Verified

Complete setup, quick-start, command reference, and troubleshooting guide.

---

## 1. PREREQUISITES

### System Requirements
- **OS:** Linux, macOS, or WSL2 (Windows)
- **Python:** 3.12+ (backend)
- **Node.js:** 18+ LTS (frontend)
- **Database:** SQLite (dev) or PostgreSQL (prod)
- **RAM:** 2GB minimum, 4GB+ recommended
- **Disk:** 1GB free (code + dependencies)

### Required Tools
```bash
# Install Python 3.12+
python3 --version  # Should output 3.12.x or higher

# Install Node.js 18+ LTS
node --version     # Should output v18.x or higher
npm --version      # Should output 8.x or higher

# Optional: PostgreSQL (for production)
psql --version     # If using Postgres instead of SQLite
```

---

## 2. LOCAL DEVELOPMENT SETUP

### 2.1 Clone the Repository
```bash
git clone <repository-url>
cd vision-action
```

### 2.2 Backend Setup

#### Create Virtual Environment
```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Key Packages:**
- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `sqlalchemy` — ORM
- `chromadb` — Vector database
- `google-cloud-aiplatform` — Vertex AI
- `pypdf` — PDF extraction
- `python-docx` — DOCX extraction
- `psutil` — System metrics
- `websockets` — WebSocket support

#### Configure Environment Variables
```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your credentials
nano .env  # or vim, code, etc.
```

**Required Variables:**
```env
# Google Vertex AI
GOOGLE_PROJECT_ID=your-gcp-project-id
GOOGLE_REGION=us-central1
VERTEX_AI_MODEL=gemini-2.5-flash

# Database (SQLite for dev)
DATABASE_URL=sqlite:///vision.db

# Frontend URL (CORS)
FRONTEND_URL=http://localhost:5173

# Server config
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
```

#### Initialize Database
```bash
cd backend
python -m backend.app.main --init-db
```

This creates:
- `vision.db` (SQLite file)
- Tables: `users`, `sessions`, `messages`, `documents`, `system_settings`
- Default admin user (configurable in script)

### 2.3 Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

**Key Packages:**
- `vue@3` — UI framework
- `typescript` — Type safety
- `tailwindcss` — Styling
- `vite` — Build tool

#### Configure Environment Variables
```bash
# Copy example to .env.local
cp .env.example .env.local

# Edit as needed (usually localhost defaults are fine)
nano .env.local
```

**Variables:**
```env
VITE_API_URL=http://127.0.0.1:8000
VITE_WS_URL=ws://127.0.0.1:8000
```

---

## 3. RUNNING LOCALLY

### 3.1 Start Backend
```bash
cd backend
source .venv/bin/activate
python -m backend.app.main
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Endpoints:**
- `http://localhost:8000/docs` — API documentation (auto-generated)
- `ws://localhost:8000/ws` — WebSocket endpoint
- `http://localhost:8000/api/login` — Authentication

### 3.2 Start Frontend (in another terminal)
```bash
cd frontend
npm run dev
```

**Expected Output:**
```
  VITE v5.x.x  ready in 200 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

### 3.3 Open in Browser
```
http://localhost:5173
```

**Login Credentials (default):**
- **Username:** admin
- **Password:** admin123

> **Note:** Change these immediately in production.

---

## 4. COMMAND REFERENCE

### Backend Commands

#### Run with Debug Mode
```bash
cd backend
source .venv/bin/activate
python -m backend.app.main --debug
```

#### Run with Custom Port
```bash
python -m backend.app.main --port 8001
```

#### Database Migrations
```bash
# Upgrade to latest schema
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Create new migration (auto-detect changes)
alembic revision --autogenerate -m "Add new column"
```

#### Seed Test Data
```bash
python scripts/seed_db.py
```

#### Clear Database
```bash
python scripts/clear_db.py
```

#### Run Tests
```bash
pytest tests/ -v
pytest tests/test_ai_service.py::test_intent_classification -v
```

#### Lint & Format Code
```bash
# Check style
flake8 backend/

# Auto-format
black backend/
isort backend/
```

---

### Frontend Commands

#### Development Server with HMR
```bash
cd frontend
npm run dev
```

#### Build for Production
```bash
npm run build
```

Output: `frontend/dist/` (ready for CDN/static hosting)

#### Preview Production Build
```bash
npm run preview
```

#### Lint Vue Components
```bash
npm run lint
```

#### Type Check (TypeScript)
```bash
npm run type-check
```

#### Format Code
```bash
npm run format
```

---

## 5. DOCKER SETUP (Optional)

### 5.1 Build Docker Image
```bash
docker build -t vision-ai:latest .
```

### 5.2 Run Container
```bash
docker run -d \
  --name vision-ai \
  -p 8000:8000 \
  -p 5173:5173 \
  -e GOOGLE_PROJECT_ID=your-project \
  -e DATABASE_URL=sqlite:///vision.db \
  vision-ai:latest
```

### 5.3 Check Logs
```bash
docker logs -f vision-ai
```

### 5.4 Stop Container
```bash
docker stop vision-ai
docker rm vision-ai
```

---

## 6. PRODUCTION DEPLOYMENT

### 6.1 Environment Setup
```bash
# Use production .env
cp .env.production .env
```

**Production Variables:**
```env
# Use PostgreSQL, not SQLite
DATABASE_URL=postgresql://user:password@db.example.com/vision

# Google Vertex AI (same as dev)
GOOGLE_PROJECT_ID=production-gcp-project
VERTEX_AI_MODEL=gemini-2.5-flash

# HTTPS enforced
FRONTEND_URL=https://vision.worldline.com
SERVER_HTTPS=true
SSL_CERTFILE=/etc/ssl/certs/server.crt
SSL_KEYFILE=/etc/ssl/private/server.key

# Security
SECURE_COOKIES=true
CORS_ORIGINS=https://vision.worldline.com
```

### 6.2 Deploy Backend
```bash
# Using systemd (Linux)
sudo cp deployment/vision-backend.service /etc/systemd/system/
sudo systemctl enable vision-backend
sudo systemctl start vision-backend

# Or using Docker (recommended)
docker push vision-ai:latest
kubectl apply -f deployment/k8s-backend.yaml
```

### 6.3 Deploy Frontend
```bash
# Build static assets
npm run build

# Upload to CDN/S3
aws s3 sync dist/ s3://vision-cdn/
```

### 6.4 Database Migration (Production)
```bash
# Backup existing database
pg_dump -U postgres vision_db > backup-2026-10-21.sql

# Run migrations
python -m alembic upgrade head

# Verify
psql -U postgres vision_db -c "SELECT version();"
```

### 6.5 Health Checks
```bash
# Backend health
curl https://api.vision.worldline.com/health

# Frontend status
curl https://vision.worldline.com/

# Database connection
curl https://api.vision.worldline.com/api/db-status
```

---

## 7. TROUBLESHOOTING

### Issue: Backend fails to start (port in use)
```bash
# Find process using port 8000
lsof -i :8000

# Kill process (if safe)
kill -9 <PID>

# Or use different port
python -m backend.app.main --port 8001
```

### Issue: WebSocket connection fails
```bash
# Check CORS configuration in backend/app/main.py
# Verify frontend URL matches FRONTEND_URL env variable

# Test WebSocket manually
wscat -c ws://localhost:8000/ws?token=your-token
```

### Issue: Database locked (SQLite)
```bash
# SQLite doesn't handle concurrent writes well
# Solution: Use PostgreSQL in production

# Temporary: Delete lock file
rm backend/vision.db-wal
rm backend/vision.db-shm
```

### Issue: Gemini API 403 Forbidden
```bash
# Check Google Cloud credentials
gcloud auth application-default login

# Verify Vertex AI API is enabled in GCP console
# Verify project has quota for text-bison, embedding-gecko

# Check GOOGLE_PROJECT_ID matches .env
echo $GOOGLE_PROJECT_ID
```

### Issue: Frontend shows blank screen
```bash
# Check browser console for errors
# Open DevTools: F12 → Console

# Verify frontend .env.local has correct API URL
cat frontend/.env.local

# Clear browser cache
# Ctrl+Shift+R (hard refresh)
```

### Issue: Slow RAG search
```bash
# ChromaDB threshold may be too loose
# Edit backend/app/services/rag_service.py:
SIMILARITY_THRESHOLD = 0.85  # Try 0.70 for stricter matching

# Restart backend
python -m backend.app.main
```

### Issue: Dependencies won't install
```bash
# Update pip/npm
pip install --upgrade pip setuptools wheel
npm install -g npm@latest

# Clear cache
pip cache purge
npm cache clean --force

# Reinstall
pip install -r requirements.txt
npm install
```

---

## 8. MONITORING & LOGS

### View Logs (Development)
```bash
# Backend logs (stdout)
tail -f backend.log

# Frontend logs (browser console)
# F12 → Console tab

# System telemetry
curl http://localhost:8000/api/telemetry
```

### Production Logging
```bash
# systemd
journalctl -u vision-backend -f

# Docker
docker logs -f vision-ai

# Application logs file
tail -f /var/log/vision-backend.log
```

---

## 9. MAINTENANCE

### Update Dependencies
```bash
# Backend
cd backend
pip list --outdated
pip install --upgrade <package-name>

# Frontend
cd frontend
npm outdated
npm update
```

### Backup Database
```bash
# SQLite
cp backend/vision.db backend/vision.db.backup-$(date +%Y%m%d)

# PostgreSQL
pg_dump -U postgres vision_db > backups/vision-$(date +%Y%m%d-%H%M%S).sql
```

### Clean Up
```bash
# Remove old logs
find . -name "*.log" -mtime +30 -delete

# Clear npm cache
npm cache clean --force

# Remove unused Python packages
pip list --outdated | grep -v "^-" | awk '{print $1}' | xargs pip uninstall -y
```

---

## 10. QUICK START SUMMARY

**Local development in 5 steps:**

```bash
# 1. Clone
git clone <repo>
cd vision-action

# 2. Backend
cd backend && python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your Google Cloud credentials
python -m backend.app.main

# 3. Frontend (new terminal)
cd frontend && npm install
cp .env.example .env.local
npm run dev

# 4. Visit
# http://localhost:5173

# 5. Login
# Username: admin
# Password: admin123
```

Done! 🚀

---

## ADDITIONAL RESOURCES

- **API Docs:** http://localhost:8000/docs (auto-generated Swagger)
- **System Directives:** `SYSTEM_DIRECTIVES.md`
- **Process Flows:** `01-ProcessFlow.md`
- **Architecture:** `02-TechnicalArchitecture.md`
- **Issues & Roadmap:** `18-IssuesAndRoadmap.md`

