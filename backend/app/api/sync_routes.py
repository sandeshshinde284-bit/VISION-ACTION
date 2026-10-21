from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Request
from app.core.config import settings
from app.services.db_service import db_service
from app.services.security_service import security_service
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import sys
import os

# Ensure backend directory is in path for sync_connectors import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../../")

import sync_connectors

# Setup module logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["Sync Management"])

# Initialize Rate Limiter for Sync Endpoints ---
limiter = Limiter(key_func=get_remote_address)

# ============================================================================
# # Helper function for admin authorization
# ============================================================================

def require_admin():
    """Middleware check that ensures admin access before sync operations"""
    # Try to get admin status from security service
    is_admin = security_service.is_admin() if hasattr(security_service, 'is_admin') else False
    
    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized: Only administrators can trigger document syncs"
        )

# ============================================================================
# # Confluence Sync Endpoints
# ============================================================================

@router.post("/confluence/page/{page_id}")
@limiter.limit("20/hour")
async def sync_single_confluence_page(request: Request, page_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger synchronization of a single Confluence page by ID.
    Executes in background to avoid timeout.
    
    # Requires admin authentication
    # Rate limited to 20 syncs per hour
    
    Args:
        page_id (str): The Confluence page ID to sync
    
    Returns:
        {"status": "queued", "page_id": page_id}
    
    Example:
        POST /api/sync/confluence/page/5475763080
    """
    # # Check admin authorization
    require_admin()
    
    if not page_id or not page_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid page_id format")
    
    if not settings.CONFLUENCE_URL or not settings.CONFLUENCE_PAT:
        raise HTTPException(status_code=503, detail="Confluence not configured")
    
    logger.info(f"Manual sync requested for Confluence page [{page_id}]")
    background_tasks.add_task(sync_connectors.sync_confluence_page, page_id)
    
    return {
        "status": "queued",
        "page_id": page_id,
        "message": f"Page {page_id} queued for synchronization"
    }


@router.post("/confluence/delta")
@limiter.limit("5/hour")
async def sync_recent_confluence(
    request: Request,
    minutes: int = Query(30, ge=1, le=1440),
    background_tasks: BackgroundTasks = None
):
    """
    Manually trigger incremental synchronization of recently modified Confluence pages.
    Scans pages modified in the last N minutes.
    
    # Requires admin authentication
    # Rate limited to 5 syncs per hour
    
    Args:
        minutes (int): Look-back window in minutes (1-1440, default 30)
    
    Returns:
        {"status": "queued", "minutes": minutes}
    
    Example:
        POST /api/sync/confluence/delta?minutes=60
    """
    # # Check admin authorization
    require_admin()
    
    if not settings.CONFLUENCE_URL or not settings.CONFLUENCE_PAT:
        raise HTTPException(status_code=503, detail="Confluence not configured")
    
    logger.info(f"Delta sync requested for Confluence pages modified in last [{minutes}] minutes")
    background_tasks.add_task(sync_connectors.sync_recent_confluence_pages, minutes)
    
    return {
        "status": "queued",
        "minutes": minutes,
        "message": f"Delta sync initiated for pages modified in last {minutes} minutes"
    }


@router.post("/ado/workitem/{item_id}")
@limiter.limit("20/hour")
async def sync_single_ado_workitem(request: Request, item_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger synchronization of a single Azure DevOps work item by ID.
    Executes in background to avoid timeout.
    
    # Requires admin authentication
    # Rate limited to 20 syncs per hour
    
    Args:
        item_id (str): The ADO work item ID to sync
    
    Returns:
        {"status": "queued", "item_id": item_id}
    
    Example:
        POST /api/sync/ado/workitem/59912
    """
    # # Check admin authorization
    require_admin()
    
    if not item_id or not item_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid item_id format")
    
    if not settings.ADO_URL or not settings.ADO_PAT:
        raise HTTPException(status_code=503, detail="Azure DevOps not configured")
    
    logger.info(f"Manual sync requested for ADO work item [{item_id}]")
    background_tasks.add_task(sync_connectors.sync_ado_workitem, item_id)
    
    return {
        "status": "queued",
        "item_id": item_id,
        "message": f"Work item {item_id} queued for synchronization"
    }


@router.post("/ado/delta")
@limiter.limit("5/hour")
async def sync_recent_ado(
    request: Request,
    days: int = Query(7, ge=1, le=180),
    background_tasks: BackgroundTasks = None
):
    """
    Manually trigger incremental synchronization of recently updated ADO work items.
    Scans items modified in the last N days.
    
    # Requires admin authentication
    # Rate limited to 5 syncs per hour
    
    Args:
        days (int): Look-back window in days (1-180, default 7)
    
    Returns:
        {"status": "queued", "days": days}
    
    Example:
        POST /api/sync/ado/delta?days=14
    """
    # # Check admin authorization
    require_admin()
    
    if not settings.ADO_URL or not settings.ADO_PAT:
        raise HTTPException(status_code=503, detail="Azure DevOps not configured")
    
    logger.info(f"Delta sync requested for ADO work items modified in last [{days}] days")
    
    # Delegate to sync_connectors if it has ado delta sync function
    if hasattr(sync_connectors, 'sync_recent_ado_workitems'):
        background_tasks.add_task(sync_connectors.sync_recent_ado_workitems, days)
    else:
        logger.warning(f"sync_recent_ado_workitems not implemented yet in sync_connectors")
        raise HTTPException(status_code=501, detail="ADO delta sync not implemented")
    
    return {
        "status": "queued",
        "days": days,
        "message": f"Delta sync initiated for items modified in last {days} days"
    }


# ============================================================================
# Sync Status & Diagnostics Endpoints
# ============================================================================

@router.get("/status")
async def get_sync_status():
    """
    Returns detailed statistics about synced documents and indexing health.
    
    Returns:
        {
            "total_documents": int,
            "total_vectors": int,
            "last_confluence_sync": datetime,
            "last_ado_sync": datetime,
            "confluence_space": str,
            "rag_database_target": str
        }
    
    Example:
        GET /api/sync/status
    """
    try:
        stats = db_service.get_document_sync_stats()
        return {
            "status": "healthy",
            "database_target": settings.DATABASE_TARGET,
            "confluence_space": settings.CONFLUENCE_SPACES,
            "rag_distance_threshold": settings.RAG_DISTANCE_THRESHOLD,
            "rag_top_k": settings.RAG_TOP_K,
            **stats
        }
    except Exception as e:
        logger.error(f"Failed to retrieve sync status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sync status: {str(e)}")


@router.get("/health")
async def sync_health_check():
    """
    Performs connectivity checks for Confluence and ADO endpoints.
    
    Returns:
        {
            "confluence": {"reachable": bool, "status": str},
            "ado": {"reachable": bool, "status": str},
            "database": {"healthy": bool, "type": str}
        }
    
    Example:
        GET /api/sync/health
    """
    health_report = {
        "timestamp": None,
        "confluence": {"reachable": False, "status": "unknown"},
        "ado": {"reachable": False, "status": "unknown"},
        "database": {"healthy": False, "type": settings.DATABASE_TARGET}
    }
    
    # Check Confluence connectivity
    if settings.CONFLUENCE_URL and settings.CONFLUENCE_PAT:
        try:
            import requests
            res = requests.head(settings.CONFLUENCE_URL.rstrip('/'), timeout=5)
            health_report["confluence"]["reachable"] = res.status_code < 400
            health_report["confluence"]["status"] = f"HTTP {res.status_code}"
        except Exception as e:
            health_report["confluence"]["status"] = f"Error: {str(e)}"
    else:
        health_report["confluence"]["status"] = "Not configured"
    
    # Check ADO connectivity
    if settings.ADO_URL and settings.ADO_PAT:
        try:
            import requests
            res = requests.head(settings.ADO_URL.rstrip('/'), timeout=5)
            health_report["ado"]["reachable"] = res.status_code < 400
            health_report["ado"]["status"] = f"HTTP {res.status_code}"
        except Exception as e:
            health_report["ado"]["status"] = f"Error: {str(e)}"
    else:
        health_report["ado"]["status"] = "Not configured"
    
    # Check database health
    try:
        health_report["database"]["healthy"] = db_service.health_check()
    except Exception as e:
        health_report["database"]["healthy"] = False
        health_report["database"]["status"] = f"Error: {str(e)}"
    
    from datetime import datetime
    health_report["timestamp"] = datetime.utcnow().isoformat()
    
    return health_report


@router.post("/full-refresh")
async def trigger_full_knowledge_base_refresh(background_tasks: BackgroundTasks):
    """
    Triggers a complete re-sync of all Confluence pages in the configured space(s).
    WARNING: This is expensive and may take several minutes.
    
    Returns:
        {"status": "queued", "operation": "full_refresh"}
    
    Example:
        POST /api/sync/full-refresh
    """
    logger.warning(f"Full knowledge base refresh initiated - this may take several minutes")
    
    async def run_full_sync():
        try:
            # Full delta with large lookback window
            sync_connectors.sync_recent_confluence_pages(minutes=10080)  # 7 days
            logger.info("Full Confluence refresh completed successfully")
        except Exception as e:
            logger.error(f"Full refresh failed: {e}")
    
    background_tasks.add_task(run_full_sync)
    
    return {
        "status": "queued",
        "operation": "full_refresh",
        "message": "Full knowledge base refresh initiated. Monitor /api/sync/health for progress."
    }
