# 🚀 Quick Start: n8n Integration

## What You Now Have:

✅ **Agent endpoints ready** (`/api/agents/extract`, `/api/agents/calculate`, `/api/agents/flag-review`)  
✅ **Config setup** (N8N_WEBHOOK_URL, N8N_WEBHOOK_SECRET)  
✅ **Workflow template** (n8n-workflow-template.json)  

---

## 3 Steps to Go Live:

### Step 1: Deploy n8n (Choose One)

#### Option A: n8n Cloud (Easiest - 5 minutes)
1. Go to https://n8n.cloud
2. Sign up (free tier: 5,000 workflows/month)
3. Import `n8n-workflow-template.json`:
   - Click "+" → "Import from File"
   - Upload the template
4. Copy webhook URL (looks like: `https://your-instance.n8n.cloud/webhook/luma-upload`)

#### Option B: Self-Hosted Docker (15 minutes)
```bash
# Create docker-compose.yml
docker-compose up -d

# Access at http://localhost:5678
# Create account & import workflow template
```

---

### Step 2: Configure Environment Variables

Add to Render environment variables (or `.env` file):

```bash
N8N_WEBHOOK_URL=https://your-instance.n8n.cloud/webhook/luma-upload
N8N_WEBHOOK_SECRET=your-secret-key-here  # Optional but recommended
```

**How to add on Render:**
1. Go to https://dashboard.render.com
2. Select `luma-final` service
3. Go to "Environment" tab
4. Add variables above
5. Save (will auto-redeploy)

---

### Step 3: Test the Integration

#### Test 1: Call Agent Endpoint Directly
```bash
# Test extraction endpoint
curl -X POST https://luma-final.onrender.com/api/agents/extract \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "YOUR_UPLOAD_ID",
    "company_id": "YOUR_COMPANY_ID"
  }'

# Expected response:
{
  "upload_id": "...",
  "confidence_score": 0.85,
  "supplier": "Iberdrola",
  "category": "electricity",
  "usage_value": 2450.0,
  "usage_unit": "kWh"
}
```

#### Test 2: Trigger n8n Workflow
```bash
# In n8n UI, click "Execute Workflow" button
# Manually input test data:
{
  "upload_id": "test-123",
  "company_id": "company-456"
}

# Watch the workflow execute through each node
```

#### Test 3: End-to-End Upload
Once n8n is configured, you can modify the upload endpoint to trigger n8n automatically.

---

## Current Flow vs. n8n Flow

### **CURRENT (What happens now):**
```
User uploads file → parse_document() runs synchronously → return results
```
**Time:** 5-30 seconds depending on file size

### **WITH n8n (What will happen):**
```
User uploads file → Store in DB with status='pending' → Return immediately
                          ↓
                    (Background processing via n8n)
                          ↓
                    Agent 1: Extract → Agent 2: Calculate → Agent 8: Notify
```
**Time:** User gets response in <1 second, processing happens asynchronously

---

## Migration Options

### Option 1: Parallel Run (Safe - Recommended)
Keep current flow as default, test n8n with specific uploads:

```python
# In files.py upload endpoint
if request.query_params.get("use_n8n") == "true":
    # Trigger n8n workflow
    trigger_n8n_workflow(upload_id, company_id)
    return {"status": "pending", "message": "Processing via n8n"}
else:
    # Current synchronous flow
    parsed_data = DocumentParser.parse_document(file_path)
    # ... existing code
```

### Option 2: Full Cutover
Replace synchronous processing with n8n trigger for all uploads.

---

## Monitoring & Debugging

### Check n8n Execution Logs:
1. Go to n8n dashboard
2. Click "Executions" tab
3. See all workflow runs with status (success/error)
4. Click any execution to see data flow through nodes

### Check Backend Logs:
```bash
# On Render dashboard
# Go to "Logs" tab
# Filter for "agent" keyword
```

### Check Upload Status:
```sql
-- In Supabase SQL editor
SELECT id, filename, status, confidence, co2e_kg
FROM upload
WHERE status IN ('pending', 'extracted', 'processed', 'review_needed')
ORDER BY uploaded_at DESC
LIMIT 20;
```

---

## Troubleshooting

### Issue: "n8n webhook URL not configured"
**Fix:** Add `N8N_WEBHOOK_URL` to Render environment variables

### Issue: Agent endpoint returns 404
**Fix:** 
1. Check backend deployed successfully
2. Test endpoint: `curl https://luma-final.onrender.com/api/agents/extract`
3. Should return 422 (validation error) not 404

### Issue: n8n workflow fails at "Agent 1" node
**Fix:**
1. Check execution log in n8n
2. Look at request/response data
3. Verify upload_id exists in database
4. Check file exists in Supabase storage

### Issue: Emails not sending
**Fix:**
1. In n8n, configure Gmail SMTP credentials
2. Go to node "Agent 8 - Send Notification"
3. Add credentials: Gmail app password
4. Test node individually

---

## Cost & Performance

### Current Setup:
- Uploads: ~5-30 seconds synchronous processing
- Max concurrent: Limited by Render instance (512MB RAM)
- User experience: Must wait for processing

### With n8n (Free tier):
- Uploads: <1 second response
- Max concurrent: 5,000 workflows/month (166/day)
- User experience: Instant feedback + email notification
- Cost: $0 (free tier sufficient for MVP)

### When to Upgrade:
- > 5,000 uploads/month → Upgrade to n8n paid ($20/month)
- OR self-host n8n (~$7/month extra on Render)

---

## Next Steps After Setup:

1. **Add more agents:**
   - Agent 7: Analytics calculation
   - Agent 6 UI: Review queue interface
   - Agent 8: Slack notifications

2. **Add retry logic:**
   - Configure n8n to retry failed extractions
   - Exponential backoff (retry after 1min, 5min, 15min)

3. **Add WebSockets:**
   - Real-time dashboard updates
   - No polling needed

4. **Add workflow monitoring:**
   - Dashboard showing processing queue
   - Alert if > 10 failed workflows

---

## Questions?

Common questions answered in `n8n-setup.md`

**Ready to go?** Start with Step 1 above! 🚀
