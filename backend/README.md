# Luma Backend

FastAPI backend for Luma ESG automation platform.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (or Supabase account)
- Resend API key
- Supabase account

### Installation

1. **Clone and navigate to backend**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.template .env
# Edit .env with your credentials
```

5. **Initialize database**
```bash
python -c "from app.database import init_db; init_db()"
```

6. **Run development server**
```bash
uvicorn main:app --reload --port 8000
```

API will be available at: http://localhost:8000
API docs: http://localhost:8000/docs

## 📁 Project Structure

```
backend/
├── app/
│   ├── models/
│   │   ├── database.py       # SQLAlchemy models
│   │   └── schemas.py        # Pydantic schemas
│   ├── routes/
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── files.py          # File upload & processing
│   │   ├── dashboard.py      # Dashboard data
│   │   └── reports.py        # Report generation
│   ├── services/
│   │   ├── auth.py           # JWT & password utilities
│   │   ├── email.py          # Resend email service
│   │   └── ocr.py            # Document parsing
│   ├── config.py             # Configuration management
│   └── database.py           # Database connection
├── scripts/
│   └── approve_company.py    # Company approval CLI
├── samples/
│   ├── iberdrola_may2025.txt
│   ├── electricity_batch.csv
│   ├── diesel_june2025.csv
│   └── freight_may2025.csv
├── main.py                   # FastAPI app entry point
├── requirements.txt
├── Dockerfile
└── .env.template
```

## 🔧 Configuration

### Environment Variables

Required variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# JWT
JWT_SECRET=your-secret-key

# Email
RESEND_API_KEY=re_your_key

# Frontend
FRONTEND_URL=https://getluma.es
ALLOWED_ORIGINS=https://getluma.es,http://localhost:5173

# Google Form
GOOGLE_FORM_URL=https://forms.google.com/your-form
```

## 📊 API Endpoints

### Authentication
- `POST /api/auth/signup` - Company signup
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Files
- `POST /api/files/upload` - Upload invoice/document
- `GET /api/files/uploads` - List all uploads
- `GET /api/files/uploads/{id}` - Get upload details
- `DELETE /api/files/uploads/{id}` - Delete upload

### Dashboard
- `GET /api/dashboard` - Get dashboard data (KPIs, trends, uploads)
- `GET /api/dashboard/summary` - Get CSRD compliance summary

### Reports
- `POST /api/reports/generate` - Generate PDF report
- `GET /api/reports/list` - List all reports

## 🛠️ Admin Tools

### Approve a Company

```bash
python scripts/approve_company.py "Company Name" user@email.com

# List pending companies
python scripts/approve_company.py --list
```

This will:
1. Approve the company
2. Create user credentials
3. Send welcome email with login details

## 🧪 Testing

Test with sample files:

```bash
# Upload Iberdrola invoice
curl -X POST http://localhost:8000/api/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@samples/iberdrola_may2025.txt"

# Upload CSV batch
curl -X POST http://localhost:8000/api/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@samples/electricity_batch.csv"
```

## 🐳 Docker Deployment

### Build image
```bash
docker build -t luma-backend .
```

### Run container
```bash
docker run -p 8000:8000 --env-file .env luma-backend
```

## 🚀 Deploy to Render

1. Create new Web Service on Render
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.11
4. Add environment variables from `.env.template`
5. Deploy!

## 📝 Invoice Parsing

Supports:
- **Spanish Utilities**: Iberdrola, Endesa, Naturgy (electricity & gas)
- **Fuel Cards**: Repsol, Cepsa, Galp, Shell, BP
- **Freight**: DHL, SEUR, MRW (from CSV)
- **Generic CSV/XLSX**: Flexible column mapping

### Emission Factors (Spain defaults)
- Electricity: 0.231 kg CO2e/kWh
- Natural Gas: 0.202 kg CO2e/kWh
- Diesel: 2.680 kg CO2e/L
- Gasoline: 2.310 kg CO2e/L
- Road Freight: 0.062 kg CO2e/tkm

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- Company-level data isolation
- File size & type validation
- CORS protection

## 📧 Email Templates

Three email types:
1. **Welcome Email** - Sent on signup with Google Form link
2. **Credentials Email** - Sent on approval with login details
3. **Report Ready** - Sent when PDF report is generated

## 🌍 Multi-language Support

Currently supports:
- Spanish (default)
- English

Set language in API requests or email templates.

## 📖 API Documentation

Full interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Support

For issues or questions, contact admin@getluma.es
