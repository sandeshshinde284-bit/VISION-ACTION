# ============================================================================
# PROJECT V.I.S.I.O.N. - MULTI-FILE RAG UPLOAD GATEWAY
# ============================================================================
# File Description:
# This module defines the REST API routes for uploading documents (PDF, DOCX, TXT)
# from the Vue frontend cockpit. 
# Uploaded files are securely cached in a temporary folder, processed sequentially 
# through the RAG parser/embedder, and then instantly deleted from local storage 
# to enforce corporate sandboxing guidelines.
# ============================================================================

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Header
from app.services.rag_service import rag_service # Local ChromaDB/Embedding engine
from app.core.config import settings
from app.api.auth import verify_session_token
import hashlib
import time
import logging
import os
import shutil
import re

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

# Define local, temporary directory to write multipart buffers before indexing
# This completely bypasses any OneDrive sync locks and Vite/HMR file-system watchers!
# (Refactored to be platform-aware to prevent serverless Cloud Run read-only disk crashes!)
if os.name != 'nt': # Running on Cloud Run (Linux/Unix container)
    TEMP_UPLOAD_DIR = "/tmp/temp_docs"
else: # Running locally (Windows/Mac)
    TEMP_UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "temp_docs"))
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True) # Ensure temp folder exists

# Strict Corporate Safety Guardrails
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
RATE_LIMIT_WINDOW = 60 # 60 seconds
MAX_UPLOADS_PER_WINDOW = 5

# In-memory dictionary for sliding-window rate limiting
# Format: { "session_id_or_ip": [timestamp1, timestamp2] }
_upload_rate_tracker = {}

def _check_rate_limit(client_id: str) -> bool:
    """Checks if the client has exceeded the upload rate limit."""
    now = time.time()
    # Clean up old timestamps
    if client_id in _upload_rate_tracker:
        _upload_rate_tracker[client_id] = [t for t in _upload_rate_tracker[client_id] if now - t < RATE_LIMIT_WINDOW]
    else:
        _upload_rate_tracker[client_id] = []

    if len(_upload_rate_tracker[client_id]) >= MAX_UPLOADS_PER_WINDOW:
        return False

    _upload_rate_tracker[client_id].append(now)
    return True


def _is_safe_filename(filename: str) -> bool:
    """
    Security: Validate filenames to prevent directory traversal and injection attacks.

    Rules:
    - Must contain alphanumeric, dots, hyphens, underscores only
    - Cannot contain path separators (/ or \)
    - Cannot be empty
    - Max 255 characters
    """
    if not filename or len(filename) > 255:
        return False

    # Block path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        return False

    # Allow: alphanumeric, dots, hyphens, underscores
    # Pattern: filename.extension
    allowed_pattern = r'^[a-zA-Z0-9._-]+$'
    return bool(re.match(allowed_pattern, filename))

@router.post("/api/upload", tags=["Knowledge Ingestion"])
async def upload_documents(
    files: list[UploadFile] = File(...),
    authorization: str = Header(None)
):
    """
    Receives an array of multipart corporate documents, saves them to a secure temp
    directory, embeds them into ChromaDB, and purges the raw files right after indexing.

    Security: Requires session token in Authorization header
    Rate limited to 5 uploads per minute

    Supported formats: PDF, DOCX, TXT
    Max file size: 15MB per file

    Example (with session token):
        POST /api/upload
        Authorization: Bearer <session_token>
        Content-Type: multipart/form-data
    """
    
    # Verify session token
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = parts[1]
    username = verify_session_token(token)
    
    # Rate Limiting - Use authenticated user ID
    client_id = username
    if not _check_rate_limit(client_id):
        logger.warning(f"Upload Rate Limit Exceeded for user {client_id}!")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many files uploaded recently. Please wait a minute.")

    ingestion_results = []
    logger.info(f"Upload request from {client_id}. Total files: {len(files)}")

    for file in files:
        filename = file.filename

        # Security: Validate filename - prevent directory traversal & malicious names
        if not _is_safe_filename(filename):
            logger.warning(f"SECURITY: Blocked unsafe filename: {filename}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid filename: {filename}")

        logger.info(f"Preparing to process: [{filename}] for user {client_id}")

        # Create unique absolute secure temp path
        temp_file_path = os.path.join(TEMP_UPLOAD_DIR, filename)

        try:
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

            # Streaming Byte-Counter and SHA-256 Hash Generation
            total_bytes_written = 0
            hasher = hashlib.sha256()
            
            with open(temp_file_path, "wb") as buffer:
                while True:
                    chunk = await file.read(1024 * 1024) # Read in 1MB chunks
                    if not chunk:
                        break # EOF
                        
                    total_bytes_written += len(chunk)
                    
                    # Hardened server-side guardrail (OOM Protection)
                    # Abort the stream instantly if it crosses the limit, rather than trusting spoofable headers!
                    if total_bytes_written > MAX_FILE_SIZE:
                        logger.warning(f"SECURITY BLOCK: File [{filename}] stream aborted. Exceeded true 15MB limit!")
                        buffer.close()
                        os.remove(temp_file_path)
                        raise ValueError("File stream exceeded maximum allowed size of 15MB.")
                    
                    buffer.write(chunk)
                    hasher.update(chunk)
            
            file_hash = hasher.hexdigest()
            doc_id = f"doc_{file_hash[:24]}" # Create a 24-char unique ID based on the file's binary content
            logger.info(f"Streamed [{filename}] ({total_bytes_written} bytes) safely. SHA-256 ID: {doc_id}")

            # Deduplication (Check database before wasting Vertex AI tokens)
            from app.services.db_service import db_service
            if db_service.get_document(doc_id):
                logger.info(f"Deduplication hit: [{filename}] (Hash: {doc_id}) is already in the vector database! Skipping embeddings.")
                ingestion_results.append({
                    "filename": filename,
                    "status": "indexed",
                    "message": "File was already indexed (Deduplicated successfully)."
                })
                continue

            # Trigger the local RAG parser, passing the unique Hash as the document_id
            custom_metadata = {
                "document_id": doc_id,
                "title": filename,
                "source_system": "UPLOAD",
                "space_key": "UPLOAD",
                "version": 1
            }
            success = rag_service.ingest_document(temp_file_path, filename, custom_metadata=custom_metadata)

            # Record success metrics for frontend feedback chips
            if success:
                ingestion_results.append({
                    "filename": filename,
                    "status": "indexed",
                    "message": "Vector indexing complete."
                })
            else:
                ingestion_results.append({
                    "filename": filename,
                    "status": "failed",
                    "message": "Extracted content was empty or unparseable."
                })

        except ValueError as ve:
            if str(ve) == "RESTRICTED_DATA_VIOLATION":
                logger.warning(f"DLP GUARDRAIL BLOCKED: Rejecting file upload [{filename}] - Policy Violation.")
                ingestion_results.append({
                    "filename": filename,
                    "status": "blocked",
                    "message": "Security Block: This document contains restricted corporate records (passwords/salaries) and is barred by DLP policy."
                })
            else:
                logger.error(f"Value error during ingestion [{filename}]: {ve}")
                ingestion_results.append({
                    "filename": filename,
                    "status": "error",
                    "message": f"Processing failure: {str(ve)}"
                })

        except Exception as e:
            logger.error(f"Error handling file upload [{filename}]: {e}")
            ingestion_results.append({
                "filename": filename,
                "status": "error",
                "message": f"Critical server upload crash: {str(e)}"
            })

        finally:
            # Critical: Instantly delete the raw document from local server storage
            # This ensures only vectors and index chunks remain inside the local secure sandbox.
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"Purged raw file [{filename}] from secure cache.")
                except Exception as pe:
                    logger.warning(f"Failed to delete secure cache file [{filename}]: {pe}")

    return {
        "status": "completed",
        "results": ingestion_results
    }
