"""
Pydantic validation schemas for all V.I.S.I.O.N. API endpoints.
Ensures type safety, data validation, and comprehensive error handling.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# LOGS API SCHEMAS
# ============================================================================

class LogEntry(BaseModel):
    """Single log entry from frontend client"""
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    level: str = Field(..., regex="^(DEBUG|INFO|WARN|ERROR)$")
    module: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=5000)
    data: Optional[Dict[str, Any]] = Field(default=None)
    stack: Optional[str] = Field(default=None, max_length=10000)


class BatchLogsRequest(BaseModel):
    """Batch log ingestion request"""
    logs: List[LogEntry] = Field(..., min_items=1, max_items=1000)

    @validator('logs')
    def validate_logs(cls, v):
        if not isinstance(v, list):
            raise ValueError("logs must be a list")
        return v


class LogResponse(BaseModel):
    """Response from log ingestion"""
    status: str = Field(..., regex="^(logged|error)$")
    timestamp: str
    level: Optional[str] = None
    count: Optional[int] = None


# ============================================================================
# UPLOAD API SCHEMAS
# ============================================================================

class DocumentUploadMetadata(BaseModel):
    """Metadata for uploaded document"""
    filename: str = Field(..., min_length=1, max_length=255)
    size_bytes: int = Field(..., ge=0, le=15728640)  # 15MB max
    content_type: str = Field(
        ...,
        regex="^(application/pdf|application/vnd.openxmlformats-officedocument.wordprocessingml.document|text/plain|application/vnd.ms-excel)$"
    )


class UploadResponse(BaseModel):
    """Response from document upload"""
    status: str = Field(..., regex="^(success|error)$")
    message: str
    indexed_count: Optional[int] = None
    error_details: Optional[str] = None


# ============================================================================
# SYNC API SCHEMAS
# ============================================================================

class SyncPageRequest(BaseModel):
    """Request to sync single Confluence page"""
    page_id: str = Field(..., min_length=1, max_length=100, regex="^[0-9]+$")

    @validator('page_id')
    def validate_page_id(cls, v):
        if not v.isdigit():
            raise ValueError("page_id must be numeric")
        return v


class SyncDeltaRequest(BaseModel):
    """Request to sync delta changes"""
    minutes: int = Field(default=60, ge=1, le=1440)  # 1 min to 1 day
    target: Optional[str] = Field(default=None, regex="^(confluence|ado)$")


class SyncWorkitemRequest(BaseModel):
    """Request to sync single ADO workitem"""
    item_id: str = Field(..., min_length=1, max_length=100, regex="^[0-9]+$")

    @validator('item_id')
    def validate_item_id(cls, v):
        if not v.isdigit():
            raise ValueError("item_id must be numeric")
        return v


class SyncFullRefreshRequest(BaseModel):
    """Request full refresh of all synced sources"""
    confirm: bool = Field(..., description="Must be true to proceed")
    target: Optional[str] = Field(default=None, regex="^(confluence|ado|all)$")


class SyncResponse(BaseModel):
    """Response from sync operations"""
    status: str = Field(..., regex="^(queued|in_progress|completed|failed)$")
    message: str
    task_id: Optional[str] = None
    estimated_duration_seconds: Optional[int] = None


# ============================================================================
# DIRECTIVES API SCHEMAS
# ============================================================================

class DirectivesRequest(BaseModel):
    """Request to save/update system directives"""
    content: str = Field(..., min_length=10, max_length=50000)
    role: str = Field(..., regex="^(ADMIN|LEAD|USER|GUEST)$")

    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("content must be at least 10 characters")
        return v.strip()


class DirectivesResponse(BaseModel):
    """Response from directives operations"""
    status: str = Field(..., regex="^(success|error)$")
    message: str
    content: Optional[str] = None
    confluence_url: Optional[str] = None
    ado_url: Optional[str] = None
    confluence_spaces: Optional[str] = None
    ado_projects: Optional[str] = None


# ============================================================================
# SESSION API SCHEMAS
# ============================================================================

class SessionCreateRequest(BaseModel):
    """Request to create new chat session"""
    title: str = Field(..., min_length=1, max_length=255)
    admin_name: str = Field(..., min_length=1, max_length=100)


class SessionUpdateRequest(BaseModel):
    """Request to update existing session"""
    session_id: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=255)


class SessionResponse(BaseModel):
    """Response from session operations"""
    status: str = Field(..., regex="^(success|error)$")
    session_id: Optional[str] = None
    message: str


# ============================================================================
# MESSAGE API SCHEMAS
# ============================================================================

class MessageRequest(BaseModel):
    """Request to save chat message"""
    sender: str = Field(..., regex="^(ADMIN|VISION|SYSTEM)$")
    text: str = Field(..., min_length=1, max_length=50000)
    admin_name: str = Field(..., min_length=1, max_length=100)
    session_id: str = Field(default="default_session", max_length=100)

    @validator('text')
    def validate_text(cls, v):
        if len(v.strip()) < 1:
            raise ValueError("message cannot be empty")
        return v.strip()


class MessageResponse(BaseModel):
    """Response from message operations"""
    status: str = Field(..., regex="^(success|error)$")
    message_id: Optional[int] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# HEALTH CHECK SCHEMAS
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., regex="^(healthy|degraded|unhealthy)$")
    timestamp: str
    service: str
    database: Optional[str] = None
    confluence: Optional[Dict[str, Any]] = None
    ado: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# ERROR RESPONSE SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    status: str = Field(default="error")
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
