# 🚀 Luma ESG - Deployment Guide

## Backend Deployment (Render)

### Step 1: Prepare Git Repository
```bash
cd C:\Users\salmane\Desktop\luma-better-main\backend
git init
git add .
git commit -m "Initial backend setup"
```

### Step 2: Push to GitHub
1. Create a new GitHub repository called `luma-esg-backend`
2. Push your code:
```bash
git remote add origin https://github.com/YOUR_USERNAME/luma-esg-backend.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Render
1. Go to https://render.com and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `luma-esg-backend`
4. Render will auto-detect the `render.yaml` file
5. Click **"Apply"**

### Step 4: Set Environment Variables
In Render dashboard, go to your service → **Environment** and add:

```
DATABASE_URL=postgresql://postgres.vlecbtkfvwkntlyaluvr:E6sS0J9q7NHBxseg@aws-0-eu-central-1.pooler.supabase.com:6543/postgres

SUPABASE_URL=https://vlecbtkfvwkntlyaluvr.supabase.co

SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZsZWNidGtmdndrbnRseWFsdXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEwOTUzMTQsImV4cCI6MjA3NjY3MTMxNH0.i1ZK4Wz6o1E-Bk1XrIODM6OIFJJmJURM9_uWgxngFWQ

SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZsZWNidGtmdndrbnRseWFsdXZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTA5NTMxNCwiZXhwIjoyMDc2NjcxMzE0fQ.hy1n5cKgDJcQFjeWDkI0iHGouMt538de8CybeedSO3Y

JWT_SECRET=5x9ERi18lGBp4TbcPnWhFyd0rXMeoDOv

RESEND_API_KEY=re_Myw6iVgY_HZ4JbxDJWjivdWoeziG9dsxE

ADMIN_EMAIL=admin@getluma.es

GOOGLE_FORM_URL=https://docs.google.com/forms/d/e/1FAIpQLSf4aQmdwdyQPPm79a9bzx8kOjBxNOvraGvz9OiaYeT2okUHxQ/viewform

FRONTEND_URL=https://YOUR_DOMAIN.com

ENVIRONMENT=production
DEBUG=False
```

### Step 5: Update CORS After Deployment
Once deployed, Render will give you a URL like: `https://luma-esg-backend.onrender.com`

Update your frontend URL in Render environment variables:
```
FRONTEND_URL=https://getluma.es
ALLOWED_ORIGINS=https://getluma.es,https://www.getluma.es
```

---

## Frontend Deployment (Vercel)

### Step 1: Update Frontend API URL
In your frontend code, update the API endpoint to your Render URL:
```typescript
// src/config.ts or similar
const API_URL = "https://luma-esg-backend.onrender.com/api"
```

### Step 2: Deploy to Vercel
1. Go to https://vercel.com and sign up/login
2. Click **"Add New Project"**
3. Import your frontend repository
4. Vercel auto-detects Vite/React settings
5. Click **"Deploy"**

### Step 3: Configure Custom Domain
1. In Vercel dashboard → **Settings** → **Domains**
2. Add your domain: `getluma.es`
3. Add DNS records (Vercel will show you exactly what to add):
   - Type: A, Name: @, Value: 76.76.21.21
   - Type: CNAME, Name: www, Value: cname.vercel-dns.com

### Step 4: Update Environment Variables (if needed)
In Vercel → **Settings** → **Environment Variables**:
```
VITE_API_URL=https://luma-esg-backend.onrender.com/api
```

---

## Testing the Deployment

### Backend Health Check
```
GET https://luma-esg-backend.onrender.com/health
```

### API Documentation
```
https://luma-esg-backend.onrender.com/docs
```

### Frontend
```
https://getluma.es
```

---

## Post-Deployment Checklist

✅ Backend deployed to Render
✅ Frontend deployed to Vercel  
✅ Custom domain configured
✅ Environment variables set
✅ CORS configured correctly
✅ Database tables created in Supabase
✅ Storage buckets created (uploads, reports)
✅ SSL certificates active (auto by Vercel/Render)
✅ Email service tested
✅ Signup → Approval → Login flow tested

---

## Monitoring & Logs

### Render Logs
- Go to your service → **Logs** tab
- Real-time application logs

### Vercel Logs  
- Go to your deployment → **Functions** tab
- Check for any errors

### Supabase Dashboard
- Monitor database usage
- Check storage bucket files

---

## Estimated Costs

- **Render Free Tier**: $0/month (spins down after 15min inactivity, cold start ~30s)
- **Vercel Hobby**: $0/month (perfect for your use case)
- **Supabase Free**: $0/month (500MB database, 1GB storage)
- **Resend Free**: $0/month (100 emails/day)

**Total: $0/month** 🎉

Upgrade only if you need:
- Render Starter ($7/mo) - No cold starts, always on
- Vercel Pro ($20/mo) - More bandwidth, team features
- Supabase Pro ($25/mo) - More storage/bandwidth

---

## Support

If deployment fails:
1. Check Render logs for errors
2. Verify all environment variables are set
3. Ensure requirements.txt has correct versions
4. Check Supabase connection string is correct

Need help? The deployment should take ~10 minutes total! 🚀
