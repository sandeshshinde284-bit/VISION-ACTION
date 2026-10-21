# V.I.S.I.O.N. Logging Guide
**Date:** Oct 21, 2026 | **Version:** 1.0 | **Status:** New

Complete guide to logging in V.I.S.I.O.N. frontend and backend.

---

## 1. BACKEND LOGGING

### 1.1 Architecture

V.I.S.I.O.N. uses a unified, production-grade logging system configured in `backend/app/core/logging_config.py`.

**Modes:**
- **Local Development:** Human-readable text logs + file backup
- **Cloud Run (GCP):** Structured JSON logs to stdout for GCP Log Explorer

### 1.2 Log File Locations

```bash
# Local development logs
logs/
  └── app.log  # Daily application log (all levels)
  └── app.log.1  # Rotated backups (up to 5 days)
```

### 1.3 Using Backend Logging

**Import in any Python file:**
```python
import logging
logger = logging.getLogger("ModuleName")

# Log at different levels
logger.debug("Debugging info")
logger.info("Processing message", extra={"user_id": 123})
logger.warning("Unexpected behavior detected")
logger.error("Failed to process request", exc_info=True)  # Includes stack trace
```

**Example from `ai_service.py`:**
```python
logger = logging.getLogger("AIService")

logger.info("Intent classification started", extra={
    "query": query,
    "intent": intent,
    "confidence": 0.95
})
```

### 1.4 Structured Logging (GCP Cloud Run)

When running on Cloud Run, logs are automatically converted to structured JSON:

```json
{
  "severity": "ERROR",
  "message": "Failed to process request",
  "logger": "WebSocketHandler",
  "module": "websockets",
  "line": 42,
  "timestamp": "2026-10-21T12:34:56.123Z",
  "exception": "Traceback (most recent call last)..."
}
```

This format is searchable and filterable in GCP Log Explorer.

### 1.5 Best Practices for Backend Logging

✅ **DO:**
- Log at appropriate levels (DEBUG for dev, INFO for important, ERROR for failures)
- Include context data in `extra` dict: `extra={"session_id": session_id, "user": username}`
- Log exceptions with `exc_info=True`: `logger.error("Request failed", exc_info=True)`
- Use descriptive messages: `"User login successful"` not `"User login"`

❌ **DON'T:**
- Log sensitive data (passwords, tokens, API keys) — EVER
- Use print() for important events — use logger instead
- Over-log (avoid debug spam in production)
- Catch exceptions silently without logging

**Security:** No passwords, tokens, or PII should appear in logs.

---

## 2. FRONTEND LOGGING

### 2.1 Architecture

Frontend logging is implemented in `frontend/src/utils/logger.ts`. Features:

- **Console Logging:** Colored, readable output in browser DevTools
- **In-Memory Storage:** Last 500 logs kept in `sessionStorage` (cleared on tab close)
- **Remote Logging:** ERROR-level logs sent to backend `/api/logs` endpoint
- **Export Capability:** Download logs as JSON or CSV for debugging

### 2.2 Using Frontend Logging

**Import in any Vue or TypeScript file:**
```typescript
import { createLogger } from '@/utils/logger'

const log = createLogger('ChatInput')

// Log at different levels
log.debug('User clicked send button', { message: messageText })
log.info('Message sent successfully', { timestamp: Date.now() })
log.warn('Network latency high', { latency: 500 })
log.error(new Error('WebSocket connection failed'))
```

**Example from `HomeView.vue`:**
```typescript
const log = createLogger('HomeView')

onMounted(() => {
  log.info('Chat interface mounted')
})

const sendMessage = () => {
  try {
    websocket.send(message)
    log.info('Message sent', { length: message.length })
  } catch (error) {
    log.error('Failed to send message', error as Error, {
      message: message,
      websocket_ready: websocket.readyState
    })
  }
}
```

### 2.3 Log Levels

| Level | Color | Usage | Remote? |
|-------|-------|-------|---------|
| **DEBUG** | Gray | Detailed dev info | ❌ No |
| **INFO** | Blue | Important events | ❌ No |
| **WARN** | Orange | Unexpected behavior | ❌ No |
| **ERROR** | Red | Failures, exceptions | ✅ Yes |

### 2.4 Accessing Frontend Logs

**In Browser DevTools:**
```javascript
// View all logs
const { globalLogger } = await import('/src/utils/logger.ts')
globalLogger.getLogs()

// Download logs
globalLogger.downloadLogs('json')  // Download as JSON
globalLogger.downloadLogs('csv')   // Download as CSV

// Clear logs
globalLogger.clear()

// Export as string
const logsJson = globalLogger.exportLogs()
const logsCsv = globalLogger.exportLogsCSV()
```

### 2.5 Automatic Remote Logging

ERROR-level logs are automatically sent to backend's `/api/logs` endpoint:

```typescript
log.error('WebSocket disconnected', error, {
  code: event.code,
  reason: event.reason
})
// This is automatically POSTed to http://localhost:8000/api/logs
```

Backend receives and logs it:
```
[ERROR] [WebSocketService] WebSocket disconnected
```

### 2.6 Best Practices for Frontend Logging

✅ **DO:**
- Create a logger per module: `const log = createLogger('ChatInput')`
- Include relevant data: `log.info('User login', { username, loginMethod })`
- Log errors with full context: `log.error('Request failed', error, { endpoint, method })`
- Use appropriate levels for different importance

❌ **DON'T:**
- Log passwords, tokens, or API keys
- Use `console.log()` for critical events — use logger
- Log too verbosely in development (fills sessionStorage)
- Ignore ERROR logs — they're sent to backend for visibility

**Security:** No PII or sensitive data in logs.

---

## 3. LOGGING API ENDPOINTS

### 3.1 Single Log Endpoint

**POST `/api/logs`** — Ingest a single log entry from frontend

**Request:**
```json
{
  "timestamp": "2026-10-21T12:34:56.123Z",
  "level": "ERROR",
  "module": "ChatInput",
  "message": "Failed to send message",
  "data": {
    "error": "Network timeout",
    "retries": 3
  },
  "stack": "Error: Network timeout\n    at sendMessage (ChatInput.vue:42)..."
}
```

**Response:**
```json
{
  "status": "logged",
  "timestamp": "2026-10-21T12:34:56.123Z",
  "level": "ERROR"
}
```

### 3.2 Batch Logs Endpoint

**POST `/api/logs/batch`** — Ingest multiple log entries

**Request:**
```json
{
  "logs": [
    {
      "timestamp": "2026-10-21T12:34:56Z",
      "level": "INFO",
      "module": "HomeView",
      "message": "Session created"
    },
    {
      "timestamp": "2026-10-21T12:34:57Z",
      "level": "ERROR",
      "module": "WebSocketService",
      "message": "Connection failed",
      "data": { "code": 1006 }
    }
  ]
}
```

**Response:**
```json
{
  "status": "logged",
  "count": 2,
  "timestamp": "2026-10-21T12:34:58Z"
}
```

### 3.3 Health Check Endpoint

**GET `/api/logs/health`** — Check logging system status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-10-21T12:34:56Z",
  "service": "logs"
}
```

---

## 4. LOG ANALYSIS & DEBUGGING

### 4.1 Common Debugging Workflows

**Find all errors in a session:**
```javascript
const logs = globalLogger.getLogs()
const errors = logs.filter(log => log.level === 'ERROR')
console.table(errors)
```

**Find logs from specific module:**
```javascript
const chatLogs = logs.filter(log => log.module === 'ChatInput')
console.table(chatLogs)
```

**Export logs for support:**
```javascript
globalLogger.downloadLogs('json')
// Now send the downloaded file to support team
```

### 4.2 Backend Log Analysis

**View real-time logs (local):**
```bash
cd backend
tail -f ../logs/app.log
```

**Find errors in log file:**
```bash
grep "ERROR" ../logs/app.log
grep "WebSocket" ../logs/app.log | grep "ERROR"
```

**Extract logs for specific session:**
```bash
grep "session-abc123" ../logs/app.log
```

### 4.3 GCP Cloud Run Logs

When deployed to Cloud Run, view logs in GCP Console:

```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 100 \
  --format json
```

Or use GCP Log Explorer:
1. Open [Cloud Console](https://console.cloud.google.com)
2. Go to Logging > Log Explorer
3. Filter by: `resource.type="cloud_run_revision" AND severity="ERROR"`

---

## 5. LOG ROTATION & CLEANUP

### 5.1 Local Log Rotation

Logs rotate automatically when they exceed size limits:
- **app.log:** 10MB max, 5 backups kept (50MB total)
- **Error log:** 5MB max, 3 backups kept (15MB total)

### 5.2 Manual Cleanup

```bash
# Remove logs older than 7 days
find logs -name "*.log" -mtime +7 -delete

# Compress old logs
gzip logs/app.log.1 logs/app.log.2

# See log size
du -sh logs/
```

### 5.3 Remote Log Retention

GCP Cloud Logging retention:
- Default: 30 days
- Premium: Up to 3650 days (10 years) available

---

## 6. TROUBLESHOOTING

### Issue: No logs appearing in file

**Solution:** Ensure `logs/` directory exists and is writable:
```bash
mkdir -p logs
chmod 755 logs
```

### Issue: logs in sessionStorage disappear

**This is normal!** sessionStorage is cleared when the tab closes. To persist:
- Use JSON export for longer-term storage
- Backend captures ERROR logs automatically

### Issue: Remote logging not working

**Check:**
1. Frontend logger has `enableRemote = true`
2. Backend `/api/logs` endpoint is responding: `curl http://localhost:8000/api/logs/health`
3. No network errors in browser console

### Issue: Logs too verbose (spam)

**Solution:** Reduce debug logging in production:
```typescript
// Only enable debug in dev mode
const log = createLogger('MyModule', import.meta.env.DEV)
```

---

## 7. CONFIGURATION

### Backend Logging Config

Edit `backend/app/core/logging_config.py`:

```python
# Change log level
root_logger.setLevel(logging.DEBUG)  # More verbose

# Change log file location
log_dir = "/custom/path/logs"

# Change format
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
```

### Frontend Logging Config

Edit `frontend/src/utils/logger.ts`:

```typescript
// Change max logs in memory
private maxLogs = 1000  // Default: 500

// Disable remote logging for a module
const log = createLogger('ModuleName', false)

// Change remote logging endpoint
const baseUrl = 'https://api.production.com'
```

---

## SUMMARY

**Backend Logging:**
- ✅ Configured in `core/logging_config.py`
- ✅ Stores to `logs/app.log` locally
- ✅ Structured JSON on Cloud Run
- ✅ Use `logger.info()`, `logger.error()`, etc.

**Frontend Logging:**
- ✅ Created in `frontend/src/utils/logger.ts`
- ✅ Stores last 500 logs in sessionStorage
- ✅ ERROR logs sent to backend automatically
- ✅ Downloadable as JSON/CSV
- ✅ Use `createLogger('ModuleName')`

**Best Practices:**
- No sensitive data in logs
- Log with context (extra data)
- Use appropriate log levels
- Monitor ERROR logs regularly
