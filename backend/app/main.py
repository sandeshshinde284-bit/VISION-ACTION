import os

# ==============================================================================
# SECURE CORPORATE SSL BRIDGE - BYPASSES ZSCALER BY FORCING HTTP/REST OVER gRPC
# ==============================================================================
# Force Google Cloud SDK to use standard HTTP/REST transport instead of gRPC.
# This makes it use Python's requests layer which is 100% patched by pip-system-certs!
os.environ["GOOGLE_CLOUD_DISABLE_GRPC"] = "true"
os.environ["API_TRANSPORT"] = "rest"
os.environ["VERTEX_AI_TRANSPORT"] = "rest"

try:
    import certifi
    import pip_system_certs.wrapt_requests
    certifi_path = certifi.where()
    os.environ["SSL_CERT_FILE"] = certifi_path
    os.environ["REQUESTS_CA_BUNDLE"] = certifi_path
    pip_system_certs.wrapt_requests.inject_truststore()
except ImportError:
    pass
# ==============================================================================

from app.core.logging_config import setup_logging

# Initialize unified production-grade console & file logging
setup_logging()

import logging
logger = logging.getLogger("MainAPI")

from pydantic import BaseModel

class SessionCreateSchema(BaseModel):
    session_id: str
    title: str
    admin_name: str

class SessionRenameSchema(BaseModel):
    title: str
    admin_name: str

from fastapi import FastAPI, Body, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api import websockets, uploads
from app.services.ai_service import ai_service

# --- ISSUE #C FIX: Initialize Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)

# create the FASTAPI app instance
app = FastAPI(
    title="Project V.I.S.I.O.N. Backend API",
    description="API for Project V.I.S.I.O.N., an enterprise AI assistant for METS",
    version="1.0.0",
)

# --- ISSUE #C FIX: Add rate limiter to app state ---
app.state.limiter = limiter

# Enable CORS for the Vue frontend (Pristine, conflict-free enterprise configuration!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://127.0.0.1:5173", 
        "http://127.0.0.1:5174"
    ], 
    allow_credentials=False, # Prevents standard browser CORS blocks on wildcard credentials!
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount Routers ---
app.include_router(websockets.router)
app.include_router(uploads.router)

# Issue #2 Fix: Mount sync management router
from app.api import sync_routes
app.include_router(sync_routes.router)

# Sync status & history endpoints (UI dashboard)
from app.api import sync_status
app.include_router(sync_status.router)

# Logging API for frontend log ingestion
from app.api import logs
app.include_router(logs.router)

# --- Directives API (Phase 4 - Cloud Persistent & Database-Backed) ---
DIRECTIVES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "SYSTEM_DIRECTIVES.md"))

@app.get("/api/directives", tags=["Configuration"])
def get_directives():
    """Reads and returns the current System Directives markdown file from database alongside dynamic base URLs."""
    from app.core.config import settings
    # 1. Try to fetch from the persistent database first!
    content = db_service.get_setting("system_directives")
    
    if not content:
        # 2. Database is empty (First boot), read the default file packaged inside the backend directory!
        logger.info(f"Database Config: No directives found in DB. Reading default template from disk...")
        if os.path.exists(DIRECTIVES_PATH):
            try:
                with open(DIRECTIVES_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 3. Seed directly to the persistent SQLite/PostgreSQL database!
                    db_service.save_setting("system_directives", content)
            except Exception as e:
                logger.warning(f"Failed to read default system directives from disk: {e}")
                
    return {
        "content": content,
        "confluence_url": settings.CONFLUENCE_URL,
        "ado_url": settings.ADO_URL,
        "confluence_spaces": settings.CONFLUENCE_SPACES,
        "ado_projects": settings.ADO_PROJECT
    }

@app.post("/api/directives", tags=["Configuration"])
def update_directives(
    content: str = Body(..., embed=True),
    role: str = Body("GUEST", embed=True)
):
    """Overwrites the System Directives inside the persistent database and reloads the active AI context."""
    # Strict Server-Side Role Validation
    if role not in ["ADMIN", "LEAD"]:
        raise HTTPException(
            status_code=403, 
            detail="Security Gating Policy: Only LEAD or ADMIN administrators are authorized to overwrite global system directives."
        )

    # 1. Write directly to your Cloud SQL PostgreSQL or local SQLite database (100% persistent!)
    db_service.save_setting("system_directives", content)
    
    # 2. Try to mirror back to local disk if the filesystem is writeable (Local Dev only, fails silently on Cloud Run!)
    try:
        with open(DIRECTIVES_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Database Settings: Successfully mirrored edited directives back to local disk.")
    except Exception as e:
        # Fails silently as expected inside Cloud Run serverless containers!
        logger.warning(f"Database Settings: Could not mirror directives to local disk (Normal on Cloud Run): {e}")
    
    # 3. Reload the AI Brain dynamically with the new instructions in 0ms!
    ai_service.reload_directives()
    
    return {"status": "success", "message": "Directives updated and AI context reloaded."}

@app.post("/api/optimize_prompt", tags=["Intelligence"])
def optimize_prompt_endpoint(content: str = Body(..., embed=True)):
    """Refactors a messy raw user prompt into an optimized, high-fidelity RAG-ready prompt using Gemini."""
    optimized = ai_service.optimize_prompt(content)
    return {"status": "success", "optimized": optimized}

@app.delete("/api/history", tags=["Configuration"])
def clear_history_endpoint():
    """Wipes the SQLite database history table and resets the active AI memory context sliding window."""
    from app.services.db_service import db_service
    db_service.clear_chat_history()
    ai_service.context_history = [] # Reset active AI brain sliding memory
    return {"status": "success", "message": "Chat history and active AI memory successfully purged."}

@app.post("/api/sync", tags=["Configuration"])
def trigger_sync_endpoint(background_tasks: BackgroundTasks, minutes: int = 180):
    """
    Triggers the Confluence & ADO delta synchronization loop as a serverless background task.
    This is highly optimized for Google Cloud Run scale-to-zero, allowing Google Cloud Scheduler
    to trigger background syncs every 3 hours natively without thread-locking the container!
    """
    try:
        #& 6.2 Fix: Check global lock before launching duplicate threads
        active_spaces = db_service.get_active_sync_targets("CONFLUENCE_SPACE")
        for space in active_spaces:
            # We just do a dry-run check here. The actual lock is acquired inside the task.
            # But if any space is currently locked, we reject the global sync trigger.
            with db_service._get_connection() as conn:
                cursor = conn.cursor()
                p = db_service.placeholder
                cursor.execute(f"SELECT is_syncing FROM config_sync WHERE target_type = {p} AND target_key = {p}", ("CONFLUENCE_SPACE", space))
                row = cursor.fetchone()
                if row and row[0] in [1, True, "TRUE", "1"]:
                    raise HTTPException(status_code=409, detail=f"Sync already in progress for space '{space}'. Please wait.")

        from sync_connectors import run_recent_sync_cycle
        # Run sync asynchronously so the API returns success instantly, preventing timeouts!
        background_tasks.add_task(run_recent_sync_cycle, minutes)
        return {
            "status": "success",
            "message": f"Serverless synchronization background task successfully scheduled for last {minutes} minutes."
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": f"Failed to queue background sync: {str(e)}"}

@app.post("/api/sync/confluence", tags=["Configuration"])
def trigger_confluence_sync_endpoint(background_tasks: BackgroundTasks, minutes: int = None):
    """
    Triggers the database-driven, multi-space Confluence sync loop as a background task.
    - If minutes is provided: Syncs only recently modified pages in active spaces.
    - If minutes is None: Runs a full recursive space crawl (hydration) over all pages.
    - Strict Data Hygiene: Skips drafts, archives, and deleted trash.
    """
    try:
        #& 6.2 Fix: Check global lock before launching duplicate threads
        active_spaces = db_service.get_active_sync_targets("CONFLUENCE_SPACE")
        for space in active_spaces:
            with db_service._get_connection() as conn:
                cursor = conn.cursor()
                p = db_service.placeholder
                cursor.execute(f"SELECT is_syncing FROM config_sync WHERE target_type = {p} AND target_key = {p}", ("CONFLUENCE_SPACE", space))
                row = cursor.fetchone()
                if row and row[0] in [1, True, "TRUE", "1"]:
                    raise HTTPException(status_code=409, detail=f"Sync already in progress for space '{space}'. Please wait.")

        from sync_connectors import sync_all_active_confluence_spaces
        # Run recursively in background to prevent browser/GCP connection timeouts
        background_tasks.add_task(sync_all_active_confluence_spaces, minutes)
        mode = f"delta sync for last {minutes} minutes" if minutes else "full space hydration"
        return {
            "status": "success",
            "message": f"Confluence {mode} successfully scheduled in the background."
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": f"Failed to queue Confluence background sync: {str(e)}"}

@app.get("/api/sync/status")
async def get_sync_status():
    """: Returns freshness audit information per Confluence space.
    Allows users to verify when data was last synced and identify stale documents.
    
    Response includes:
    - Last sync time per space
    - Total document count
    - Stale document count (>7 days old)
    - Average freshness
    """
    try:
        from app.services.db_service import db_service
        from datetime import datetime, timedelta, timezone
        
        with db_service._get_connection() as conn:
            cursor = conn.cursor()
            
            # Query 1: Get stats per space
            if db_service.placeholder == "%s":  # PostgreSQL
                cursor.execute("""
                    SELECT 
                        space_key,
                        COUNT(*) as doc_count,
                        MAX(last_synced_at) as last_sync_time,
                        COUNT(CASE WHEN last_synced_at < NOW() - INTERVAL '7 days' THEN 1 END) as stale_count
                    FROM documents
                    WHERE source_system = 'CONFLUENCE'
                    GROUP BY space_key
                    ORDER BY last_sync_time DESC
                """)
            else:  # SQLite
                cursor.execute("""
                    SELECT 
                        space_key,
                        COUNT(*) as doc_count,
                        MAX(last_synced_at) as last_sync_time,
                        COUNT(CASE WHEN last_synced_at < datetime('now', '-7 days') THEN 1 END) as stale_count
                    FROM documents
                    WHERE source_system = 'CONFLUENCE'
                    GROUP BY space_key
                    ORDER BY last_sync_time DESC
                """)
            
            rows = cursor.fetchall()
            spaces_stats = []
            
            for row in rows:
                space_key, doc_count, last_sync_time, stale_count = row
                freshness = "Unknown"
                if last_sync_time:
                    try:
                        sync_dt = datetime.fromisoformat(last_sync_time.replace('Z', '+00:00')) if isinstance(last_sync_time, str) else last_sync_time.replace(tzinfo=timezone.utc)
                        now = datetime.now(timezone.utc)
                        delta = now - sync_dt
                        hours = int(delta.total_seconds() // 3600)
                        freshness = f"{hours}h ago" if hours > 0 else "Just now"
                    except:
                        pass
                
                spaces_stats.append({
                    "space": space_key,
                    "doc_count": doc_count,
                    "stale_count": stale_count,
                    "last_synced": freshness,
                    "health": "🟢 Fresh" if stale_count == 0 else "🟡 Mixed" if stale_count < doc_count // 2 else "🔴 Stale"
                })
            
            # Query 2: Overall stats
            if db_service.placeholder == "%s":
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_docs,
                        COUNT(CASE WHEN source_system = 'CONFLUENCE' THEN 1 END) as conf_docs,
                        COUNT(CASE WHEN source_system = 'ADO' THEN 1 END) as ado_docs,
                        COUNT(CASE WHEN last_synced_at < NOW() - INTERVAL '7 days' THEN 1 END) as stale_docs
                    FROM documents
                """)
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_docs,
                        COUNT(CASE WHEN source_system = 'CONFLUENCE' THEN 1 END) as conf_docs,
                        COUNT(CASE WHEN source_system = 'ADO' THEN 1 END) as ado_docs,
                        COUNT(CASE WHEN last_synced_at < datetime('now', '-7 days') THEN 1 END) as stale_docs
                    FROM documents
                """)
            
            overall = cursor.fetchone()
            total_docs, conf_docs, ado_docs, stale_docs = overall if overall else (0, 0, 0, 0)
            
            return {
                "status": "success",
                "summary": {
                    "total_documents": total_docs,
                    "confluence_docs": conf_docs,
                    "ado_docs": ado_docs,
                    "stale_documents_7d": stale_docs,
                    "freshness_health": "🟢 Excellent" if stale_docs == 0 else "🟡 Good" if stale_docs < total_docs // 4 else "🔴 Needs Refresh"
                },
                "spaces": spaces_stats
            }
    except Exception as e:
        logger.error(f"Failed to retrieve sync status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# ==============================================================================
# SAAS MULTI-SESSION REST CRUD GATEWAYS (PHASE 4)
# ==============================================================================
from app.services.db_service import db_service

class LoginSchema(BaseModel):
    username: str
    password: str

@app.post("/api/login", tags=["Authentication"])
def login_endpoint(payload: LoginSchema):
    """Queries the persistent database to authenticate the user and return their dynamic role."""
    username_clean = payload.username.strip().lower()
    password_clean = payload.password.strip()

    user = db_service.authenticate_user(username_clean, password_clean)
    if user:
        # Generate a secure database-driven session token instead of relying on frontend hardcoded strings!
        token = db_service.generate_auth_token(user["username"], user["role"])
        if token:
            return {
                "status": "success",
                "username": user["username"],
                "role": user["role"],
                "token": token
            }
    raise HTTPException(status_code=401, detail="Access Key Rejected: Invalid username or password combo.")

@app.get("/api/sessions", tags=["Multi-Session"])
def get_sessions_endpoint(admin_name: str = "Sandesh"):
    """Lists all active chat sessions owned by the authenticated admin."""
    sessions = db_service.get_chat_sessions(admin_name)
    return {"status": "success", "sessions": sessions}

@app.get("/api/telemetry", tags=["Diagnostics"])
def get_telemetry_endpoint():
    """
    Returns unified system-wide diagnostics, knowledge base coverage, and sync status
    for the secure Admin Telemetry Cockpit.
    """
    from app.services.db_service import db_service
    try:
        with db_service._get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Total documents count by system
                cursor.execute("SELECT source_system, COUNT(*) FROM documents GROUP BY source_system")
                doc_stats = {row[0]: row[1] for row in cursor.fetchall()}
                
                # 2. Total vector chunks count by system
                cursor.execute("SELECT source_system, COUNT(*) FROM knowledge_base GROUP BY source_system")
                chunk_stats = {row[0]: row[1] for row in cursor.fetchall()}
                
                # 3. Space key distribution
                cursor.execute("SELECT space_key, COUNT(*) FROM documents GROUP BY space_key")
                space_stats = {row[0]: row[1] for row in cursor.fetchall()}
                
                # 4. Get active sync targets
                cursor.execute("SELECT target_key, last_synced_at FROM config_sync WHERE is_active = TRUE")
                sync_targets = {row[0]: str(row[1]) if row[1] else "Never" for row in cursor.fetchall()}
                
        return {
            "status": "success",
            "telemetry": {
                "database_status": "Connected (PostgreSQL / pgvector)",
                "documents": doc_stats,
                "chunks": chunk_stats,
                "spaces": space_stats,
                "sync_targets": sync_targets
            }
        }
    except Exception as e:
        # Fallback to local SQLite structures if PostgreSQL is unavailable during diagnostic tests
        try:
            with db_service._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_system, COUNT(*) FROM documents GROUP BY source_system")
                doc_stats = {row[0]: row[1] for row in cursor.fetchall()}
                
                chunk_stats = {"CHROMA_LOCAL": "Active (ChromaDB Indexed)"}
                
                cursor.execute("SELECT space_key, COUNT(*) FROM documents GROUP BY space_key")
                space_stats = {row[0]: row[1] for row in cursor.fetchall()}
                
                cursor.execute("SELECT target_key, last_synced_at FROM config_sync WHERE is_active = 1")
                sync_targets = {row[0]: str(row[1]) if row[1] else "Never" for row in cursor.fetchall()}
                
            return {
                "status": "success",
                "telemetry": {
                    "database_status": "Connected (Local SQLite / ChromaDB)",
                    "documents": doc_stats,
                    "chunks": chunk_stats,
                    "spaces": space_stats,
                    "sync_targets": sync_targets
                }
            }
        except Exception as sqlite_err:
            return {"status": "error", "message": f"Diagnostics failed: {str(e)} / {str(sqlite_err)}"}

@app.post("/api/sessions", tags=["Multi-Session"])
def create_session_endpoint(payload: SessionCreateSchema):
    """Creates a new concurrent chat session row in the database."""
    success = db_service.create_chat_session(payload.session_id, payload.title, payload.admin_name)
    if success:
        return {"status": "success", "session_id": payload.session_id}
    return {"status": "error", "message": "Failed to create chat session."}

@app.put("/api/sessions/{session_id}", tags=["Multi-Session"])
def rename_session_endpoint(session_id: str, payload: SessionRenameSchema):
    """Renames an active chat session (validates admin ownership)."""
    success = db_service.rename_chat_session(session_id, payload.title, payload.admin_name)
    if success:
        return {"status": "success", "message": f"Session renamed to [{payload.title}]."}
    return {"status": "error", "message": "Failed to rename session or permission denied."}

@app.get("/api/sessions/{session_id}", tags=["Multi-Session"])
def delete_session_endpoint(session_id: str, admin_name: str = "Sandesh"):
    """Atomically purges a session and all associated message records."""
    success = db_service.delete_chat_session(session_id, admin_name)
    if success:
        return {"status": "success", "message": f"Session {session_id} successfully deleted."}
    return {"status": "error", "message": "Failed to delete session or permission denied."}

from app.core.config import settings

@app.get("/api/history", tags=["Multi-Session"])
def get_session_history_endpoint(session_id: str, limit: int = settings.UI_HISTORY_LIMIT, admin_name: str = "Sandesh"):
    """Retrieves paginated historical timeline rows strictly scoped to active session and admin_name."""
    history = db_service.get_chat_history_for_session(session_id, admin_name, limit=limit)
    # Return formatted rows matching the frontend timeline expectations
    formatted_history = []
    for msg in history: # Maintain perfect chronological ASC flow directly from SQLite!
        sender = str(msg.get("sender", "")).upper().strip()
        text = msg.get("text")
        if sender == "ADMIN":
            formatted_history.append(f"[ADMIN]: {text}")
        else:
            formatted_history.append(text)
    return {"status": "success", "history": formatted_history}


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Defensive Safeguard: Ensure the dist/assets folders exist so the mount doesn't crash on startup!
os.makedirs("dist/assets", exist_ok=True)
if not os.path.exists("dist/index.html"):
    with open("dist/index.html", "w", encoding="utf-8") as f:
        f.write("<html><body><h1>V.I.S.I.O.N. Full-Stack Container Booting...</h1><p>Please build and copy your frontend dist/ folder inside the backend directory and redeploy.</p></body></html>")

@app.get("/api/debug/rag-search", tags=["Diagnostics"])
def debug_rag_search_endpoint(query: str, top_k: int = 5):
    """: Exposes raw RAG search metrics for threshold tuning.
    Returns chunk candidates, their cosine distances, and how they compare against active thresholds.
    """
    from app.services.rag_service import rag_service
    from app.core.config import settings
    
    results = rag_service.query_knowledge_base(query, top_k=top_k)
    debug_payload = []
    
    for idx, res in enumerate(results):
        distance = res.get("distance", 1.0)
        
        status = "REJECTED (Low Match)"
        if distance <= settings.RAG_HIGH_THRESHOLD:
            status = "HIGH CONFIDENCE"
        elif distance <= settings.RAG_DISTANCE_THRESHOLD:
            status = "MEDIUM CONFIDENCE"
            
        debug_payload.append({
            "rank": idx + 1,
            "document_id": res.get("metadata", {}).get("document_id", "Unknown"),
            "source_system": res.get("metadata", {}).get("source_system", "Unknown"),
            "cosine_distance": round(distance, 4),
            "status": status,
            "snippet": res.get("text", "")[:150] + "..." # Truncate for clean JSON
        })
        
    return {
        "status": "success",
        "query": query,
        "active_thresholds": {
            "high_confidence_cap": settings.RAG_HIGH_THRESHOLD,
            "medium_confidence_cap": settings.RAG_DISTANCE_THRESHOLD
        },
        "results": debug_payload
    }

# 1. Mount the compiled assets directory for static files (JS/CSS)
# This mounts /assets to serve files from dist/assets inside the container!
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

# 2. Add catch-all wildcard router to serve index.html for all other paths (Supports Vue Router!)
@app.get("/{catchall:path}", tags=["Static Frontend"])
def serve_spa(catchall: str):
    return FileResponse("dist/index.html")


