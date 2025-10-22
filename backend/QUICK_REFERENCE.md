# 🚀 Luma Backend - Quick Reference Card

## 📁 File Locations

| What | Where |
|------|-------|
| Main app | `backend/main.py` |
| Config | `backend/app/config.py` |
| Models | `backend/app/models/database.py` |
| Auth routes | `backend/app/routes/auth.py` |
| Upload routes | `backend/app/routes/files.py` |
| Dashboard | `backend/app/routes/dashboard.py` |
| Reports | `backend/app/routes/reports.py` |
| Invoice parser | `backend/app/services/ocr.py` |
| Email service | `backend/app/services/email.py` |
| Approval script | `backend/scripts/approve_company.py` |

---

## 🔑 Key Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app.database import init_db; init_db()"

# Run dev server
uvicorn main:app --reload --port 8000

# Approve company
python scripts/approve_company.py "Company Name" user@email.com

# List pending companies
python scripts/approve_company.py --list

# Build Docker image
docker build -t luma-backend .

# Run Docker container
docker run -p 8000:8000 --env-file .env luma-backend
```

---

## 🌐 API Endpoints

### Auth
- `POST /api/auth/signup` - Signup
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - User info

### Files
- `POST /api/files/upload` - Upload file
- `GET /api/files/uploads` - List uploads
- `GET /api/files/uploads/{id}` - Upload details

### Dashboard
- `GET /api/dashboard` - Dashboard data
- `GET /api/dashboard/summary` - CSRD summary

### Reports
- `POST /api/reports/generate` - Generate PDF
- `GET /api/reports/list` - List reports

---

## 🔧 Environment Variables (Critical)

```bash
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_KEY=...
SUPABASE_SERVICE_KEY=...
JWT_SECRET=...
RESEND_API_KEY=re_...
FRONTEND_URL=https://getluma.es
ALLOWED_ORIGINS=https://getluma.es
GOOGLE_FORM_URL=https://forms.google.com/...
```

---

## 📊 Supported Invoice Formats

### PDF Invoices
- **Iberdrola** (electricity)
- **Endesa** (electricity)
- **Naturgy** (gas)
- **Repsol/Cepsa/Galp** (fuel)

### CSV/XLSX
- Electricity batches
- Diesel/fuel transactions
- Freight/logistics data

---

## 🧪 Quick Test

```bash
# 1. Signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Test","contact_email":"test@test.com"}'

# 2. Approve
python scripts/approve_company.py "Test" admin@test.com

# 3. Login (get token)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"[generated]"}'

# 4. Upload
curl -X POST http://localhost:8000/api/files/upload \
  -H "Authorization: Bearer [TOKEN]" \
  -F "file=@samples/iberdrola_may2025.txt"

# 5. Dashboard
curl http://localhost:8000/api/dashboard \
  -H "Authorization: Bearer [TOKEN]"
```

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS error | Update `ALLOWED_ORIGINS` in `.env` |
| DB connection failed | Check `DATABASE_URL` format |
| File upload fails | Verify Supabase Storage buckets exist |
| Email not sending | Check `RESEND_API_KEY` |
| JWT invalid | Ensure `JWT_SECRET` is set |
| Low confidence parsing | Check invoice format matches regex |

---

## 📂 Database Tables

- `companies` - Company info
- `users` - User credentials
- `uploads` - Uploaded files + extracted data
- `reports` - Generated PDF reports
- `compliance_metrics` - CSRD requirements

---

## 🎯 Deployment Steps

1. Create Supabase project + buckets
2. Get Resend API key
3. Create Google Form
4. Deploy to Render (set env vars)
5. Initialize database
6. Update frontend with API URL
7. Test full flow

---

## 📧 Email Templates

1. **Welcome** - Sent on signup
2. **Credentials** - Sent on approval
3. **Report Ready** - Sent when PDF generated

---

## 📈 Emission Factors

| Source | Factor | Unit |
|--------|--------|------|
| Electricity | 0.231 | kg CO₂e/kWh |
| Gas | 0.202 | kg CO₂e/kWh |
| Diesel | 2.680 | kg CO₂e/L |
| Gasoline | 2.310 | kg CO₂e/L |

---

## 🔗 URLs (Production)

- **API**: https://luma-backend.onrender.com
- **Docs**: https://luma-backend.onrender.com/docs
- **Health**: https://luma-backend.onrender.com/health
- **Frontend**: https://getluma.es

---

## 💡 Pro Tips

- Use `/docs` for interactive API testing
- Check Render logs for debugging
- Monitor Supabase dashboard for DB health
- Test with sample files in `/samples`
- Keep `JWT_SECRET` secure (32+ chars)
- Enable HTTPS only in production

---

**Need Help?** Check `README.md`, `DEPLOYMENT.md`, or `INTEGRATION.md`
