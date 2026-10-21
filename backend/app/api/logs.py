"""
Logging API endpoints for frontend log ingestion and log management.
Includes input validation via Pydantic schemas.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.logging_config import get_service_logger
from app.api.schemas import LogEntry, BatchLogsRequest, LogResponse

router = APIRouter(prefix="/api/logs", tags=["logs"])
logger = get_service_logger("logs_api")


@router.post("/", response_model=LogResponse)
async def ingest_frontend_logs(log_entry: LogEntry):
    """
    Ingest logs from frontend client with validation.

    Request body (validated):
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
        # Pydantic validation already applied by FastAPI
        timestamp = log_entry.timestamp or datetime.utcnow().isoformat()
        level = log_entry.level
        module = log_entry.module
        message = log_entry.message
        data = log_entry.data or {}

        # Log to backend system
        logger.info(
            f"[{level}] [{module}] {message}",
            extra={"data": data}
        )

        return LogResponse(
            status="logged",
            timestamp=timestamp,
            level=level,
        )
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


@router.post("/batch", response_model=LogResponse)
async def ingest_batch_logs(batch_request: BatchLogsRequest):
    """
    Ingest batch of logs from frontend with validation.

    Request body (validated):
    {
        "logs": [
            {"timestamp": "...", "level": "INFO", "module": "...", ...},
            ...
        ]
    }
    """
    try:
        # Pydantic validation already applied by FastAPI
        logs = batch_request.logs

        for log_entry in logs:
            level = log_entry.level
            module = log_entry.module
            message = log_entry.message

            logger.info(f"[{level}] [{module}] {message}")

        logger.info(f"Ingested batch of {len(logs)} frontend logs")

        return LogResponse(
            status="logged",
            count=len(logs),
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to ingest batch logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid batch")
