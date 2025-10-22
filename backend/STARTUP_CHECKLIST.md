# 🚀 Luma Backend - Startup Checklist

Use this checklist to get your backend live in under 2 hours!

---

## ☑️ PRE-DEPLOYMENT (45 minutes)

### 1. Supabase Setup (15 min)
- [ ] Go to https://supabase.com
- [ ] Click "New Project"
- [ ] Name: `luma-production`
- [ ] Region: Frankfurt (closest to Spain)
- [ ] Database password: **Save securely!**
- [ ] Wait for project creation (~2 min)

#### Get Credentials
- [ ] Go to **Project Settings** → **API**
- [ ] Copy **Project URL** → Save as `SUPABASE_URL`
- [ ] Copy **anon/public key** → Save as `SUPABASE_KEY`
- [ ] Copy **service_role key** → Save as `SUPABASE_SERVICE_KEY`
- [ ] Go to **Project Settings** → **Database**
- [ ] Copy **Connection string (URI)** → Save as `DATABASE_URL`

#### Create Storage Buckets
- [ ] Go to **Storage** in sidebar
- [ ] Click "New Bucket"
- [ ] Name: `uploads`, Public: ✅, Click "Create"
- [ ] Click "New Bucket" again
- [ ] Name: `reports`, Public: ✅, Click "Create"
- [ ] Verify both buckets appear in list

---

### 2. Resend Setup (5 min)
- [ ] Go to https://resend.com
- [ ] Sign up with email
- [ ] Verify email
- [ ] Go to **API Keys**
- [ ] Click "Create API Key"
- [ ] Name: `luma-production`
- [ ] Copy key → Save as `RESEND_API_KEY`

#### Domain Setup (Optional - for production emails)
- [ ] Go to **Domains**
- [ ] Click "Add Domain"
- [ ] Enter: `getluma.es`
- [ ] Add DNS records to your domain provider
- [ ] Wait for verification

**For testing**: Use `onboarding@resend.dev` as sender (no domain needed)

---

### 3. Google Form Setup (10 min)
- [ ] Go to https://forms.google.com
- [ ] Click "Blank Form"
- [ ] Title: "Luma - Company Verification"
- [ ] Add fields:
  - Company Name (Short answer, Required)
  - Contact Person (Short answer, Required)
  - Email (Short answer, Required)
  - Phone (Short answer)
  - Sector/Industry (Dropdown: Technology, Manufacturing, Retail, Services, Other)
  - Number of Employees (Multiple choice: 1-10, 11-50, 51-200, 201-500, 500+)
  - CSRD Contact Person (Short answer)
  - Additional Notes (Paragraph)
- [ ] Click **Send** → **Link** tab
- [ ] Copy link → Save as `GOOGLE_FORM_URL`
- [ ] Click **Responses** → Enable "Get email notifications"

---

### 4. Generate JWT Secret (2 min)
```bash
# On Mac/Linux
openssl rand -hex 32

# On Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})

# Or online: https://randomkeygen.com/ (copy "CodeIgniter Encryption Keys")
```
- [ ] Copy generated string → Save as `JWT_SECRET`

---

### 5. Prepare Environment Variables (3 min)
Create a text file with all credentials:

```bash
DATABASE_URL=postgresql://postgres.[password]@[host].supabase.co:5432/postgres
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_KEY=[anon-key]
SUPABASE_SERVICE_KEY=[service-role-key]
JWT_SECRET=[your-32-char-secret]
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
RESEND_API_KEY=re_[your-key]
ADMIN_EMAIL=admin@getluma.es
FRONTEND_URL=https://getluma.es
ALLOWED_ORIGINS=https://getluma.es,https://luma-better-main.vercel.app
GOOGLE_FORM_URL=https://forms.google.com/[your-form-id]
ELECTRICITY_FACTOR_KG_PER_KWH=0.231
NATURAL_GAS_FACTOR_KG_PER_KWH=0.202
DIESEL_FACTOR_KG_PER_L=2.680
GASOLINE_FACTOR_KG_PER_L=2.310
ROAD_FREIGHT_FACTOR_KG_PER_TKM=0.062
RAIL_FREIGHT_FACTOR_KG_PER_TKM=0.018
SEA_FREIGHT_FACTOR_KG_PER_TKM=0.010
AIR_FREIGHT_FACTOR_KG_PER_TKM=0.500
NATURAL_GAS_M3_TO_KWH=11.63
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,csv,xlsx,jpg,png
ENVIRONMENT=production
DEBUG=False
```

---

## ☑️ DEPLOYMENT (30 minutes)

### 6. GitHub Setup (5 min)
- [ ] Commit all backend code to GitHub
- [ ] Ensure `backend/` folder contains all files
- [ ] Push to main branch

---

### 7. Render Deployment (15 min)
- [ ] Go to https://render.com
- [ ] Click "New" → "Web Service"
- [ ] Click "Connect to GitHub"
- [ ] Authorize Render to access repository
- [ ] Select your `luma-better-main` repository
- [ ] Configure:

**Basic Settings:**
- Name: `luma-backend`
- Region: Frankfurt (closest to Spain)
- Branch: `main`
- Root Directory: `backend`
- Runtime: `Python 3`

**Build Settings:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Instance Type:**
- Free (for testing) or Starter ($7/mo for production)

- [ ] Click "Advanced" → "Add Environment Variable"
- [ ] Paste ALL environment variables from step 5 (one at a time)
- [ ] Click "Create Web Service"
- [ ] Wait for build to complete (~5 minutes)
- [ ] Copy service URL: `https://luma-backend.onrender.com`

---

### 8. Database Initialization (5 min)
- [ ] In Render dashboard, go to your service
- [ ] Click **Shell** tab (top right)
- [ ] Wait for shell to connect
- [ ] Run:
```bash
python -c "from app.database import init_db; init_db()"
```
- [ ] Verify output: "✅ Database tables created successfully"
- [ ] Close shell

---

### 9. Health Check (2 min)
- [ ] Open browser
- [ ] Visit: `https://luma-backend.onrender.com/health`
- [ ] Expected response:
```json
{
  "status": "healthy",
  "environment": "production",
  "timestamp": "2025-10-22"
}
```
- [ ] Visit: `https://luma-backend.onrender.com/docs`
- [ ] Verify Swagger UI loads with all endpoints

---

## ☑️ TESTING (20 minutes)

### 10. Test Signup Flow (5 min)
```bash
curl -X POST https://luma-backend.onrender.com/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Corporation",
    "contact_email": "YOUR_EMAIL@example.com",
    "sector": "Technology"
  }'
```

- [ ] Expected: `{"message":"Thank you for signing up!","company_id":"..."}`
- [ ] Check your email for welcome message
- [ ] Verify Google Form link works

---

### 11. Test Approval Flow (5 min)
- [ ] In Render, go to **Shell** tab
- [ ] Run:
```bash
python scripts/approve_company.py --list
```
- [ ] Verify "Test Corporation" appears
- [ ] Run:
```bash
python scripts/approve_company.py "Test Corporation" admin@test.com
```
- [ ] Copy generated password from output
- [ ] Check email for credentials

---

### 12. Test Login (3 min)
```bash
curl -X POST https://luma-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "PASTE_GENERATED_PASSWORD_HERE"
  }'
```

- [ ] Expected: `{"access_token":"eyJ...","token_type":"bearer","user":{...}}`
- [ ] Copy the `access_token` value

---

### 13. Test Upload (5 min)
```bash
# Download sample invoice
curl -O https://raw.githubusercontent.com/[your-repo]/backend/samples/iberdrola_may2025.txt

# Upload it
curl -X POST https://luma-backend.onrender.com/api/files/upload \
  -H "Authorization: Bearer PASTE_TOKEN_HERE" \
  -F "file=@iberdrola_may2025.txt"
```

- [ ] Expected: `{"file_id":"...","status":"processed","record":{...}}`
- [ ] Verify `co2e_kg` is calculated
- [ ] Check Supabase Storage → `uploads` bucket has file

---

### 14. Test Dashboard (2 min)
```bash
curl https://luma-backend.onrender.com/api/dashboard \
  -H "Authorization: Bearer PASTE_TOKEN_HERE"
```

- [ ] Expected: `{"kpis":{...},"trend":{...},"scope_pie":{...},"uploads":[...]}`
- [ ] Verify upload appears in `uploads` array

---

## ☑️ FRONTEND INTEGRATION (15 minutes)

### 15. Update Frontend Environment (5 min)
- [ ] In Vercel project settings
- [ ] Add environment variable:
  - Key: `VITE_API_URL`
  - Value: `https://luma-backend.onrender.com`
- [ ] Redeploy frontend
- [ ] Wait for deployment

---

### 16. Update Backend CORS (5 min)
- [ ] Get Vercel deployment URL: `https://[your-app].vercel.app`
- [ ] In Render, go to **Environment** tab
- [ ] Update `ALLOWED_ORIGINS`:
  ```
  https://getluma.es,https://[your-app].vercel.app
  ```
- [ ] Click "Save Changes"
- [ ] Wait for auto-redeploy

---

### 17. Test Full Flow (5 min)
- [ ] Visit your frontend: `https://getluma.es` or Vercel URL
- [ ] Click "Join Luma"
- [ ] Fill signup form
- [ ] Check email
- [ ] Approve company via Render shell
- [ ] Login with credentials
- [ ] Upload an invoice (drag & drop)
- [ ] Verify dashboard updates

---

## ☑️ POST-LAUNCH (10 minutes)

### 18. Set Up Monitoring (5 min)
- [ ] In Render, go to **Metrics** tab
- [ ] Enable email alerts for:
  - Service down
  - High error rate
  - High memory usage

### 19. Documentation (5 min)
- [ ] Bookmark important URLs:
  - API: `https://luma-backend.onrender.com`
  - Docs: `https://luma-backend.onrender.com/docs`
  - Supabase: `https://app.supabase.com`
  - Render: `https://dashboard.render.com`
  - Resend: `https://resend.com/emails`

- [ ] Save credentials securely (password manager)

---

## 🎉 LAUNCH COMPLETE!

### ✅ Success Checklist
- [x] Backend deployed to Render
- [x] Database initialized
- [x] All 5 tests passed
- [x] Frontend connected
- [x] CORS configured
- [x] Emails sending
- [x] Full flow working

---

## 📊 Next Steps

### Week 1: Soft Launch
- [ ] Invite 2-3 test companies
- [ ] Monitor logs daily
- [ ] Collect feedback
- [ ] Fix any issues

### Week 2: Public Launch
- [ ] Update website with signup CTA
- [ ] Announce on social media
- [ ] Monitor performance
- [ ] Track signups

### Month 1: Optimize
- [ ] Analyze usage patterns
- [ ] Add missing invoice formats
- [ ] Improve parsing accuracy
- [ ] Gather feature requests

---

## 🚨 Troubleshooting Quick Fixes

### Backend won't start
1. Check Render logs for errors
2. Verify all env vars are set
3. Check DATABASE_URL format

### CORS errors
1. Ensure frontend URL is in ALLOWED_ORIGINS
2. No trailing slashes in URLs
3. Redeploy backend after changes

### Emails not sending
1. Check RESEND_API_KEY is valid
2. Verify sender email/domain
3. Check Resend dashboard for errors

### File upload fails
1. Verify Supabase buckets exist
2. Check buckets are set to Public
3. Verify SUPABASE_SERVICE_KEY is correct

---

## 📞 Support Resources

- **Render Docs**: https://render.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Resend Docs**: https://resend.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com

---

## 🎓 You Did It!

**Your ESG automation platform is now LIVE! 🚀**

Time to transform sustainability reporting in Spain! 🇪🇸🌱

---

**Total Time: ~2 hours**
**Monthly Cost: $7 (Render Starter)**
**Value Delivered: Priceless** ✨
