# MEDIUM Priority Issues - Action Plan

**Date:** October 21, 2026  
**Focus:** Code quality improvements (non-blocking, iterative)

---

## 📊 MEDIUM Priority Backlog Summary

| Category | Count | Impact | Effort | Status |
|----------|-------|--------|--------|--------|
| Null/Undefined checks | 271+ | High | 2-3 weeks | ⏳ Pending |
| SQL query syntax cleanup | 11 | Low | 2-3 hours | ⏳ Nice-to-have |
| Rate limiting | 5 | Medium | 0 hours | ✅ Done |
| Encryption at rest | - | Medium | 4-6 hours | ⏳ Enterprise |

---

## 1️⃣ Null/Undefined Checks (HIGH Impact, Iterative)

### Current State
- 271+ potential null/undefined accesses found
- Pattern: `.value`, `.length`, `.data` accessed without checks
- Risk: Runtime errors in edge cases

### Recommended Approach - INCREMENTAL FIXES

**Phase 1 (This Sprint): Critical paths only**
- [ ] HomeView.vue - Main chat message handling
- [ ] ChatInput.vue - User input validation
- [ ] SystemLog.vue - Message filtering and display
- **Estimated effort:** 3-4 hours

**Phase 2 (Next Sprint): UI Components**
- [ ] All molecules and organisms components
- [ ] Add checks for optional data from API responses
- **Estimated effort:** 1 week

**Phase 3 (Future): Comprehensive coverage**
- [ ] Every component and service
- [ ] Full 271+ instances addressed
- **Estimated effort:** 2-3 weeks (ongoing)

### Example Pattern

```typescript
// ❌ BEFORE - Can throw if data is undefined
const messages = chatLog.value.map(m => m.text)
const length = message.split(' ').length

// ✅ AFTER - Safe handling
const messages = chatLog.value?.map(m => m?.text) ?? []
const length = message?.split(' ')?.length ?? 0

// ✅ EXPLICIT null checks (when nullish coalescing isn't enough)
if (user?.profile?.name) {
  displayName.value = user.profile.name
} else {
  displayName.value = 'Unknown User'
}
```

### Implementation Strategy

1. **Use optional chaining (`?.`)** for property access
2. **Use nullish coalescing (`??`)** for default values
3. **Keep defensive checks** where logic depends on exact falsy value
4. **Add TypeScript strict mode** for future improvements

### Starting Point - Top 5 Files

1. `frontend/src/views/HomeView.vue` - Most critical message handling
2. `frontend/src/components/1-atoms/ChatInput.vue` - User input
3. `frontend/src/components/3-organisms/SystemLog.vue` - Message display
4. `frontend/src/services/ChatService.ts` - API integration
5. `frontend/src/composables/useWebSocket.ts` - WebSocket data

---

## 2️⃣ SQL Query Syntax Cleanup (LOW Impact)

### Current State - VERIFIED SAFE ✅

All 11 instances use **parameterized queries correctly**:
```python
# Already safe - uses parameter tuple
cursor.execute(f"SELECT * FROM table WHERE id = {p}", (value,))
```

### Improvement Opportunity (Nice-to-have)

Cleaner syntax - remove f-string wrapper:
```python
# Current (safe but verbose)
cursor.execute(f"SELECT * FROM table WHERE id = {p}", (value,))

# Better (cleaner, same safety)
cursor.execute("SELECT * FROM table WHERE id = ?", (value,))
```

### Action Plan
- [ ] Low priority - can be addressed in future refactoring
- [ ] Does not block any functionality
- [ ] Pure code cleanliness improvement

---

## 3️⃣ Rate Limiting - STATUS: ✅ COMPLETE

**All endpoints properly rate-limited:**

| Endpoint | Limit | Status |
|----------|-------|--------|
| `/api/sync/confluence/page/{id}` | 20/hour | ✅ Active |
| `/api/sync/confluence/delta` | 5/hour | ✅ Active |
| `/api/sync/ado/workitem/{id}` | 20/hour | ✅ Active |
| `/api/sync/ado/delta` | 5/hour | ✅ Active |
| `/api/upload` | 5 per 60s | ✅ Active |

**No action needed.** ✅

---

## 4️⃣ Encryption at Rest (Enterprise Feature)

### Current State
- No data encryption in database
- Documents stored in plaintext in ChromaDB
- Chat history plaintext in PostgreSQL/SQLite

### Why Later?
- Adds significant complexity
- Must handle key rotation
- Performance impact on RAG search
- Enterprise feature (nice-to-have, not blocking)

### When Needed
- When handling PHI/PII data
- Compliance requirements (GDPR, HIPAA)
- Production deployment with sensitive data

### Implementation (When Needed)
```python
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()

# Usage
encrypted_content = encrypt_field.encrypt(document.content)
# Store encrypted_content in database
```

**Estimated effort when needed:** 4-6 hours

---

## 🎯 Recommended Sprint Plan

### This Week (Quick Wins)
- [ ] Start Phase 1 of null/undefined checks (critical paths)
- [ ] Pick 2-3 files from the starting point list
- [ ] Add optional chaining and nullish coalescing
- **Effort:** 3-4 hours
- **Impact:** Reduces edge-case crashes in main UI

### Next Week (Quality Pass)
- [ ] Complete Phase 1 (all critical files)
- [ ] Begin Phase 2 (component library)
- [ ] Code review and testing
- **Effort:** 1 week
- **Impact:** Production-grade robustness

### Future Sprints
- [ ] Complete Phase 3 (comprehensive coverage)
- [ ] Refactor SQL queries (if needed)
- [ ] Add encryption at rest (if compliance needed)

---

## 📈 Progress Tracking

Use this template to track null/undefined fixes:

```markdown
### HomeView.vue - Null Check Implementation
- [ ] Line 245: Add check for user?.profile?.name
- [ ] Line 312: Add check for message?.split()
- [ ] Line 478: Add check for session?.id
- [ ] Testing: Manual test with missing data
- **Status:** In Progress (2/3 done)
```

---

## 🔍 How to Find Issues

### Quick scan for most critical patterns:

```bash
# Missing null checks on .value
grep -rn "\.value\[" frontend/src/views/

# Missing null checks on API responses
grep -rn "data\." frontend/src/services/

# Missing null checks in loops
grep -rn "\.map(" frontend/src/ | grep -v "?\\."

# Missing null checks on object properties
grep -rn "\.\w\+\.length" frontend/src/
```

---

## ✅ Completion Criteria

- [ ] All critical paths (HomeView, ChatInput, SystemLog) have null checks
- [ ] No unhandled undefined access in main chat flow
- [ ] At least 50% of 271+ instances addressed (incremental is OK)
- [ ] Tests pass with missing/null data
- [ ] Code review complete

---

**Last Updated:** October 21, 2026  
**Status:** Ready to implement  
**Owner:** [Assign to team member]
