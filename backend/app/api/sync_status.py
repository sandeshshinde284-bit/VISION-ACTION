# ============================================================================
# PROJECT V.I.S.I.O.N. - SYNC STATUS & MANAGEMENT API
# ============================================================================
# File Description:
# Provides REST endpoints for querying sync status, history, and triggering
# manual syncs from the admin UI. Returns sync history, last sync timestamps,
# and current operational status.
# ============================================================================

from fastapi import APIRouter, HTTPException, Query, Header
from app.core.config import settings
from app.services.db_service import db_service
from app.services.security_service import security_service
from app.api.auth import verify_session_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync-status", tags=["Sync Status & History"])

# ============================================================================
# SESSION AUTHORIZATION
# ============================================================================
# BUG FIX (2026-10-22): this used to call security_service.is_admin(), a method
# that does not exist anywhere in security_service.py. hasattr() silently
# returned False every time, so is_admin was always False and every endpoint
# below unconditionally raised 403 - these endpoints were completely unusable
# regardless of who called them. Switched to the same session-token check
# sync_routes.py already uses for its own sync endpoints, so this is now
# consistent with the rest of the app AND actually callable.

def require_admin(authorization: str = Header(None)):
    """Verifies the caller's session token (same mechanism as sync_routes.py)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid token format")
    return verify_session_token(parts[1])


# ============================================================================
# SYNC STATUS ENDPOINTS
# ============================================================================

@router.get("/health")
async def get_sync_health():
    """
    Get overall sync system health status.
    Public endpoint - shows if sync system is operational.
    
    Returns:
        {
            "status": "healthy|degraded|error",
            "confluence_configured": bool,
            "ado_configured": bool,
            "database_active": bool,
            "last_check": "2025-01-20T14:32:10"
        }
    """
    try:
        is_confluence = bool(settings.CONFLUENCE_URL and settings.CONFLUENCE_PAT)
        is_ado = bool(settings.ADO_URL and settings.ADO_PAT)
        is_db = True  # If we got here, DB is at least minimal operational
        
        status = "healthy"
        if not (is_confluence or is_ado):
            status = "degraded"
        
        return {
            "status": status,
            "confluence_configured": is_confluence,
            "ado_configured": is_ado,
            "database_active": is_db,
            "last_check": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get sync health: {e}")
        return {
            "status": "error",
            "confluence_configured": False,
            "ado_configured": False,
            "database_active": False,
            "error": str(e)
        }


@router.get("/history")
async def get_sync_history(
    document_id: str = Query(None),
    source_system: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    authorization: str = Header(None)
):
    """
    Get sync operation history for debugging and audit trails.
    Admin-only endpoint.
    
    Query Parameters:
        document_id (str, optional): Filter by specific document
        source_system (str, optional): Filter by CONFLUENCE or ADO
        limit (int): Max results to return (1-200, default 50)
    
    Returns:
        [
            {
                "document_id": "confluence_page_12345",
                "source_system": "CONFLUENCE",
                "sync_type": "full_page_sync",
                "status": "COMPLETE",
                "chunk_count": 47,
                "vector_count": 1,
                "started_at": "2025-01-20T14:32:10.123456",
                "completed_at": "2025-01-20T14:32:45.654321",
                "duration_seconds": 35.5
            },
            ...
        ]
    
    Example:
        GET /api/sync-status/history?source_system=CONFLUENCE&limit=10
    """
    require_admin(authorization)
    
    try:
        results = db_service.get_sync_status(
            document_id=document_id,
            source_system=source_system
        )
        
        # Calculate duration and add helpful metadata
        for result in results[:limit]:
            if result.get("completed_at") and result.get("started_at"):
                try:
                    start = datetime.fromisoformat(result["started_at"])
                    end = datetime.fromisoformat(result["completed_at"])
                    result["duration_seconds"] = (end - start).total_seconds()
                except:
                    result["duration_seconds"] = None
        
        logger.info(f"Retrieved sync history: {len(results)} records")
        return results[:limit]
        
    except Exception as e:
        logger.error(f"Failed to retrieve sync history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sync history: {e}")


@router.get("/last-sync/{source_system}")
async def get_last_sync_info(source_system: str, authorization: str = Header(None)):
    """
    Get the most recent sync operation for a given source system.
    Shows when Confluence or ADO was last synced.
    
    Parameters:
        source_system (str): CONFLUENCE or ADO
    
    Returns:
        {
            "source_system": "CONFLUENCE",
            "last_completed_at": "2025-01-20T14:32:45",
            "last_status": "COMPLETE",
            "last_document": "confluence_page_12345",
            "total_syncs": 42,
            "successful_syncs": 40,
            "failed_syncs": 2,
            "minutes_since_last_sync": 5
        }
    
    Example:
        GET /api/sync-status/last-sync/CONFLUENCE
    """
    require_admin(authorization)
    
    try:
        if source_system not in ["CONFLUENCE", "ADO"]:
            raise HTTPException(status_code=400, detail="Invalid source_system. Use CONFLUENCE or ADO")
        
        results = db_service.get_sync_status(source_system=source_system)
        
        if not results:
            return {
                "source_system": source_system,
                "last_completed_at": None,
                "last_status": "NEVER",
                "total_syncs": 0,
                "successful_syncs": 0,
                "failed_syncs": 0,
                "minutes_since_last_sync": None
            }
        
        # Get stats from all syncs
        total = len(results)
        successful = len([r for r in results if r.get("status") == "COMPLETE"])
        failed = len([r for r in results if r.get("status") == "ERROR"])
        
        # Get last completed
        last_result = results[0]
        last_completed = last_result.get("completed_at")
        
        minutes_since = None
        if last_completed:
            try:
                last_time = datetime.fromisoformat(last_completed)
                minutes_since = int((datetime.utcnow() - last_time).total_seconds() / 60)
            except:
                pass
        
        return {
            "source_system": source_system,
            "last_completed_at": last_completed,
            "last_status": last_result.get("status"),
            "last_document": last_result.get("document_id"),
            "total_syncs": total,
            "successful_syncs": successful,
            "failed_syncs": failed,
            "minutes_since_last_sync": minutes_since
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get last sync info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_sync_summary(authorization: str = Header(None)):
    """
    Get a high-level summary of sync operations for the dashboard.
    Shows both Confluence and ADO sync status at a glance.
    
    Returns:
        {
            "confluence": {
                "last_synced": "5 minutes ago",
                "status": "healthy",
                "total_docs_synced": 127,
                "last_status": "COMPLETE"
            },
            "ado": {
                "last_synced": "2 hours ago",
                "status": "healthy",
                "total_docs_synced": 45,
                "last_status": "COMPLETE"
            },
            "system_health": "healthy"
        }
    """
    require_admin(authorization)
    
    try:
        confluence_info = db_service.get_sync_status(source_system="CONFLUENCE")
        ado_info = db_service.get_sync_status(source_system="ADO")
        
        def format_system_summary(results, system_name):
            if not results:
                return {
                    "last_synced": "Never",
                    "status": "not_configured",
                    "total_syncs": 0,
                    "last_status": None
                }
            
            last = results[0]
            last_completed = last.get("completed_at")
            
            minutes_ago = None
            if last_completed:
                try:
                    last_time = datetime.fromisoformat(last_completed)
                    mins = int((datetime.utcnow() - last_time).total_seconds() / 60)
                    if mins < 60:
                        minutes_ago = f"{mins} minute{'s' if mins != 1 else ''} ago"
                    else:
                        hours = mins // 60
                        minutes_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
                except:
                    minutes_ago = "Unknown"
            
            # Determine health status
            status = "healthy"
            if last.get("status") == "ERROR":
                status = "error"
            elif last.get("status") == "IN_PROGRESS":
                status = "syncing"
            elif minutes_ago and "hour" in minutes_ago and int(minutes_ago.split()[0]) > 24:
                status = "stale"
            
            return {
                "last_synced": minutes_ago or "Never",
                "status": status,
                "total_syncs": len(results),
                "last_status": last.get("status"),
                "last_document": last.get("document_id")
            }
        
        return {
            "confluence": format_system_summary(confluence_info, "CONFLUENCE"),
            "ado": format_system_summary(ado_info, "ADO"),
            "system_health": "healthy"  # Can be expanded based on error counts
        }
        
    except Exception as e:
        logger.error(f"Failed to get sync summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
