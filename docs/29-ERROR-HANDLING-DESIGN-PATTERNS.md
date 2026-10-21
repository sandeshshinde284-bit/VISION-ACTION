# V.I.S.I.O.N. ERROR HANDLING & RELIABILITY DESIGN PATTERNS

**Date:** 2026-10-21  
**Status:** ARCHITECTURAL SPECIFICATION  
**Version:** 1.0  
**Audience:** Backend & Frontend Developers

---

## EXECUTIVE SUMMARY

Error handling in V.I.S.I.O.N. must follow consistent patterns across all integration points:
- **Confluence Sync** — Document pull with network/auth resilience
- **ADO Sync** — Work item pull with network/auth resilience  
- **Web Search** — Query execution with rate-limit handling
- **RAG Ingestion** — Document parsing with detailed failure modes
- **User Feedback** — Real-time notifications via WebSocket

This document defines the standard patterns for all integration points.

---

## ERROR TYPE CLASSIFICATION

All errors fall into one of 6 categories:

### 1. NETWORK ERRORS (Transient, Retryable)

| Error | HTTP | Behavior | Retry? | Action |
|-------|------|----------|--------|--------|
| `network_timeout` | — | Request took >timeout | ✅ YES | Exponential backoff |
| `network_unreachable` | — | DNS/connection failed | ✅ YES | Exponential backoff |
| `ssl_verification_failed` | — | Certificate error | ❌ NO | Admin action needed |
| `proxy_error` | 407 | Proxy auth required | ❌ NO | Config fix |

### 2. AUTHENTICATION ERRORS (Permanent, Non-Retryable)

| Error | HTTP | Behavior | Retry? | Action |
|-------|------|----------|--------|--------|
| `invalid_credentials` | 401 | PAT/token invalid | ❌ NO | Replace credentials |
| `token_expired` | 401 | Token time-limited | ❌ NO | Re-authenticate |
| `permission_denied` | 403 | User lacks access | ❌ NO | Request access |
| `mfa_required` | 403 | MFA needed | ❌ NO | Enable MFA |

### 3. RATE LIMITING (Transient, Retryable with delay)

| Error | HTTP | Behavior | Retry? | Action |
|-------|------|----------|--------|--------|
| `rate_limit_exceeded` | 429 | Too many requests | ✅ YES | Backoff + retry |
| `quota_exceeded` | 429 | Monthly limit hit | ❌ NO | Wait or upgrade |
| `api_throttled` | 503 | Server throttling | ✅ YES | Exponential backoff |

### 4. DATA ERRORS (Permanent, Non-Retryable)

| Error | HTTP | Behavior | Retry? | Action |
|-------|------|----------|--------|--------|
| `not_found` | 404 | Resource doesn't exist | ❌ NO | Skip or report |
| `document_locked` | 423 | Page/item locked | ✅ MAYBE | Retry after delay |
| `document_archived` | 410 | Page/item archived | ❌ NO | Skip |
| `invalid_format` | 400 | File type unsupported | ❌ NO | Reject |
| `file_too_large` | 413 | Exceeds max size | ❌ NO | Reject |

### 5. SYSTEM ERRORS (Transient, Retryable)

| Error | Behavior | Retry? | Action |
|-------|----------|--------|--------|
| `database_connection_lost` | Can't reach DB | ✅ YES | Exponential backoff |
| `vector_store_down` | ChromaDB/pgvector unreachable | ✅ YES | Exponential backoff |
| `disk_space_full` | Storage exhausted | ❌ NO | Admin cleanup |
| `memory_limit_exceeded` | OOM | ❌ NO | Restart service |

### 6. SERVICE ERRORS (Usually Transient)

| Error | Behavior | Retry? | Action |
|-------|----------|--------|--------|
| `service_unavailable` | 503 | Temp outage | ✅ YES | Backoff + retry |
| `internal_server_error` | 500 | Unexpected crash | ✅ YES | Backoff + retry |
| `bad_gateway` | 502 | Upstream issue | ✅ YES | Backoff + retry |

---

## STANDARD ERROR RESPONSE FORMAT

All sync/ingestion operations return this structure:

```json
{
  "status": "success|error|partial",
  "request_id": "req_12345abc",
  "timestamp": "2026-10-21T18:05:30Z",
  "source": "confluence|ado|web_search|rag_ingestion",
  
  "success_data": {
    "document_id": "confluence_page_12345",
    "title": "Engineering Architecture Doc",
    "chunks_processed": 42,
    "vectors_stored": 42,
    "duration_seconds": 5.3
  },
  
  "error": {
    "error_type": "network_timeout",
    "error_message": "Confluence server did not respond within 15 seconds",
    "error_code": "CONF_TIMEOUT_001",
    "retryable": true,
    "retry_count": 0,
    "max_retries": 3,
    "next_retry_at": "2026-10-21T18:06:00Z",
    "details": {
      "timeout_seconds": 15,
      "attempted_url": "https://confluence.example.com/wiki/rest/api/content/12345",
      "response_code": null
    }
  },
  
  "metadata": {
    "attempt": 1,
    "source_system": "CONFLUENCE",
    "space_key": "ARCH",
    "page_id": "12345"
  }
}
```

---

## CONFLUENCE SYNC ERROR HANDLING

### Success Case ✅

```python
def sync_confluence_page(page_id: str) -> SyncResponse:
    """
    Sync single Confluence page into RAG.
    Returns structured response with success/error details.
    """
    try:
        # GET page from Confluence API
        res = requests.get(
            f"{url}/wiki/rest/api/content/{page_id}?expand=body.storage",
            auth=auth,
            timeout=15
        )
        
        # HANDLE DIFFERENT HTTP STATUS CODES
        if res.status_code == 200:
            # SUCCESS CASE
            data = res.json()
            title = data.get("title")
            html_body = data.get("body", {}).get("storage", {}).get("value")
            
            # Convert HTML → Markdown
            markdown = convert_html_to_markdown(html_body)
            
            # Ingest into RAG
            ingest_result = rag_service.ingest_document(
                content=markdown,
                metadata={"source": "confluence", "page_id": page_id}
            )
            
            if ingest_result["status"] == "success":
                return SyncResponse(
                    status="success",
                    document_id=f"confluence_page_{page_id}",
                    title=title,
                    chunks_processed=ingest_result["chunks"],
                    vectors_stored=ingest_result["vectors"],
                    duration_seconds=ingest_result["duration"]
                )
            else:
                # RAG INGESTION FAILED
                return SyncResponse(
                    status="error",
                    error_type="ingestion_failed",
                    error_message=ingest_result["error"],
                    retryable=False  # Parsing error, not network
                )
        
        elif res.status_code == 401:
            # AUTHENTICATION FAILED
            return SyncResponse(
                status="error",
                error_type="invalid_credentials",
                error_message="Confluence PAT is invalid or expired",
                retryable=False
            )
        
        elif res.status_code == 403:
            # PERMISSION DENIED
            return SyncResponse(
                status="error",
                error_type="permission_denied",
                error_message=f"No permission to access page {page_id}",
                retryable=False
            )
        
        elif res.status_code == 404:
            # NOT FOUND
            return SyncResponse(
                status="error",
                error_type="not_found",
                error_message=f"Page {page_id} not found in Confluence",
                retryable=False
            )
        
        elif res.status_code == 429:
            # RATE LIMITED
            retry_after = res.headers.get("Retry-After", 60)
            return SyncResponse(
                status="error",
                error_type="rate_limit_exceeded",
                error_message="Confluence API rate limit hit",
                retryable=True,
                next_retry_at=datetime.utcnow() + timedelta(seconds=int(retry_after))
            )
        
        elif res.status_code >= 500:
            # SERVER ERROR (transient)
            return SyncResponse(
                status="error",
                error_type="service_unavailable",
                error_message=f"Confluence server error (HTTP {res.status_code})",
                retryable=True,
                next_retry_at=datetime.utcnow() + timedelta(seconds=30)  # 30s backoff
            )
        
        else:
            # UNEXPECTED HTTP CODE
            return SyncResponse(
                status="error",
                error_type="unexpected_http_code",
                error_message=f"Unexpected HTTP {res.status_code}",
                retryable=False
            )
    
    except requests.exceptions.Timeout:
        # NETWORK TIMEOUT (transient)
        return SyncResponse(
            status="error",
            error_type="network_timeout",
            error_message="Confluence server did not respond within 15 seconds",
            retryable=True,
            next_retry_at=datetime.utcnow() + timedelta(seconds=5)  # 5s backoff
        )
    
    except requests.exceptions.ConnectionError as e:
        # NETWORK UNREACHABLE (transient)
        return SyncResponse(
            status="error",
            error_type="network_unreachable",
            error_message=f"Cannot reach Confluence server: {str(e)}",
            retryable=True,
            next_retry_at=datetime.utcnow() + timedelta(seconds=10)  # 10s backoff
        )
    
    except requests.exceptions.SSLError:
        # SSL CERTIFICATE ERROR (permanent)
        return SyncResponse(
            status="error",
            error_type="ssl_verification_failed",
            error_message="SSL certificate verification failed",
            retryable=False
        )
    
    except Exception as e:
        # UNEXPECTED ERROR
        logger.exception(f"Unexpected error syncing Confluence page {page_id}")
        return SyncResponse(
            status="error",
            error_type="internal_error",
            error_message="Unexpected server error",
            retryable=True,
            next_retry_at=datetime.utcnow() + timedelta(seconds=60)
        )
```

---

## ADO SYNC ERROR HANDLING

Same pattern as Confluence:

```python
def sync_ado_workitem(item_id: str) -> SyncResponse:
    """Sync ADO work item with structured error handling."""
    
    try:
        res = requests.get(
            f"{ado_url}/_apis/wit/workitems/{item_id}?api-version=7.0",
            auth=("", pat),
            timeout=15
        )
        
        if res.status_code == 200:
            # SUCCESS
            return SyncResponse(status="success", ...)
        
        elif res.status_code == 401:
            return SyncResponse(
                status="error",
                error_type="invalid_credentials",
                error_message="ADO PAT is invalid or expired",
                retryable=False
            )
        
        # ... etc (same pattern as Confluence)
    
    except requests.exceptions.Timeout:
        return SyncResponse(
            status="error",
            error_type="network_timeout",
            error_message="ADO server not responding",
            retryable=True
        )
```

---

## WEB SEARCH ERROR HANDLING

```python
def search_knowledge_base(query: str, scope: str) -> SearchResponse:
    """
    Search @web, @internal, or @both.
    scope: "web" | "internal" | "both"
    """
    
    try:
        if scope == "web":
            results = search_web(query)
        elif scope == "internal":
            results = search_confluence_and_ado(query)
        elif scope == "both":
            web_results = search_web(query)
            internal_results = search_confluence_and_ado(query)
            results = merge_results(web_results, internal_results)
        
        return SearchResponse(
            status="success",
            query=query,
            scope=scope,
            results=results,
            count=len(results),
            duration_seconds=elapsed
        )
    
    except requests.exceptions.Timeout:
        return SearchResponse(
            status="error",
            error_type="search_timeout",
            error_message="Search took too long (>30 seconds)",
            retryable=True
        )
    
    except RateLimitError:
        return SearchResponse(
            status="error",
            error_type="rate_limit_exceeded",
            error_message="Too many searches. Please wait 1 minute.",
            retryable=True,
            next_retry_at=datetime.utcnow() + timedelta(minutes=1)
        )
    
    except NoResultsError:
        return SearchResponse(
            status="success",  # Not an error, just no results
            results=[],
            count=0,
            message="No results found for query"
        )
```

---

## RAG INGESTION ERROR HANDLING

```python
def ingest_document(file_path: str, metadata: dict) -> IngestionResponse:
    """
    Ingest document into RAG.
    Returns detailed success/error response.
    """
    
    start_time = time.time()
    
    try:
        # STEP 1: Parse file
        try:
            chunks = chunk_document(file_path)
        except UnicodeDecodeError:
            return IngestionResponse(
                status="error",
                error_type="invalid_encoding",
                error_message="File is not valid UTF-8 text",
                retryable=False
            )
        except PdfParsingError as e:
            return IngestionResponse(
                status="error",
                error_type="document_parsing_failed",
                error_message=f"Cannot parse PDF: {str(e)}",
                retryable=False
            )
        except Exception as e:
            return IngestionResponse(
                status="error",
                error_type="parsing_failed",
                error_message=f"Failed to parse document: {str(e)}",
                retryable=False
            )
        
        # STEP 2: Embed chunks (call Vertex AI)
        try:
            vectors = embed_chunks(chunks)
        except QuotaExceededError:
            return IngestionResponse(
                status="error",
                error_type="quota_exceeded",
                error_message="Vertex AI monthly quota exceeded",
                retryable=False  # Requires payment/upgrade
            )
        except RateLimitError:
            return IngestionResponse(
                status="error",
                error_type="rate_limit_exceeded",
                error_message="Vertex AI rate limit hit",
                retryable=True,
                next_retry_at=datetime.utcnow() + timedelta(minutes=1)
            )
        except TokenWindowExceededError:
            return IngestionResponse(
                status="error",
                error_type="token_limit_exceeded",
                error_message=f"Document too large for embedding ({chunks} chunks)",
                retryable=False  # Need to split differently
            )
        except VertexAIError as e:
            return IngestionResponse(
                status="error",
                error_type="embedding_failed",
                error_message=f"Embedding service error: {str(e)}",
                retryable=True
            )
        
        # STEP 3: Store vectors (ChromaDB or pgvector)
        try:
            vector_ids = store_vectors(vectors, metadata)
        except ConnectionError:
            return IngestionResponse(
                status="error",
                error_type="database_connection_lost",
                error_message="Cannot reach vector database",
                retryable=True,
                next_retry_at=datetime.utcnow() + timedelta(seconds=30)
            )
        except DiskSpaceLimitError:
            return IngestionResponse(
                status="error",
                error_type="disk_space_full",
                error_message="Vector database disk is full",
                retryable=False  # Admin cleanup needed
            )
        except StorageError as e:
            return IngestionResponse(
                status="error",
                error_type="storage_failed",
                error_message=f"Failed to store vectors: {str(e)}",
                retryable=True
            )
        
        # SUCCESS
        duration = time.time() - start_time
        return IngestionResponse(
            status="success",
            document_id=metadata.get("document_id"),
            chunks_processed=len(chunks),
            vectors_stored=len(vector_ids),
            duration_seconds=duration
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error ingesting {file_path}")
        return IngestionResponse(
            status="error",
            error_type="internal_error",
            error_message="Unexpected server error",
            retryable=True
        )
```

---

## RETRY LOGIC WITH EXPONENTIAL BACKOFF

All retryable errors use exponential backoff:

```python
async def retry_with_backoff(
    operation,
    max_retries=3,
    base_delay=1,
    max_delay=300
):
    """
    Retry operation with exponential backoff.
    
    Delays: 1s, 2s, 4s, 8s, 16s, ... (capped at 300s)
    Plus random jitter: ±10%
    """
    
    for attempt in range(1, max_retries + 1):
        try:
            return await operation()
        
        except Exception as e:
            result = parse_error(e)
            
            if not result.retryable or attempt == max_retries:
                raise  # Don't retry non-retryable errors
            
            # Calculate backoff
            delay = min(
                base_delay * (2 ** (attempt - 1)),
                max_delay
            )
            # Add jitter: ±10%
            jitter = delay * 0.1 * (random.random() - 0.5)
            actual_delay = delay + jitter
            
            logger.warning(
                f"Attempt {attempt} failed: {result.error_type}. "
                f"Retrying in {actual_delay:.1f}s..."
            )
            
            await asyncio.sleep(actual_delay)
    
    raise Exception(f"Failed after {max_retries} retries")
```

---

## USER FEEDBACK VIA WEBSOCKET

When sync completes, send notification to frontend:

```python
async def send_sync_notification(websocket: WebSocket, response: SyncResponse):
    """Send sync result notification to connected client."""
    
    notification = {
        "event": "sync_complete",
        "timestamp": datetime.utcnow().isoformat(),
        "source": response.source,
        "status": response.status,
        "document_id": response.document_id,
        "title": response.title,
        
        # Success data
        "chunks_processed": response.chunks_processed if response.status == "success" else 0,
        "vectors_stored": response.vectors_stored if response.status == "success" else 0,
        
        # Error data
        "error_type": response.error_type if response.status == "error" else None,
        "error_message": response.error_message if response.status == "error" else None,
        "retryable": response.retryable if response.status == "error" else None,
        "next_retry_at": response.next_retry_at.isoformat() if response.next_retry_at else None,
        
        # Metadata
        "duration_seconds": response.duration_seconds,
        "retry_count": response.retry_count
    }
    
    try:
        await websocket.send_json(notification)
    except RuntimeError:
        logger.warning("WebSocket closed, cannot send sync notification")
```

Frontend displays:

```vue
<template>
  <div class="sync-notification" :class="status">
    <span v-if="status === 'success'">✅ {{ title }} synced ({{ duration }}s)</span>
    <span v-else-if="status === 'error'">
      ❌ {{ title }}: {{ error_message }}
      <button v-if="retryable" @click="retry">🔄 Retry</button>
    </span>
  </div>
</template>
```

---

## TESTING STRATEGY

For each error type, test:

1. **Network Errors**
   - Mock `requests.exceptions.Timeout`
   - Verify retryable=true, exponential backoff works
   - Test max_retries limit

2. **Auth Errors**
   - Mock HTTP 401
   - Verify retryable=false
   - No infinite retry loop

3. **Rate Limiting**
   - Mock HTTP 429
   - Verify Retry-After header respected
   - Verify backoff calculation

4. **Data Errors**
   - Mock HTTP 404
   - Verify graceful skip (not crash)

5. **System Errors**
   - Mock database connection loss
   - Verify recovery after reconnect

6. **WebSocket Feedback**
   - Verify frontend receives notifications
   - Test with closed socket
   - Test concurrent syncs

---

## IMPLEMENTATION TIMELINE

- **Phase 1:** Error classification + Response types (4 hours)
- **Phase 2:** Confluence/ADO error handling (6 hours)
- **Phase 3:** Retry logic + backoff (4 hours)
- **Phase 4:** WebSocket notifications (4 hours)
- **Phase 5:** Web search + RAG ingestion (4 hours)
- **Phase 6:** Testing + monitoring (4 hours)

**Total: 26 hours (3-4 days)**

---

**Next Steps:**
1. Implement error types enum
2. Add SyncResponse dataclass
3. Update sync_confluence_page() with error handling
4. Update sync_ado_workitem() with error handling
5. Add WebSocket notification sending
6. Create frontend SyncStatus component
7. Add comprehensive tests

