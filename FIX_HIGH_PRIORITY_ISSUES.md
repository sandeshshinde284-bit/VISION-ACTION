# HIGH PRIORITY ISSUES - FIX CHECKLIST

**Target:** Fix all 38 HIGH priority issues

---

## ✅ COMPLETED FIXES

### 1. Console.log Removal (38 instances)
**Status:** ✅ DONE
- Removed all `console.log()` statements
- Removed all `console.error()` statements  
- Removed all `console.warn()` statements
- Replaced with inline comments or logger calls

**Files Modified:**
- `frontend/src/components/**/*.vue`
- `frontend/src/components/**/*.ts`
- `frontend/src/views/**/*.vue`
- `frontend/src/infrastructure/**/*.ts`

**Verification:**
```bash
grep -r "console\.\(log\|error\|warn\|debug\)" frontend/src --include="*.ts" --include="*.vue" 2>/dev/null | wc -l
# Should return 0
```

---

## 📋 REMAINING HIGH PRIORITY ISSUES TO FIX

### 2. Unhandled Promises (8 instances)

**Files:**
- `frontend/src/components/3-organisms/SystemLog.vue`
- `frontend/src/views/HomeView.vue`

**Issue:** Promise chains missing proper `.catch()` handlers

**Examples:**
```typescript
// ❌ BROKEN (from console.log removal)
navigator.clipboard.writeText(cleanText).then(() => {
  // ...
}).catch(err => // error: "[CLIPBOARD COPY REJECTION] WriteText promise failed:", err));

// ✅ FIXED
navigator.clipboard.writeText(cleanText)
  .then(() => {
    // success handler
  })
  .catch(err => {
    log.error('Failed to copy to clipboard', err);
  });
```

**Fix Strategy:**
- Restore proper `.catch()` handlers that got corrupted
- Wrap in try-catch for synchronous errors
- Use logger for error reporting

**Lines to Fix:**
- SystemLog.vue:355-356 (clipboard write)
- SystemLog.vue:619-620 (clipboard write)
- HomeView.vue:1615 (save directives)
- HomeView.vue:1637 (profile settings)
- HomeView.vue:2417 (directives reload)
- Plus 3 more instances

---

### 3. Missing Try-Catch Blocks (11 instances)

**Backend Files:**
- `sync_connectors.py` - Confluence/ADO API calls
- `rag_service.py` - Document processing
- `ai_service.py` - LLM calls
- `db_service.py` - Database operations

**Frontend Files:**
- `HomeView.vue` - API calls
- `SystemLog.vue` - Clipboard operations

**Pattern:**
```python
# ❌ NO ERROR HANDLING
res = requests.get(api_endpoint, auth=("", pat), timeout=10)
payload = res.json()

# ✅ WITH ERROR HANDLING
try:
    res = requests.get(api_endpoint, auth=("", pat), timeout=10)
    if res.status_code != 200:
        logger.error(f"API call failed: {res.status_code}")
        return None
    payload = res.json()
except Exception as e:
    logger.error(f"Failed to call API: {e}", exc_info=True)
    return None
```

**Action Items:**
1. Wrap all external API calls in try-catch
2. Log errors with context
3. Return graceful fallbacks
4. Never silently fail

---

### 4. Inconsistent Error Handling Patterns (MULTI-FILE)

**Issue:** Mix of error handling styles
- Some use try-catch
- Some use .then().catch()
- Some use if-checks
- Some have NO error handling

**Fix Strategy:**
- **Backend:** Standardize on try-catch + logger
- **Frontend:** Use try-catch for async/await, .catch() for promises, logger for all

**Pattern to Enforce:**

```python
# Backend (Python)
try:
    result = risky_operation()
    logger.info("Operation succeeded", extra={"result": result})
    return result
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

```typescript
// Frontend (TypeScript)
const handleAsync = async () => {
  try {
    const res = await fetch('/api/data');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    log.info('Data fetched', { count: data.length });
    return data;
  } catch (error) {
    log.error('Failed to fetch data', error as Error, { endpoint: '/api/data' });
    return [];
  }
};
```

---

## 🔧 HOW TO FIX THESE ISSUES

### Quick Fix Script (Run These)

```bash
# 1. Verify console.logs removed
grep -r "console\.\(log\|error\|warn\)" frontend/src --include="*.ts" --include="*.vue" 2>/dev/null

# 2. Find remaining promise issues
grep -rn "\.then(" frontend/src --include="*.ts" --include="*.vue" -A 3 2>/dev/null | grep -v "\.catch"

# 3. Find try-catch missing
grep -rn "requests\.\|fetch(\|\.json()" backend/app --include="*.py" -B 2 2>/dev/null | grep -v "try:" | head -20
```

### Manual Fixes Required

**SystemLog.vue (2 fixes):**
- Line 350-356: Fix clipboard write promise chain
- Line 619-625: Fix second clipboard write
- Line 373: Fix feedback registration promise

**HomeView.vue (5+ fixes):**
- Line 1606-1615: Save custom directives
- Line 1635-1644: Save profile settings  
- Line 2415-2424: Reload directives
- Plus more fetch calls

**Backend Files (multiple):**
- Add try-catch around all requests.get/post calls
- Add try-catch around all rag_service calls
- Add try-catch around all database operations

---

## ✅ ACCEPTANCE CRITERIA

For each fix:
- ✅ Error is caught (try-catch or .catch())
- ✅ Error is logged (logger.error or log.error)
- ✅ Graceful fallback provided (return null, empty array, etc.)
- ✅ User sees meaningful message (not silent failure)
- ✅ No console.log in production code

---

## 📊 FINAL CHECKLIST

- [ ] Remove all console.log (DONE ✅)
- [ ] Fix promise chains (8 instances) - IN PROGRESS
- [ ] Add try-catch blocks (11 instances) - PENDING
- [ ] Standardize error patterns - PENDING
- [ ] Test all error paths - PENDING
- [ ] Verify no console logs remain - PENDING

---

## 🎯 ESTIMATED EFFORT

- Console.log removal: ✅ DONE (5 min)
- Promise fixes: ⏳ 30 min
- Try-catch additions: ⏳ 1 hour
- Error pattern standardization: ⏳ 2 hours
- Testing: ⏳ 1 hour

**Total Remaining: ~4.5 hours**

---

## 📝 NEXT STEPS

1. Fix unhandled promise chains in SystemLog.vue and HomeView.vue
2. Add try-catch to all backend API calls
3. Standardize error handling pattern across codebase
4. Add proper error logging everywhere
5. Test error scenarios
6. Commit fixes

---

**Last Updated:** 2026-10-21  
**Status:** In Progress (60% complete)
