# V.I.S.I.O.N. Logging — Quick Reference

## Backend Logging (Python)

```python
import logging
logger = logging.getLogger("MyService")

# Different levels
logger.debug("Development details")           # Only in dev logs
logger.info("User logged in")                # Always recorded
logger.warning("High memory usage")          # Noted but not error
logger.error("Request failed", exc_info=True) # With stack trace
```

**Files:**
- `logs/app.log` — All application logs
- `logs/app.log.1` — Previous day (automatic rotation)

**View logs:**
```bash
tail -f logs/app.log           # Real-time
grep "ERROR" logs/app.log      # Filter
```

---

## Frontend Logging (TypeScript/Vue)

```typescript
import { createLogger } from '@/utils/logger'
const log = createLogger('MyComponent')

// Different levels
log.debug('User clicked button', { action: 'submit' })
log.info('Form submitted successfully')
log.warn('Network slow', { latency: 500 })
log.error(error, new Error('Submit failed'), { formData })
```

**Access logs in DevTools Console:**
```javascript
// View all logs
globalLogger.getLogs()

// Download logs
globalLogger.downloadLogs('json')  // Save as JSON
globalLogger.downloadLogs('csv')   // Save as CSV

// Clear logs
globalLogger.clear()
```

---

## Log Levels

| Level | Backend | Frontend | Remote? | When to Use |
|-------|---------|----------|---------|-------------|
| DEBUG | ✅ | ✅ | ❌ | Dev details, variable values |
| INFO | ✅ | ✅ | ❌ | Important events, state changes |
| WARN | ✅ | ✅ | ❌ | Unexpected but handled situations |
| ERROR | ✅ | ✅ | ✅ | Failures, exceptions, bugs |

---

## Security Rules

⚠️ **NEVER log:**
- Passwords
- API keys / tokens
- Personal data (PII)
- Credit card numbers
- Internal IP addresses

✅ **DO log:**
- Function entry/exit
- Important state changes
- Error messages
- User actions (not data)
- Performance metrics

**Example:**
```python
# ❌ BAD
logger.info(f"User login: {username}:{password}")

# ✅ GOOD
logger.info(f"User login attempt", extra={
    "username": username,
    "success": True
})
```

---

## Common Patterns

### On Error
```python
try:
    process_request()
except Exception as e:
    logger.error("Request processing failed", exc_info=True)
    raise
```

### With Context
```python
logger.info("Processing message", extra={
    "session_id": session_id,
    "message_length": len(msg),
    "user_role": user.role
})
```

### Performance Tracking
```python
import time
start = time.time()
result = expensive_operation()
duration = time.time() - start
logger.info("Operation completed", extra={
    "operation": "expensive_operation",
    "duration_ms": duration * 1000
})
```

---

## Endpoints

### Frontend → Backend

**Single log:**
```bash
POST http://localhost:8000/api/logs
{
  "timestamp": "2026-10-21T12:34:56Z",
  "level": "ERROR",
  "module": "ChatInput",
  "message": "Request failed",
  "data": { "status": 500 }
}
```

**Batch logs:**
```bash
POST http://localhost:8000/api/logs/batch
{
  "logs": [
    { "level": "INFO", "module": "HomeView", "message": "Mounted" },
    { "level": "ERROR", "module": "WebSocket", "message": "Disconnected" }
  ]
}
```

**Health check:**
```bash
GET http://localhost:8000/api/logs/health
```

---

## Debugging Tips

### Find logs by module
```javascript
const logs = globalLogger.getLogs()
logs.filter(l => l.module === 'ChatInput')
```

### Find all errors
```javascript
logs.filter(l => l.level === 'ERROR')
```

### Find by time range
```javascript
const start = new Date('2026-10-21T12:00:00').getTime()
const end = new Date('2026-10-21T13:00:00').getTime()
logs.filter(l => {
  const time = new Date(l.timestamp).getTime()
  return time >= start && time <= end
})
```

### Export for sharing
```javascript
// Download JSON
globalLogger.downloadLogs('json')

// Or copy to clipboard
copy(globalLogger.exportLogs())
```

---

## Configuration

**Backend:** `backend/app/core/logging_config.py`
- Cloud Run auto-detected → JSON logs
- Local dev → text logs + file
- Log level, format, file paths

**Frontend:** `frontend/src/utils/logger.ts`
- Max 500 logs in sessionStorage
- Enable/disable remote logging per logger
- Custom log level filtering

---

## Full Documentation

See `docs/19-LoggingGuide.md` for complete guide.
