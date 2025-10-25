# Architecture Comparison: Current vs. n8n Integration

## Current Architecture (As-Is)

```
┌─────────────┐
│   Browser   │
│  (React)    │
└──────┬──────┘
       │ 1. POST /api/files/upload (file + metadata)
       ↓
┌─────────────────────────────────────────────┐
│         FastAPI Backend (Render)            │
│  ┌──────────────────────────────────────┐  │
│  │  files.py: upload_file()             │  │
│  │                                      │  │
│  │  1. Validate file                   │  │
│  │  2. Save to temp storage            │  │
│  │  3. DocumentParser.parse_document() │◄─── BLOCKING: Takes 5-30s
│  │  4. Calculate emissions             │  │
│  │  5. Store in Supabase               │  │
│  │  6. Return results                  │  │
│  └──────────────────────────────────────┘  │
└─────────────┬───────────────────────────────┘
              │ 7. Response after 5-30 seconds
              ↓
┌─────────────────────┐
│  Supabase Database  │
│  - upload table     │
│  - Storage bucket   │
└─────────────────────┘

⏱️  Timeline: User waits 5-30 seconds for response
🔄  Concurrency: 1 request blocks 1 thread
💾  State: Everything in one transaction
🚫  Failure: If parser crashes, upload fails completely
```

### Current Flow Step-by-Step:
1. **User uploads** → Frontend sends FormData
2. **Backend receives** → `upload_file()` function starts
3. **File saved** → Temporarily to `/tmp/`
4. **Parser runs** → `DocumentParser.parse_document()` (5-30s)
5. **Emissions calculated** → Apply factors from config
6. **Database insert** → One Upload record created
7. **Response sent** → User sees results immediately
8. **Frontend refreshes** → Dashboard shows new data

---

## n8n Architecture (Target)

```
┌─────────────┐
│   Browser   │
│  (React)    │
└──────┬──────┘
       │ 1. POST /api/files/upload (file + metadata)
       ↓
┌─────────────────────────────────────────────────────────┐
│         FastAPI Backend (Render)                        │
│  ┌──────────────────────────────────────────┐          │
│  │  files.py: upload_file()  [MODIFIED]     │          │
│  │                                          │          │
│  │  1. Validate file                       │          │
│  │  2. Upload to Supabase Storage          │          │
│  │  3. Create DB record (status='pending') │          │
│  │  4. Trigger n8n webhook (async)         │◄──── NON-BLOCKING
│  │  5. Return immediately                  │          │
│  └──────────────────────────────────────────┘          │
│                                                         │
│  ┌────────── New Agent Endpoints ──────────┐          │
│  │  /api/agents/extract                     │          │
│  │  /api/agents/calculate                   │          │
│  │  /api/agents/flag-review                 │          │
│  └──────────────────────────────────────────┘          │
└──────────┬──────────────────────────────────────────────┘
           │ 6. Response in <1 second
           ↓
┌─────────────────────┐         ┌──────────────────────────────┐
│  Supabase Database  │         │         n8n Cloud            │
│  - upload (pending) │         │  ┌────────────────────────┐  │
│  - Storage bucket   │◄────────┤  │  Workflow Execution    │  │
└─────────────────────┘         │  │                        │  │
           ↑                    │  │ 1. Agent 1: Extract    │──┼─┐
           │                    │  │    ↓                   │  │ │
           │                    │  │ 2. Check confidence    │  │ │
           │                    │  │    ↓                   │  │ │
           │                    │  │ 3. Agent 2: Calculate  │  │ │ Calls backend
           │                    │  │    ↓                   │  │ │ endpoints
           │                    │  │ 4. Agent 8: Notify     │  │ │
           │                    │  └────────────────────────┘  │ │
           │                    └──────────────────────────────┘ │
           │                                                     │
           └─────────────────────────────────────────────────────┘
                        Updates DB with results

⏱️  Timeline: User waits <1 second, processing happens in background
🔄  Concurrency: Unlimited parallel processing
💾  State: Tracked through status field (pending→extracted→processed)
✅  Failure: Automatic retries, graceful degradation
```

### n8n Flow Step-by-Step:
1. **User uploads** → Frontend sends FormData
2. **Backend receives** → `upload_file()` function starts
3. **File uploaded** → Directly to Supabase Storage (permanent)
4. **Database insert** → Upload record with `status='pending'`
5. **n8n triggered** → Background task calls webhook
6. **Response sent immediately** → User sees "Processing..." (1 second)
7. **Frontend polls** → Checks status every 5 seconds
8. **n8n processes** (in parallel, may take 30s):
   - Agent 1: Downloads file, extracts data
   - Agent 2: Calculates emissions
   - Agent 8: Sends email notification
9. **Database updates** → Status changes to `processed`
10. **Frontend refreshes** → Shows completed data
11. **User receives email** → "Your invoice is processed"

---

## Files Modified

### ✅ Already Modified (No Breaking Changes):
- **`backend/app/config.py`** - Added n8n settings (optional, empty by default)
- **`backend/main.py`** - Added agents router (new endpoints, doesn't affect existing)

### 🔧 Will Need Modification:
- **`backend/app/routes/files.py`** - `upload_file()` function
  - Current: Synchronous processing
  - Future: Optional async trigger

### 📁 New Files (No conflicts):
- **`backend/app/routes/agents.py`** - New agent endpoints
- **`n8n-workflow-template.json`** - Workflow configuration
- **`n8n-setup.md`** & **`QUICKSTART-N8N.md`** - Documentation

---

## Database Schema Changes

### Current Schema:
```sql
CREATE TABLE upload (
    id UUID PRIMARY KEY,
    filename TEXT,
    supplier TEXT,
    category TEXT,
    usage_value FLOAT,
    co2e_kg FLOAT,
    confidence FLOAT,
    status TEXT,  -- Already exists! ('processing', 'processed', 'failed')
    uploaded_at TIMESTAMP,
    ...
);
```

### With n8n (No schema changes needed!):
Same schema, just new status values used:
- `'pending'` - Uploaded, waiting for extraction
- `'extracted'` - Agent 1 completed
- `'processed'` - Agent 2 completed (existing)
- `'review_needed'` - Low confidence, needs human review
- `'failed'` - Processing failed (existing)

**No migration needed** - existing status field handles everything!

---

## API Endpoints Impact

### Existing Endpoints (No Changes):
```
✅ POST   /api/files/upload        - Still works (will be enhanced)
✅ GET    /api/files/uploads        - Still works
✅ GET    /api/files/uploads/:id    - Still works
✅ DELETE /api/files/uploads/:id    - Still works
✅ DELETE /api/files/uploads/clear  - Still works
✅ POST   /api/auth/register        - Unaffected
✅ POST   /api/auth/login           - Unaffected
✅ GET    /api/dashboard/stats      - Unaffected
```

### New Endpoints (Added, not replacing):
```
🆕 POST   /api/agents/extract       - For n8n to call
🆕 POST   /api/agents/calculate     - For n8n to call
🆕 POST   /api/agents/flag-review   - For n8n to call
```

---

## Frontend Impact

### Current Frontend:
```tsx
// UploadArea.tsx - Current
const handleUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/files/upload', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  // Data immediately available with co2e_kg, supplier, etc.
  toast.success(`Processed! ${data.co2e_kg} kg CO₂e`);
};
```

### With n8n (Backwards compatible):
```tsx
// UploadArea.tsx - Enhanced
const handleUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/files/upload', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  
  if (data.status === 'pending') {
    // NEW: Async processing
    toast.info('Processing in background...');
    // Poll for status updates (already implemented in Dashboard.tsx!)
  } else {
    // OLD: Synchronous processing (still works)
    toast.success(`Processed! ${data.co2e_kg} kg CO₂e`);
  }
};
```

**Key Point:** Frontend already has status polling logic in Dashboard.tsx, so it will automatically work with async processing!

---

## Deployment Impact

### Current Deployment:
```
1. Push to GitHub
2. Render auto-deploys backend (3-5 min)
3. Netlify auto-deploys frontend (1-2 min)
4. Done
```

### With n8n:
```
1. Push to GitHub
2. Render auto-deploys backend (3-5 min)
3. Netlify auto-deploys frontend (1-2 min)
4. n8n workflow already running (no deploy needed)
5. Done
```

**n8n changes don't require redeployment** - you modify workflows in the n8n UI!

---

## Migration Strategy (Zero Downtime)

### Phase 1: Setup (No user impact)
```
✅ Deploy agent endpoints (already done)
✅ Set up n8n instance
✅ Configure webhook URL
⏱️  Current flow still active
```

### Phase 2: Testing (Opt-in)
```python
# Modified upload endpoint
@router.post("/upload")
async def upload_file(file: UploadFile, use_n8n: bool = False):
    if use_n8n:
        # NEW: Async processing via n8n
        return trigger_n8n_workflow()
    else:
        # OLD: Synchronous processing (default)
        return process_synchronously()
```
**Users:** See no change (use_n8n=False by default)
**You:** Test with `?use_n8n=true` query parameter

### Phase 3: Gradual Rollout
```python
# Roll out to 10% of users
import random

@router.post("/upload")
async def upload_file(file: UploadFile):
    if random.random() < 0.10:  # 10% of uploads
        return trigger_n8n_workflow()
    else:
        return process_synchronously()
```

### Phase 4: Full Migration
```python
# All users use n8n
@router.post("/upload")
async def upload_file(file: UploadFile):
    return trigger_n8n_workflow()
    # Old code removed
```

---

## Risk Analysis

### Low Risk Changes:
✅ **Adding agent endpoints** - New routes, don't affect existing  
✅ **Adding n8n config** - Optional variables, empty by default  
✅ **Router registration** - Just adds new routes  
✅ **Documentation** - No code impact  

### Medium Risk Changes:
⚠️  **Modifying upload endpoint** - Changes core functionality  
⚠️  **Frontend polling** - Could increase API calls  
⚠️  **Status field usage** - New values, need to handle in UI  

### Mitigation:
- **Feature flag** - Keep old flow as fallback
- **Gradual rollout** - Test with subset of users
- **Monitoring** - Track error rates during migration
- **Rollback plan** - Can revert to synchronous in 5 minutes

---

## Performance Comparison

### Current System:
```
Scenario: 10 users upload simultaneously

User 1: Upload → Wait 5s  → ✅ Done (5s)
User 2: Upload → Wait 10s → ✅ Done (10s)  [waited for user 1]
User 3: Upload → Wait 15s → ✅ Done (15s)  [waited for users 1,2]
...
User 10: Upload → Wait 50s → ✅ Done (50s) [waited for 9 users]

Average wait: 27.5 seconds
Worst case: 50 seconds
```

### With n8n:
```
Scenario: 10 users upload simultaneously

User 1: Upload → ✅ Response (0.5s) → [Background processing]
User 2: Upload → ✅ Response (0.5s) → [Background processing]
User 3: Upload → ✅ Response (0.5s) → [Background processing]
...
User 10: Upload → ✅ Response (0.5s) → [Background processing]

[All processing happens in parallel via n8n]

Average wait: 0.5 seconds
Worst case: 0.5 seconds
All get email notification when done (5-30s later)
```

---

## What Stays The Same

✅ **Authentication** - No changes to JWT, login, registration  
✅ **Database schema** - No migrations needed  
✅ **File storage** - Still using Supabase Storage  
✅ **Emission calculations** - Same factors, same logic  
✅ **Dashboard UI** - Shows same data, same format  
✅ **Existing uploads** - Old data unaffected  
✅ **Document parsing** - Same DocumentParser class  
✅ **Testing files** - Same test CSVs, PDFs work  

---

## What Changes

🔄 **Upload response time** - From 5-30s to <1s  
🔄 **Processing model** - From synchronous to asynchronous  
🔄 **Error handling** - From fail-fast to retry with fallback  
🔄 **Notifications** - New email when processing complete  
🔄 **Monitoring** - Can see workflow status in n8n dashboard  
🔄 **Scalability** - From 1 request/time to unlimited parallel  

---

## Rollback Plan (If Needed)

If n8n integration causes issues:

### Step 1: Immediate Rollback (5 minutes)
```python
# In files.py, comment out n8n trigger
# @router.post("/upload")
# async def upload_file(...):
#     # return trigger_n8n_workflow()  # DISABLED
#     return process_synchronously()  # ENABLED
```
Push to git → Render auto-deploys → Back to old flow

### Step 2: Remove n8n components (Optional)
```bash
# Remove agent endpoints
git rm backend/app/routes/agents.py

# Remove from main.py
# Remove: app.include_router(agents.router)

# Remove env vars from Render
# Delete: N8N_WEBHOOK_URL, N8N_WEBHOOK_SECRET
```

---

## Summary

### Breaking Changes: **NONE** ✅
- All existing functionality preserved
- New features additive, not replacing
- Can run both flows simultaneously during migration

### Database Changes: **NONE** ✅
- Uses existing status field
- No migrations required
- Backwards compatible

### Frontend Changes: **MINIMAL** ✅
- Already has polling logic
- Already handles status field
- Will work automatically with async flow

### Risk Level: **LOW** ✅
- Feature flag for gradual rollout
- Rollback in 5 minutes if needed
- Old flow kept as fallback

### Benefits:
- 📈 **50x faster** response time (27.5s → 0.5s)
- 🔄 **Unlimited** concurrent uploads
- ✉️ **Email** notifications
- 🔁 **Auto-retry** on failures
- 📊 **Monitoring** dashboard

### Recommendation:
**Proceed with Phase 1 (Setup)** - Zero risk, zero user impact, enables future async processing when ready.
