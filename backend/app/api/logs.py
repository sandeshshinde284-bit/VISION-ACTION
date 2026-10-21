"""
Logging API endpoints for frontend log ingestion and log management.
"""

from fastapi import APIRouter, Request, HTTPException
from datetime import datetime
from app.logging_config import get_service_logger

router = APIRouter(prefix="/api/logs", tags=["logs"])
logger = get_service_logger("logs_api")


@router.post("/")
async def ingest_frontend_logs(request: Request):
    """
    Ingest logs from frontend client.

    Request body:
    {
        "timestamp": "2026-10-21T12:34:56Z",
        "level": "ERROR",
        "module": "ChatInput",
        "message": "Failed to send message",
        "data": {"error": "Network timeout"},
        "stack": "..."
    }
    """
    try:
        log_entry = await request.json()

        timestamp = log_entry.get("timestamp", datetime.utcnow().isoformat())
        level = log_entry.get("level", "UNKNOWN")
        module = log_entry.get("module", "UNKNOWN")
        message = log_entry.get("message", "No message")
        data = log_entry.get("data", {})

        # Log to backend system
        logger.info(
            f"[{level}] [{module}] {message}",
            extra={"data": data}
        )

        return {
            "status": "logged",
            "timestamp": timestamp,
            "level": level,
        }
    except Exception as e:
        logger.error(f"Failed to ingest frontend log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid log entry")


@router.get("/health")
async def logs_health():
    """Check logging system health."""
    logger.debug("Logs API health check")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "logs",
    }


@router.post("/batch")
async def ingest_batch_logs(request: Request):
    """
    Ingest batch of logs from frontend.

    Request body:
    {
        "logs": [
            {"timestamp": "...", "level": "INFO", "module": "...", ...},
            ...
        ]
    }
    """
    try:
        data = await request.json()
        logs = data.get("logs", [])

        if not isinstance(logs, list):
            raise ValueError("logs must be a list")

        for log_entry in logs:
            level = log_entry.get("level", "INFO")
            module = log_entry.get("module", "UNKNOWN")
            message = log_entry.get("message", "")

            logger.info(f"[{level}] [{module}] {message}")

        logger.info(f"Ingested batch of {len(logs)} frontend logs")

        return {
            "status": "logged",
            "count": len(logs),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to ingest batch logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid batch")
