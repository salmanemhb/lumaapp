# n8n Integration Setup for Luma

## Option 1: n8n Cloud (Easiest - Recommended for MVP)
**Cost:** Free tier: 5,000 workflow executions/month
**URL:** https://n8n.cloud
**Setup Time:** 10 minutes

### Steps:
1. Sign up at n8n.cloud
2. Create new workflow
3. Get webhook URL (will look like: `https://your-instance.n8n.cloud/webhook/...`)
4. Configure Supabase to trigger this webhook on file upload

## Option 2: Self-Hosted n8n (Docker)
**Cost:** Free (but you pay for hosting - $5-10/month on Render/Railway)
**Control:** Full control over data and workflows

### Docker Compose Setup:
```yaml
# docker-compose.yml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_HOST=${N8N_HOST}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - NODE_ENV=production
      - WEBHOOK_URL=https://your-n8n-instance.com/
      - GENERIC_TIMEZONE=Europe/Madrid
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
```

### Deploy to Render:
1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: luma-n8n
    runtime: docker
    dockerfilePath: ./Dockerfile.n8n
    envVars:
      - key: N8N_PASSWORD
        generateValue: true
      - key: N8N_HOST
        value: luma-n8n.onrender.com
```

2. Create `Dockerfile.n8n`:
```dockerfile
FROM n8nio/n8n:latest
EXPOSE 5678
CMD ["n8n", "start"]
```

---

## Phase 2: Create Workflow in n8n

### Workflow Nodes Configuration:

#### 1. Webhook Trigger Node
```json
{
  "type": "webhook",
  "path": "luma-upload",
  "httpMethod": "POST",
  "responseMode": "onReceived",
  "authentication": "headerAuth",
  "authHeaderName": "X-N8N-Secret"
}
```

#### 2. Agent 1: Data Extraction Node
```json
{
  "type": "httpRequest",
  "method": "POST",
  "url": "https://luma-final.onrender.com/api/agents/extract",
  "body": {
    "upload_id": "={{$json.upload_id}}"
  },
  "authentication": "headerAuth"
}
```

#### 3. Decision Node: Check Confidence
```json
{
  "type": "if",
  "conditions": {
    "string": [
      {
        "value1": "={{$json.confidence_score}}",
        "operation": "smaller",
        "value2": "0.7"
      }
    ]
  }
}
```

#### 4. Agent 6: Flag for Review (if low confidence)
```json
{
  "type": "httpRequest",
  "method": "POST",
  "url": "https://luma-final.onrender.com/api/agents/flag-review",
  "body": {
    "upload_id": "={{$json.upload_id}}",
    "reason": "Low confidence score: {{$json.confidence_score}}"
  }
}
```

#### 5. Agent 2: Calculate Emissions (if high confidence)
```json
{
  "type": "httpRequest",
  "method": "POST",
  "url": "https://luma-final.onrender.com/api/agents/calculate",
  "body": {
    "upload_id": "={{$json.upload_id}}"
  }
}
```

#### 6. Agent 8: Send Notification
```json
{
  "type": "emailSend",
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587
  },
  "fromEmail": "noreply@getluma.es",
  "toEmail": "={{$json.user_email}}",
  "subject": "Invoice Processed - {{$json.filename}}",
  "html": "<h2>Processing Complete</h2><p>File: {{$json.filename}}</p><p>Emissions: {{$json.co2e_kg}} kg CO₂e</p>"
}
```

---

## Phase 3: Backend Changes

### 3.1 Add Webhook Secret to Config
```python
# backend/app/config.py
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET")
```

### 3.2 Modify Upload Endpoint
Instead of processing immediately, trigger n8n:

```python
# backend/app/routes/files.py
import httpx

@router.post("/upload")
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    # 1. Store file in Supabase Storage
    file_url = await store_file_in_supabase(file)
    
    # 2. Create upload record with status='pending'
    upload_record = await db.insert_upload({
        "filename": file.filename,
        "file_url": file_url,
        "status": "pending",  # Changed from immediate processing
        "company_id": current_user.company_id
    })
    
    # 3. Trigger n8n workflow (non-blocking)
    background_tasks.add_task(trigger_n8n_workflow, upload_record.id)
    
    # 4. Return immediately
    return {
        "message": "File uploaded successfully. Processing in background.",
        "upload_id": upload_record.id,
        "status": "pending"
    }

async def trigger_n8n_workflow(upload_id: str):
    """Trigger n8n workflow asynchronously"""
    async with httpx.AsyncClient() as client:
        await client.post(
            settings.N8N_WEBHOOK_URL,
            json={"upload_id": upload_id},
            headers={"X-N8N-Secret": settings.N8N_WEBHOOK_SECRET}
        )
```

### 3.3 Add Agent Endpoints
Create endpoints that n8n will call:

```python
# backend/app/routes/agents.py
@router.post("/agents/extract")
async def agent_extract(data: dict):
    """Agent 1: Extract data from upload"""
    upload_id = data["upload_id"]
    agent = DataIntakeAgent()
    result = await agent.process_upload(upload_id)
    return result

@router.post("/agents/calculate")
async def agent_calculate(data: dict):
    """Agent 2: Calculate emissions"""
    upload_id = data["upload_id"]
    # Fetch extracted data
    upload = await db.get_upload(upload_id)
    # Calculate emissions
    emissions = calculate_emissions(upload)
    # Update database
    await db.update_upload(upload_id, {"co2e_kg": emissions, "status": "processed"})
    return {"co2e_kg": emissions}

@router.post("/agents/flag-review")
async def agent_flag_review(data: dict):
    """Agent 6: Flag for manual review"""
    upload_id = data["upload_id"]
    reason = data.get("reason", "Low confidence")
    await db.update_upload(upload_id, {
        "status": "review_needed",
        "review_reason": reason
    })
    return {"status": "flagged"}
```

---

## Phase 4: Frontend Changes

### 4.1 Add Polling for Status Updates
Since processing is async, frontend needs to check status:

```typescript
// src/pages/Dashboard.tsx
useEffect(() => {
  const interval = setInterval(async () => {
    // Check for uploads with status='pending' or 'processing'
    const pendingUploads = uploads.filter(u => 
      u.status === 'pending' || u.status === 'processing'
    );
    
    if (pendingUploads.length > 0) {
      // Fetch updated data
      const response = await fetch(`${API_URL}/api/files/uploads`);
      const data = await response.json();
      setUploads(data);
    }
  }, 5000); // Poll every 5 seconds
  
  return () => clearInterval(interval);
}, [uploads]);
```

### 4.2 Add Real-time Updates (WebSocket - Optional)
For instant updates without polling:

```python
# backend/app/websocket.py
from fastapi import WebSocket

@app.websocket("/ws/{company_id}")
async def websocket_endpoint(websocket: WebSocket, company_id: str):
    await websocket.accept()
    # When n8n completes, broadcast to all connected clients
    await websocket.send_json({
        "type": "upload_complete",
        "upload_id": upload_id,
        "status": "processed"
    })
```

---

## Phase 5: Supabase Database Trigger (Alternative to n8n Webhook)

If you want Supabase to directly trigger n8n on insert:

```sql
-- Create function to call n8n webhook
CREATE OR REPLACE FUNCTION notify_n8n_on_upload()
RETURNS TRIGGER AS $$
DECLARE
  webhook_url TEXT := 'https://your-instance.n8n.cloud/webhook/luma-upload';
BEGIN
  PERFORM net.http_post(
    url := webhook_url,
    headers := jsonb_build_object('Content-Type', 'application/json'),
    body := jsonb_build_object(
      'upload_id', NEW.id,
      'filename', NEW.filename,
      'company_id', NEW.company_id
    )
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER upload_created
AFTER INSERT ON upload
FOR EACH ROW
EXECUTE FUNCTION notify_n8n_on_upload();
```

---

## Timeline & Milestones

### Week 1: Setup & Infrastructure
- [ ] Sign up for n8n Cloud OR deploy self-hosted
- [ ] Create basic workflow with webhook trigger
- [ ] Test webhook connectivity

### Week 2: Agent Endpoints
- [ ] Create `/api/agents/extract` endpoint
- [ ] Create `/api/agents/calculate` endpoint
- [ ] Create `/api/agents/flag-review` endpoint
- [ ] Test each endpoint individually

### Week 3: Integration
- [ ] Modify upload endpoint to trigger n8n
- [ ] Add status polling to frontend
- [ ] Test end-to-end flow
- [ ] Add error handling & retries

### Week 4: Advanced Features
- [ ] Add Agent 8 email notifications
- [ ] Add Agent 7 analytics
- [ ] Add WebSocket for real-time updates
- [ ] Performance optimization

---

## Cost Breakdown

| Service | Current | With n8n |
|---------|---------|----------|
| Backend (Render) | $7/month | $7/month |
| Frontend (Netlify) | Free | Free |
| Supabase | Free tier | Free tier |
| **n8n Cloud** | **-** | **Free (5k exec/mo)** |
| Total | $7/month | $7/month |

**If self-hosting n8n:**
| Total | $7/month | $14/month |

---

## Benefits of n8n Integration

✅ **Instant Response:** User doesn't wait for processing  
✅ **Better Error Handling:** Automatic retries on failures  
✅ **Visibility:** See processing status in real-time  
✅ **Scalability:** Handle 1000 uploads without blocking  
✅ **Flexibility:** Easy to add new agents/steps  
✅ **Monitoring:** Built-in execution logs  
✅ **No Code Changes:** Modify workflow without redeploying  

---

## Migration Strategy

### Option A: Gradual Migration (Recommended)
1. Keep current synchronous flow as default
2. Add n8n as optional flag: `?use_n8n=true`
3. Test with subset of users
4. Gradually increase percentage
5. Full cutover when stable

### Option B: Immediate Migration
1. Deploy n8n
2. Switch all uploads to async flow
3. Monitor closely for 48 hours
4. Rollback plan ready

---

## Testing Checklist

Before going live:
- [ ] Upload PDF → Check n8n execution log
- [ ] Upload CSV with 100 rows → Verify all processed
- [ ] Upload with bad data → Verify retry logic
- [ ] Simulate n8n downtime → Verify graceful degradation
- [ ] Load test: 50 simultaneous uploads
- [ ] Check email notifications work
- [ ] Verify analytics updates correctly

