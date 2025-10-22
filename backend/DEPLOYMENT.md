# Deployment Guide - Luma Backend on Render

## 🚀 Deploy FastAPI Backend to Render

### Prerequisites
- GitHub repository with backend code
- Render account (free tier works)
- Supabase account (for database & storage)
- Resend account (for emails)

---

## Step 1️⃣: Prepare Supabase

### Create Supabase Project
1. Go to https://supabase.com
2. Create new project
3. Wait for provisioning (~2 minutes)

### Get Database URL
1. Go to **Project Settings** → **Database**
2. Copy **Connection string (URI)**
3. Format: `postgresql://postgres:[password]@[host]:5432/postgres`

### Create Storage Buckets
1. Go to **Storage** in sidebar
2. Create two buckets:
   - `uploads` (for invoices/documents)
   - `reports` (for generated PDFs)
3. Set both to **Public** (or configure policies)

### Get API Keys
1. Go to **Project Settings** → **API**
2. Copy:
   - **Project URL** (SUPABASE_URL)
   - **anon/public key** (SUPABASE_KEY)
   - **service_role key** (SUPABASE_SERVICE_KEY)

---

## Step 2️⃣: Setup Resend

1. Go to https://resend.com
2. Sign up / Login
3. Get API key from dashboard
4. Verify your domain (or use resend.dev for testing)

---

## Step 3️⃣: Deploy to Render

### Create Web Service
1. Go to https://render.com
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Select the repository with backend code

### Configure Build Settings
- **Name**: `luma-backend`
- **Region**: Choose closest to Spain (Frankfurt/Amsterdam)
- **Branch**: `main`
- **Root Directory**: `backend` (if backend is in subdirectory)
- **Runtime**: `Python 3`
- **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

### Environment Variables
Click **Advanced** → **Add Environment Variable** and add:

```bash
# Database (from Supabase)
DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_KEY=[anon-key]
SUPABASE_SERVICE_KEY=[service-role-key]

# JWT (generate a random secret)
JWT_SECRET=[generate-random-string-here]
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Email (from Resend)
RESEND_API_KEY=re_[your-key]
ADMIN_EMAIL=admin@getluma.es

# Frontend (update after Vercel deployment)
FRONTEND_URL=https://getluma.es
ALLOWED_ORIGINS=https://getluma.es,https://[your-vercel-app].vercel.app

# Google Form (create form first)
GOOGLE_FORM_URL=https://forms.google.com/[your-form-id]

# Emission Factors (Spain defaults)
ELECTRICITY_FACTOR_KG_PER_KWH=0.231
NATURAL_GAS_FACTOR_KG_PER_KWH=0.202
DIESEL_FACTOR_KG_PER_L=2.680
GASOLINE_FACTOR_KG_PER_L=2.310
ROAD_FREIGHT_FACTOR_KG_PER_TKM=0.062
RAIL_FREIGHT_FACTOR_KG_PER_TKM=0.018
SEA_FREIGHT_FACTOR_KG_PER_TKM=0.010
AIR_FREIGHT_FACTOR_KG_PER_TKM=0.500

# Natural Gas Conversion
NATURAL_GAS_M3_TO_KWH=11.63

# File Upload
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,csv,xlsx,jpg,png

# Environment
ENVIRONMENT=production
DEBUG=False
```

### Deploy
1. Click **Create Web Service**
2. Wait for build & deployment (~5 minutes)
3. Your API will be available at: `https://luma-backend.onrender.com`

---

## Step 4️⃣: Initialize Database

### Option A: Run from Render Shell
1. Go to your Render service
2. Click **Shell** tab
3. Run:
```bash
python -c "from app.database import init_db; init_db()"
```

### Option B: Run Locally
1. Copy `DATABASE_URL` from Render env vars
2. Create local `.env` with that URL
3. Run:
```bash
python -c "from app.database import init_db; init_db()"
```

---

## Step 5️⃣: Test Backend

### Health Check
```bash
curl https://luma-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production"
}
```

### API Docs
Visit: `https://luma-backend.onrender.com/docs`

---

## Step 6️⃣: Create Google Form

1. Go to https://forms.google.com
2. Create new form with fields:
   - Company Name
   - Contact Person
   - Email
   - Phone
   - Sector/Industry
   - Number of Employees
   - CSRD Contact Person
   - Additional Notes
3. Copy form URL
4. Update `GOOGLE_FORM_URL` in Render env vars

---

## Step 7️⃣: Approve First Company

### Using Render Shell
1. Go to Render service → **Shell**
2. Run:
```bash
python scripts/approve_company.py --list
```

3. Approve a company:
```bash
python scripts/approve_company.py "Company Name" user@email.com
```

---

## Step 8️⃣: Connect Frontend (Vercel)

### Update Frontend ENV
In Vercel, set:
```bash
VITE_API_URL=https://luma-backend.onrender.com
```

### Update Backend CORS
In Render env vars, update:
```bash
ALLOWED_ORIGINS=https://getluma.es,https://[your-vercel-app].vercel.app
```

Then redeploy backend.

---

## 🔧 Maintenance

### View Logs
1. Go to Render service
2. Click **Logs** tab
3. Filter by errors/warnings

### Monitor Performance
1. Go to **Metrics** tab
2. Check:
   - Response times
   - Memory usage
   - Request volume

### Update Code
1. Push to GitHub
2. Render auto-deploys (if enabled)
3. Or manually trigger: **Manual Deploy** → **Deploy latest commit**

---

## 🚨 Troubleshooting

### Database Connection Error
- Check `DATABASE_URL` format
- Ensure Supabase project is running
- Verify IP whitelist in Supabase (Render IPs may change)

### File Upload Fails
- Check Supabase Storage buckets exist
- Verify `SUPABASE_SERVICE_KEY` is correct
- Check bucket policies (public or authenticated)

### Email Not Sending
- Verify `RESEND_API_KEY` is valid
- Check domain is verified in Resend
- For testing, use `onboarding@resend.dev` as sender

### CORS Errors
- Ensure frontend URL is in `ALLOWED_ORIGINS`
- Check URL format (no trailing slash)
- Redeploy backend after changes

---

## 📊 Performance Tips

### Free Tier Limitations
- Render free tier spins down after 15 min inactivity
- First request after spin-down takes ~30 seconds
- Upgrade to paid ($7/mo) for always-on

### Optimize Cold Starts
1. Reduce dependencies in `requirements.txt`
2. Use health check endpoint from frontend to keep warm
3. Consider caching with Redis (add-on)

### Scale Up
When needed:
1. Upgrade Render plan (more RAM/CPU)
2. Enable auto-scaling
3. Add read replicas for database

---

## 🔐 Security Checklist

✅ Use strong `JWT_SECRET` (32+ random chars)
✅ Enable HTTPS only (Render does this)
✅ Set `DEBUG=False` in production
✅ Restrict `ALLOWED_ORIGINS` to known domains
✅ Use Supabase service key only on backend
✅ Enable Supabase RLS (Row Level Security)
✅ Rotate API keys periodically
✅ Monitor logs for suspicious activity

---

## 🎉 Done!

Your backend is now live at: `https://luma-backend.onrender.com`

Test the full flow:
1. User signs up → receives welcome email
2. You approve via script → user gets credentials email
3. User logs in → sees empty dashboard
4. User uploads invoice → auto-extraction works
5. User generates report → PDF created & emailed

---

## 📞 Support

If issues persist:
- Check Render logs
- Verify all env vars are set
- Test endpoints with Postman/curl
- Contact: admin@getluma.es
