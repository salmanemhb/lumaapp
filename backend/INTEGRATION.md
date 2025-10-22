# Luma - Full Stack Integration Guide

## 🏗️ Architecture Overview

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│                 │      │                  │      │                 │
│   React App     │─────▶│  FastAPI Backend │─────▶│   Supabase      │
│   (Vercel)      │      │    (Render)      │      │  (DB+Storage)   │
│                 │      │                  │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │                       │                          │
         │                       │                          │
         ▼                       ▼                          ▼
   getluma.es          luma-backend.onrender.com    Postgres + S3
                                │
                                ▼
                       ┌────────────────┐
                       │     Resend     │
                       │  (Email API)   │
                       └────────────────┘
```

---

## 📋 Complete Setup Checklist

### 1️⃣ Backend Setup (FastAPI on Render)

#### A. Supabase Configuration
- [ ] Create Supabase project
- [ ] Create `uploads` storage bucket (public)
- [ ] Create `reports` storage bucket (public)
- [ ] Copy Database URL, Project URL, anon key, service key
- [ ] Enable Row Level Security (optional but recommended)

#### B. Resend Configuration
- [ ] Create Resend account
- [ ] Get API key
- [ ] Verify domain OR use `onboarding@resend.dev` for testing

#### C. Google Form
- [ ] Create Google Form for company verification
- [ ] Add fields: company name, contact, email, phone, sector, CSRD contact
- [ ] Get shareable link
- [ ] Set to accept responses

#### D. Render Deployment
- [ ] Create Web Service on Render
- [ ] Connect GitHub repo
- [ ] Set root directory to `backend`
- [ ] Configure build command: `pip install -r requirements.txt`
- [ ] Configure start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Add all environment variables (see DEPLOYMENT.md)
- [ ] Deploy and wait for build
- [ ] Test: `https://[your-service].onrender.com/health`

#### E. Database Initialization
- [ ] Open Render Shell OR connect locally
- [ ] Run: `python -c "from app.database import init_db; init_db()"`
- [ ] Verify tables created in Supabase

---

### 2️⃣ Frontend Setup (React on Vercel)

#### A. Environment Variables
Create `.env.local` in frontend root:

```bash
VITE_API_URL=https://[your-render-service].onrender.com
```

#### B. Update API Integration

In your React app, create API client:

```typescript
// src/lib/api.ts
const API_URL = import.meta.env.VITE_API_URL;

export const api = {
  // Auth
  signup: (data) => fetch(`${API_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }),
  
  login: (email, password) => fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  }),
  
  // Dashboard
  getDashboard: (token) => fetch(`${API_URL}/api/dashboard`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  
  // Upload
  uploadFile: (token, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${API_URL}/api/files/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
  },
  
  // Reports
  generateReport: (token, data) => fetch(`${API_URL}/api/reports/generate`, {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
};
```

#### C. Auth Context Update

```typescript
// src/contexts/AuthContext.tsx
const login = async (email: string, password: string) => {
  const response = await api.login(email, password);
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
    return true;
  }
  return false;
};
```

#### D. Dashboard Integration

```typescript
// src/pages/Dashboard.tsx
useEffect(() => {
  const fetchDashboard = async () => {
    const token = localStorage.getItem('token');
    const response = await api.getDashboard(token);
    const data = await response.json();
    
    // Update state with:
    // data.kpis (total_emissions_kg, scope1_kg, etc.)
    // data.trend (months, values_kg)
    // data.scope_pie (scope1, scope2, scope3)
    // data.uploads (recent files)
  };
  
  fetchDashboard();
}, []);
```

#### E. Upload Component

```typescript
// src/components/UploadArea.tsx
const handleUpload = async (file: File) => {
  const token = localStorage.getItem('token');
  const response = await api.uploadFile(token, file);
  const data = await response.json();
  
  if (response.ok) {
    // Show success: data.record contains extracted info
    // Update dashboard
  } else {
    // Show error
  }
};
```

#### F. Vercel Deployment
- [ ] Push to GitHub
- [ ] Import project in Vercel
- [ ] Add environment variable: `VITE_API_URL`
- [ ] Deploy
- [ ] Get deployment URL: `https://[your-app].vercel.app`
- [ ] Update custom domain to `getluma.es`

---

### 3️⃣ Backend CORS Update

After frontend deployment:
- [ ] Go to Render service → Environment
- [ ] Update `ALLOWED_ORIGINS`:
  ```
  https://getluma.es,https://[your-app].vercel.app
  ```
- [ ] Update `FRONTEND_URL`:
  ```
  https://getluma.es
  ```
- [ ] Redeploy backend

---

## 🔄 Complete User Flow

### Flow 1: Company Signup
1. User visits `getluma.es`
2. Fills "Join Luma" form (company name, email, sector)
3. Frontend calls `POST /api/auth/signup`
4. Backend:
   - Creates pending company in DB
   - Sends welcome email via Resend
   - Email contains Google Form link
5. User receives email, fills Google Form
6. You receive form response notification

### Flow 2: Company Approval (Admin)
1. You review Google Form submission
2. Run approval script:
   ```bash
   python scripts/approve_company.py "Company Name" user@company.com
   ```
3. Script:
   - Approves company
   - Creates user with auto-generated password
   - Sends credentials email
4. User receives login credentials

### Flow 3: First Login
1. User visits `getluma.es/login`
2. Enters email + password
3. Frontend calls `POST /api/auth/login`
4. Backend validates, returns JWT token
5. Frontend stores token, redirects to dashboard
6. Dashboard shows "No Data Yet" (empty state)

### Flow 4: First Upload
1. User clicks upload area or drags file
2. Frontend calls `POST /api/files/upload` with file
3. Backend:
   - Uploads to Supabase Storage
   - Extracts text from PDF (PyMuPDF)
   - Parses with regex (Iberdrola/Endesa/etc.)
   - Calculates CO2e = usage × emission factor
   - Returns extracted data
4. Frontend shows extraction result:
   ```json
   {
     "supplier": "Iberdrola",
     "category": "electricity",
     "scope": 2,
     "usage_value": 12500,
     "usage_unit": "kWh",
     "co2e_kg": 2887.5,
     "confidence": 0.93
   }
   ```
5. Dashboard refreshes with new data

### Flow 5: Dashboard View
1. Frontend calls `GET /api/dashboard`
2. Backend aggregates:
   - Total emissions by scope
   - Monthly trend (last 6 months)
   - Recent uploads list
   - CSRD coverage %
3. Frontend displays:
   - KPI cards (total, scope 1/2/3)
   - Line chart (trend)
   - Pie chart (scope breakdown)
   - Upload table

### Flow 6: Report Generation
1. User clicks "Generate Report"
2. Frontend calls `POST /api/reports/generate` with period
3. Backend:
   - Queries uploads in period
   - Calculates totals
   - Generates PDF with ReportLab
   - Uploads to Supabase Storage
   - Sends email with download link
4. Frontend shows success + download button
5. User receives email with PDF link

---

## 🧪 Testing the Full Flow

### Test 1: Signup
```bash
curl -X POST https://luma-backend.onrender.com/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Corp",
    "contact_email": "test@example.com",
    "sector": "Technology"
  }'
```

Expected: Welcome email sent to test@example.com

### Test 2: Approval
```bash
# On Render shell or locally
python scripts/approve_company.py "Test Corp" admin@testcorp.com
```

Expected: Credentials email sent

### Test 3: Login
```bash
curl -X POST https://luma-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@testcorp.com",
    "password": "[generated-password]"
  }'
```

Expected: JWT token returned

### Test 4: Upload
```bash
curl -X POST https://luma-backend.onrender.com/api/files/upload \
  -H "Authorization: Bearer [TOKEN]" \
  -F "file=@samples/iberdrola_may2025.txt"
```

Expected: Parsed invoice data returned

### Test 5: Dashboard
```bash
curl https://luma-backend.onrender.com/api/dashboard \
  -H "Authorization: Bearer [TOKEN]"
```

Expected: KPIs, trends, uploads

---

## 🔐 Security Best Practices

### Backend
- [x] JWT with strong secret (32+ chars)
- [x] Password hashing (bcrypt)
- [x] Company-level data isolation
- [x] File type & size validation
- [x] CORS restricted to known domains
- [ ] Rate limiting (add middleware)
- [ ] Input sanitization (SQL injection protection)
- [ ] HTTPS only (Render default)

### Frontend
- [x] Token stored in localStorage (or httpOnly cookies)
- [x] Auto-logout on 401
- [x] Protected routes (redirect if not logged in)
- [ ] XSS protection (sanitize user input)
- [ ] CSRF tokens (if using cookies)

### Database (Supabase)
- [ ] Enable Row Level Security (RLS)
- [ ] Create policies: users can only access their company data
- [ ] Backup enabled
- [ ] SSL enforced

---

## 📊 Monitoring & Analytics

### Backend Metrics (Render)
- Response time
- Error rate
- Memory usage
- Request volume

### Database Metrics (Supabase)
- Connections
- Query performance
- Storage usage

### Email Metrics (Resend)
- Delivery rate
- Open rate
- Bounce rate

### Frontend Metrics (Vercel)
- Page load time
- Core Web Vitals
- Error tracking (add Sentry)

---

## 🚀 Go-Live Checklist

### Pre-Launch
- [ ] All environment variables set
- [ ] Database initialized
- [ ] Email templates tested
- [ ] Upload parsing tested (all Spanish suppliers)
- [ ] PDF generation tested
- [ ] CORS configured correctly
- [ ] SSL certificates active
- [ ] Domain DNS configured (getluma.es → Vercel)
- [ ] Admin script tested

### Launch Day
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel
- [ ] Test full signup → upload → report flow
- [ ] Monitor logs for errors
- [ ] Set up monitoring alerts

### Post-Launch
- [ ] Approve first real company
- [ ] Collect user feedback
- [ ] Monitor performance
- [ ] Plan feature roadmap

---

## 🆘 Troubleshooting

### Issue: CORS Error
**Solution**: Ensure frontend URL is in `ALLOWED_ORIGINS`, redeploy backend

### Issue: Database Connection Failed
**Solution**: Check `DATABASE_URL` format, verify Supabase is running

### Issue: File Upload Fails
**Solution**: Check Supabase Storage buckets exist and are public

### Issue: Email Not Sending
**Solution**: Verify Resend API key, check domain verification

### Issue: JWT Invalid
**Solution**: Ensure `JWT_SECRET` matches between deployments, token not expired

### Issue: Parsing Returns Low Confidence
**Solution**: Check invoice format matches expected regex patterns, add new patterns

---

## 📞 Support Contacts

- **Backend Issues**: Check Render logs
- **Database Issues**: Check Supabase dashboard
- **Email Issues**: Check Resend dashboard
- **Frontend Issues**: Check Vercel logs

---

## 🎉 Success Criteria

Your platform is live when:
✅ Users can sign up and receive welcome email
✅ You can approve companies via script
✅ Users receive credentials and can log in
✅ Dashboard loads with empty state
✅ Spanish invoices (Iberdrola, Endesa, etc.) parse correctly
✅ CO2e calculations are accurate
✅ PDF reports generate successfully
✅ All emails send properly
✅ Frontend and backend communicate without CORS errors

**Congratulations! 🌱 Luma is now live and ready to automate ESG reporting for Spanish companies.**
