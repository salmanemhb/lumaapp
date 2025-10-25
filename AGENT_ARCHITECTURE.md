# 🤖 LUMA Multi-Agent System Architecture

**Date:** October 25, 2025  
**Status:** Design Phase → Implementation Ready

---

## 📋 Executive Summary

Luma is building an automated CSRD/ESG reporting platform using a modular agent-based architecture. This document defines the complete system structure for implementation.

---

## 🎯 System Overview

### Current State
- ✅ Frontend: React/Next.js on Netlify/Vercel
- ✅ Backend: FastAPI on Render
- ✅ Database: PostgreSQL (Supabase)
- ✅ Auth: Company signup + approval workflow
- ✅ Email: Resend API

### Target Architecture
- 🎯 9 specialized agents (instead of monolithic backend)
- 🎯 n8n workflow orchestration
- 🎯 Event-driven communication
- 🎯 CSRD/ESRS compliance built-in

---

## 🧩 Agent Definitions

### **Agent 1: Data Intake Agent**
**Purpose:** Extract and normalize data from uploaded files

**Triggers:**
- User uploads PDF/CSV/Excel/Image to dashboard
- File saved to Supabase Storage

**Process:**
```
Upload → File Validation → Type Detection → Data Extraction → Normalization → Storage
```

**Technology Stack:**
- OCR: Tesseract / Google Vision API
- PDF: pdfplumber / PyPDF2
- CSV/Excel: pandas
- Images: PIL + Tesseract

**Input:**
```json
{
  "file_url": "s3://bucket/invoice.pdf",
  "file_type": "pdf",
  "company_id": "uuid",
  "uploaded_at": "2025-10-25T10:00:00Z"
}
```

**Output:**
```json
{
  "upload_id": "uuid",
  "status": "processed", // or "review_needed"
  "confidence_score": 0.92,
  "extracted_data": {
    "supplier": "Iberdrola",
    "category": "electricity",
    "period_start": "2025-09-01",
    "period_end": "2025-09-30",
    "usage_value": 1250.5,
    "usage_unit": "kWh",
    "amount_total": 185.75,
    "currency": "EUR",
    "invoice_number": "INV-2025-09-001"
  }
}
```

**Database Tables:**
- `uploads` - File metadata and extraction results
- `extraction_logs` - OCR confidence and raw output

**API Endpoint:**
```
POST /api/agents/data-intake
Body: { "upload_id": "uuid" }
Response: { "status": "processed", "data": {...} }
```

**Error Handling:**
- Confidence < 70% → flag for manual review
- Extraction fails → retry 3x, then notify admin
- Unsupported format → reject with clear message

---

### **Agent 2: Emission Calculation Agent**
**Purpose:** Calculate CO2e emissions using regional factors

**Triggers:**
- Data Intake Agent completes extraction
- User manually corrects data

**Process:**
```
Normalized Data → Fetch Emission Factor → Apply Formula → Store Results → Update Dashboard
```

**Technology Stack:**
- Python calculation engine
- Redis cache for emission factors
- PostgreSQL for results

**Input:**
```json
{
  "upload_id": "uuid",
  "company_id": "uuid",
  "category": "electricity",
  "region": "ES-MD", // Spain - Madrid
  "usage_value": 1250.5,
  "usage_unit": "kWh",
  "period_start": "2025-09-01",
  "period_end": "2025-09-30"
}
```

**Calculation Logic:**
```python
# Fetch factor
factor = get_emission_factor(
    region="ES-MD",
    category="electricity",
    date="2025-09-01"
)
# Example: 0.215 kg CO2e per kWh (Spain grid mix 2025)

# Calculate
co2e_kg = usage_value * factor.value
# 1250.5 kWh * 0.215 = 268.86 kg CO2e

# Determine scope
scope = determine_scope(category)
# electricity → Scope 2 (purchased energy)
```

**Output:**
```json
{
  "emission_result_id": "uuid",
  "upload_id": "uuid",
  "scope": 2,
  "co2e_kg": 268.86,
  "emission_factor": 0.215,
  "emission_factor_source": "MITECO_2025_Q3",
  "calculation_date": "2025-10-25T10:05:00Z"
}
```

**Database Tables:**
- `emission_results` - Calculated emissions
- `emission_factors` - Regional factors with versioning

**API Endpoint:**
```
POST /api/agents/calculate-emissions
Body: { "upload_id": "uuid" }
Response: { "co2e_kg": 268.86, "scope": 2 }
```

---

### **Agent 3: Emission Factor Knowledge Agent** 🆕
**Purpose:** Maintain up-to-date regional emission factors

**Triggers:**
- Scheduled sync (quarterly)
- Manual refresh request
- New region added

**Data Sources:**
1. **Spain:** MITECO (Ministerio para la Transición Ecológica)
2. **EU:** Eurostat Energy Statistics
3. **Global:** IPCC 2006 Guidelines
4. **Fallback:** EPA Emission Factors

**Factor Schema:**
```sql
CREATE TABLE emission_factors (
  id UUID PRIMARY KEY,
  region VARCHAR(10), -- 'ES', 'ES-MD', 'FR', 'PT'
  category VARCHAR(50), -- 'electricity', 'natural_gas', 'diesel'
  scope INTEGER, -- 1, 2, or 3
  factor_value DECIMAL(15,6), -- kg CO2e per unit
  unit VARCHAR(20), -- 'kWh', 'm3', 'L', 'kg'
  source VARCHAR(100), -- 'MITECO_2025_Q3'
  methodology VARCHAR(100), -- 'Market-based' or 'Location-based'
  valid_from DATE,
  valid_until DATE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Example Factors:**
```json
{
  "Spain Electricity (2025 Q3)": {
    "region": "ES",
    "category": "electricity",
    "factor_value": 0.215,
    "unit": "kWh",
    "source": "MITECO_2025_Q3",
    "methodology": "Location-based"
  },
  "Spain Natural Gas": {
    "region": "ES",
    "category": "natural_gas",
    "factor_value": 2.016,
    "unit": "m3",
    "source": "IPCC_2006"
  },
  "Diesel (all regions)": {
    "region": "GLOBAL",
    "category": "diesel",
    "factor_value": 2.68,
    "unit": "L",
    "source": "IPCC_2006"
  }
}
```

**API Endpoints:**
```
GET  /api/factors?region=ES&category=electricity&date=2025-09-01
POST /api/factors/sync (admin only)
GET  /api/factors/history?category=electricity
```

**Sync Process:**
```
1. Check for new factors (compare dates)
2. Download from authoritative source
3. Validate format and values
4. Store with version control
5. Notify Calculation Agent of updates
6. Log sync in audit trail
```

---

### **Agent 4: CSRD Readiness Agent**
**Purpose:** Track compliance with ESRS disclosure requirements

**Triggers:**
- New emission data calculated
- User uploads additional data
- Report generated

**ESRS Modules Tracked:**
```
E1 - Climate Change
E2 - Pollution
E3 - Water and Marine Resources
E4 - Biodiversity and Ecosystems
E5 - Circular Economy
S1 - Own Workforce
S2 - Workers in Value Chain
S3 - Affected Communities
S4 - Consumers and End-Users
G1 - Business Conduct
```

**Readiness Calculation:**
```python
# E1 Requirements (Climate Change)
E1_REQUIREMENTS = {
    "E1-1": {
        "name": "Transition Plan",
        "required_data": ["scope1", "scope2", "scope3", "targets", "policies"]
    },
    "E1-2": {
        "name": "Energy Consumption",
        "required_data": ["electricity", "natural_gas", "renewable_pct"]
    },
    "E1-3": {
        "name": "GHG Emissions",
        "required_data": ["scope1", "scope2", "scope3", "intensity_metric"]
    },
    "E1-4": {
        "name": "GHG Removals",
        "required_data": ["carbon_offsets", "nature_based_solutions"]
    }
}

# Check coverage
def calculate_e1_readiness(company_data):
    total_requirements = len(E1_REQUIREMENTS)
    met_requirements = 0
    
    for code, req in E1_REQUIREMENTS.items():
        available = sum(1 for field in req["required_data"] 
                       if company_data.has(field))
        required = len(req["required_data"])
        
        if available / required >= 0.8:  # 80% threshold
            met_requirements += 1
    
    return (met_requirements / total_requirements) * 100
```

**Output:**
```json
{
  "company_id": "uuid",
  "overall_readiness": 45.2,
  "modules": {
    "E1": {
      "readiness": 75.0,
      "disclosures": {
        "E1-1": { "status": "complete", "coverage": 100 },
        "E1-2": { "status": "partial", "coverage": 80 },
        "E1-3": { "status": "complete", "coverage": 100 },
        "E1-4": { "status": "missing", "coverage": 0 }
      },
      "missing_data": ["carbon_offsets", "nature_based_solutions"]
    },
    "E2": { "readiness": 0, "disclosures": {...} }
  },
  "next_steps": [
    "Upload waste management data for E2",
    "Add carbon offset projects for E1-4",
    "Complete water consumption data for E3"
  ]
}
```

**Database Table:**
```sql
CREATE TABLE csrd_readiness (
  id UUID PRIMARY KEY,
  company_id UUID REFERENCES companies(id),
  esrs_module VARCHAR(10), -- 'E1', 'E2', etc.
  disclosure_code VARCHAR(20), -- 'E1-1', 'E1-2', etc.
  required BOOLEAN, -- based on materiality
  data_available BOOLEAN,
  completeness_pct DECIMAL(5,2),
  missing_items JSON,
  last_updated TIMESTAMP DEFAULT NOW()
);
```

**API Endpoint:**
```
GET /api/csrd/readiness/:company_id
Response: { "overall_readiness": 45.2, "modules": {...} }
```

---

### **Agent 5: Report Generation Agent**
**Purpose:** Create CSRD-compliant sustainability reports

**Triggers:**
- User clicks "Generate CSRD Report" button
- Scheduled annual report
- External audit request

**Report Types:**
1. **Full CSRD Report** (annual, all ESRS modules)
2. **Carbon Footprint Report** (GHG inventory)
3. **Custom Module Report** (e.g., E1 only)

**Generation Process:**
```
1. Aggregate all company data (emissions, uploads, metadata)
2. Calculate KPIs (intensity metrics, YoY change, targets progress)
3. Fetch ESRS templates based on material modules
4. Populate templates with data + narrative prompts
5. Generate PDF with charts and tables
6. Generate XBRL file (EU digital reporting format)
7. Store report in database + file storage
8. Send notification to user
```

**Technology Stack:**
- PDF: WeasyPrint or ReportLab
- XBRL: Arelle library
- Templates: Jinja2 with ESRS structure
- Charts: Plotly or Matplotlib

**Report Structure:**
```
CSRD Report 2025
├── Executive Summary
├── Company Profile
├── Materiality Assessment
├── ESRS E1: Climate Change
│   ├── E1-1: Transition Plan
│   ├── E1-2: Policies
│   ├── E1-3: Targets and Progress
│   ├── E1-4: Energy Consumption
│   ├── E1-5: GHG Emissions (Scope 1, 2, 3)
│   └── E1-6: Intensity Metrics
├── ESRS E2: Pollution (if material)
├── ...
├── Audit Trail Summary
└── Appendices
    ├── Emission Factor Sources
    ├── Calculation Methodologies
    └── Data Quality Notes
```

**Output:**
```json
{
  "report_id": "uuid",
  "company_id": "uuid",
  "report_type": "CSRD_Full",
  "period_start": "2025-01-01",
  "period_end": "2025-12-31",
  "esrs_modules": ["E1", "E2", "S1"],
  "completeness_score": 85.5,
  "file_url": "https://storage.com/reports/uuid.pdf",
  "xbrl_url": "https://storage.com/reports/uuid.xbrl",
  "generated_at": "2025-10-25T10:30:00Z",
  "version": 1
}
```

**Database Table:**
```sql
CREATE TABLE reports (
  id UUID PRIMARY KEY,
  company_id UUID REFERENCES companies(id),
  report_type VARCHAR(50),
  period_start DATE,
  period_end DATE,
  esrs_modules JSON,
  completeness_score DECIMAL(5,2),
  total_emissions_kg DECIMAL(15,2),
  file_url TEXT,
  xbrl_url TEXT,
  generated_at TIMESTAMP DEFAULT NOW(),
  version INTEGER DEFAULT 1
);
```

**API Endpoint:**
```
POST /api/reports/generate
Body: {
  "company_id": "uuid",
  "report_type": "CSRD_Full",
  "period_start": "2025-01-01",
  "period_end": "2025-12-31"
}
Response: {
  "report_id": "uuid",
  "status": "generating", // or "completed"
  "estimated_time": 120 // seconds
}
```

---

### **Agent 6: AI Review Agent**
**Purpose:** Validate data quality and CSRD compliance

**Triggers:**
- Report generated
- User requests review
- Scheduled compliance check

**Review Layers:**

**1. Data Quality Checks (Rule-Based)**
```python
def check_data_quality(company_data):
    issues = []
    
    # Outlier detection
    if company_data["emissions_current"] > company_data["emissions_previous"] * 5:
        issues.append({
            "severity": "high",
            "type": "outlier",
            "message": "Emissions increased 5x year-over-year",
            "suggestion": "Verify calculation or data entry"
        })
    
    # Missing periods
    gaps = find_date_gaps(company_data["monthly_emissions"])
    if gaps:
        issues.append({
            "severity": "medium",
            "type": "missing_data",
            "message": f"Missing data for months: {gaps}",
            "suggestion": "Upload invoices for missing periods"
        })
    
    # Inconsistent units
    if company_data["usage_units"] != company_data["previous_units"]:
        issues.append({
            "severity": "medium",
            "type": "inconsistency",
            "message": "Unit changed from kWh to MWh",
            "suggestion": "Confirm unit conversion is correct"
        })
    
    return issues
```

**2. CSRD Compliance Checks**
```python
def check_csrd_compliance(report):
    checks = {
        "double_materiality": {
            "required": True,
            "present": report.has("materiality_assessment"),
            "details": "CSRD requires double materiality assessment"
        },
        "climate_targets": {
            "required": report.modules.includes("E1"),
            "present": report.has("climate_targets"),
            "details": "E1-1 requires decarbonization targets"
        },
        "scope_3_disclosure": {
            "required": report.company.size == "Large",
            "present": report.has("scope3_emissions"),
            "details": "Large companies must report Scope 3"
        },
        "audit_trail": {
            "required": True,
            "present": report.has("audit_trail"),
            "details": "Full traceability required for assurance"
        }
    }
    
    compliance_score = sum(1 for c in checks.values() 
                          if not c["required"] or c["present"])
    compliance_score = (compliance_score / len(checks)) * 100
    
    return {
        "compliance_score": compliance_score,
        "checks": checks
    }
```

**3. AI-Powered Insights (LLM)**
```python
def get_ai_insights(report_text):
    prompt = f"""
You are a CSRD compliance auditor. Review this sustainability report excerpt:

{report_text}

Provide:
1. Completeness score (0-100)
2. Missing ESRS disclosures
3. Clarity improvements (max 3)
4. Red flags (greenwashing, inconsistencies)

Format as JSON.
"""
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.3
    )
    
    return json.loads(response.choices[0].message.content)
```

**Output:**
```json
{
  "review_id": "uuid",
  "report_id": "uuid",
  "data_quality_score": 92.0,
  "compliance_score": 85.0,
  "overall_score": 88.5,
  "issues": [
    {
      "severity": "high",
      "type": "missing_disclosure",
      "code": "E1-4",
      "message": "GHG removal projects not disclosed",
      "suggestion": "Add carbon offset or nature-based solutions data"
    },
    {
      "severity": "medium",
      "type": "data_gap",
      "message": "February 2025 emissions data missing",
      "suggestion": "Upload February invoices"
    }
  ],
  "strengths": [
    "Complete Scope 1 and 2 emissions",
    "Clear climate targets with timelines",
    "Good data traceability"
  ],
  "improvements": [
    "Add more context to Scope 3 calculations",
    "Include supplier engagement strategy",
    "Clarify renewable energy procurement"
  ],
  "reviewed_at": "2025-10-25T10:35:00Z"
}
```

**API Endpoint:**
```
POST /api/reports/:report_id/review
Response: {
  "overall_score": 88.5,
  "issues": [...],
  "improvements": [...]
}
```

---

### **Agent 7: Analytics & Visualization Agent**
**Purpose:** Prepare dashboard data and insights

**Triggers:**
- New emission data calculated
- User opens dashboard
- Scheduled daily aggregation

**Dashboard Metrics:**
```javascript
{
  // KPIs
  "total_emissions_kg": 125430.5,
  "scope1_kg": 12450.0,
  "scope2_kg": 68500.5,
  "scope3_kg": 44480.0,
  
  // Trends
  "monthly_emissions": [
    { "month": "2025-01", "total": 10500 },
    { "month": "2025-02", "total": 11200 },
    // ...
  ],
  
  // Scope breakdown
  "scope_breakdown": [
    { "scope": "Scope 1", "value": 12450, "percentage": 9.9 },
    { "scope": "Scope 2", "value": 68500, "percentage": 54.6 },
    { "scope": "Scope 3", "value": 44480, "percentage": 35.5 }
  ],
  
  // Category breakdown
  "category_breakdown": [
    { "category": "Electricity", "co2e_kg": 68500, "percentage": 54.6 },
    { "category": "Natural Gas", "co2e_kg": 12450, "percentage": 9.9 },
    { "category": "Transport", "co2e_kg": 35200, "percentage": 28.1 },
    { "category": "Waste", "co2e_kg": 9280, "percentage": 7.4 }
  ],
  
  // CSRD readiness
  "csrd_readiness": 45.2,
  
  // Recent uploads
  "recent_uploads": [
    {
      "id": "uuid",
      "file_name": "invoice_sept_2025.pdf",
      "status": "processed",
      "co2e_kg": 268.86,
      "uploaded_at": "2025-10-25T09:00:00Z"
    }
  ],
  
  // Insights
  "insights": [
    {
      "type": "alert",
      "message": "Emissions increased 15% compared to last month",
      "action": "Review September transport data"
    },
    {
      "type": "suggestion",
      "message": "Upload waste management data to improve CSRD readiness",
      "action": "Upload E2 data"
    }
  ]
}
```

**Performance Optimization:**
```sql
-- Materialized view for fast dashboard loads
CREATE MATERIALIZED VIEW company_dashboard_data AS
SELECT 
  c.id as company_id,
  c.name,
  -- Total emissions
  SUM(er.co2e_kg) as total_emissions_kg,
  SUM(CASE WHEN er.scope = 1 THEN er.co2e_kg ELSE 0 END) as scope1_kg,
  SUM(CASE WHEN er.scope = 2 THEN er.co2e_kg ELSE 0 END) as scope2_kg,
  SUM(CASE WHEN er.scope = 3 THEN er.co2e_kg ELSE 0 END) as scope3_kg,
  -- CSRD readiness
  AVG(cr.completeness_pct) as csrd_readiness,
  -- Last updated
  MAX(er.calculated_at) as last_updated
FROM companies c
LEFT JOIN emission_results er ON c.id = er.company_id
LEFT JOIN csrd_readiness cr ON c.id = cr.company_id
GROUP BY c.id, c.name;

-- Refresh nightly or after major updates
REFRESH MATERIALIZED VIEW company_dashboard_data;
```

**API Endpoint:**
```
GET /api/dashboard/:company_id
Response: { ...all dashboard data... }
```

---

### **Agent 8: Notification Agent**
**Purpose:** Send transactional emails and alerts

**Triggers:**
- Upload completed
- Report generated
- Review finished
- Approval needed
- CSRD deadline approaching

**Notification Types:**
```javascript
const NOTIFICATION_TEMPLATES = {
  UPLOAD_SUCCESS: {
    subject: "✅ Upload processed successfully",
    template: "upload_success.html",
    priority: "low",
    data: ["file_name", "co2e_kg", "category"]
  },
  
  UPLOAD_FAILED: {
    subject: "❌ Upload processing failed",
    template: "upload_failed.html",
    priority: "high",
    data: ["file_name", "error_message", "support_link"]
  },
  
  REPORT_READY: {
    subject: "📊 Your CSRD report is ready",
    template: "report_ready.html",
    priority: "medium",
    data: ["report_type", "download_link", "completeness_score"]
  },
  
  REVIEW_COMPLETE: {
    subject: "🔍 AI review completed",
    template: "review_complete.html",
    priority: "medium",
    data: ["overall_score", "issues_count", "view_link"]
  },
  
  CSRD_DEADLINE: {
    subject: "⏰ CSRD reporting deadline approaching",
    template: "deadline_reminder.html",
    priority: "critical",
    data: ["deadline_date", "days_remaining", "readiness_pct"]
  },
  
  DATA_REVIEW_NEEDED: {
    subject: "👀 Data needs manual review",
    template: "review_needed.html",
    priority: "medium",
    data: ["upload_id", "confidence_score", "review_link"]
  }
};
```

**Email Queue:**
```sql
CREATE TABLE email_queue (
  id UUID PRIMARY KEY,
  company_id UUID REFERENCES companies(id),
  recipient_email VARCHAR(255),
  template_name VARCHAR(50),
  template_data JSON,
  priority VARCHAR(20),
  status VARCHAR(20), -- 'pending', 'sent', 'failed'
  attempts INTEGER DEFAULT 0,
  scheduled_at TIMESTAMP,
  sent_at TIMESTAMP,
  error_message TEXT
);
```

**Processing Logic:**
```python
async def process_email_queue():
    """Process pending emails every minute"""
    pending = get_pending_emails(limit=50)
    
    for email in pending:
        try:
            result = send_email(
                to=email.recipient_email,
                template=email.template_name,
                data=email.template_data
            )
            
            mark_as_sent(email.id, result.message_id)
        
        except Exception as e:
            email.attempts += 1
            if email.attempts >= 3:
                mark_as_failed(email.id, str(e))
                notify_admin(email.id)
            else:
                reschedule(email.id, delay=5 * email.attempts)
```

**API Endpoint:**
```
POST /api/notifications/send
Body: {
  "template": "REPORT_READY",
  "recipient": "user@company.com",
  "data": { "report_type": "CSRD_Full", ... }
}
```

---

### **Agent 9: Audit Trail Agent** 🆕
**Purpose:** Maintain complete traceability for CSRD assurance

**Triggers:**
- Any data change (create, update, delete)
- Any calculation performed
- Any report generated
- Any user action

**Legal Requirement:**
> **CSRD Article 4:** Companies must maintain an audit trail showing:
> - How data was collected
> - Who entered/modified data
> - What calculations were performed
> - Which emission factors were used
> - When reports were generated

**Audit Log Schema:**
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  company_id UUID REFERENCES companies(id),
  event_type VARCHAR(50), -- 'upload', 'calculation', 'correction', 'report'
  actor VARCHAR(100), -- 'user_id' or 'system'
  resource_type VARCHAR(50), -- 'upload', 'emission_result', 'report'
  resource_id UUID,
  action VARCHAR(20), -- 'create', 'update', 'delete'
  before_state JSON,
  after_state JSON,
  reason TEXT,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Make immutable (no updates or deletes allowed)
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;
```

**Events to Log:**
```javascript
const AUDIT_EVENTS = {
  // Data lifecycle
  UPLOAD_CREATED: { type: 'upload', action: 'create' },
  DATA_EXTRACTED: { type: 'extraction', action: 'create' },
  DATA_CORRECTED: { type: 'upload', action: 'update' },
  EMISSION_CALCULATED: { type: 'calculation', action: 'create' },
  
  // Reports
  REPORT_GENERATED: { type: 'report', action: 'create' },
  REPORT_DOWNLOADED: { type: 'report', action: 'access' },
  
  // User actions
  USER_LOGIN: { type: 'auth', action: 'login' },
  COMPANY_APPROVED: { type: 'company', action: 'update' },
  
  // System events
  FACTOR_UPDATED: { type: 'emission_factor', action: 'update' },
  BACKUP_COMPLETED: { type: 'system', action: 'backup' }
};
```

**Example Audit Entry:**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "event_type": "DATA_CORRECTED",
  "actor": "user_123",
  "resource_type": "upload",
  "resource_id": "upload_456",
  "action": "update",
  "before_state": {
    "usage_value": 1250.5,
    "category": "electricity"
  },
  "after_state": {
    "usage_value": 1350.5, // User corrected OCR error
    "category": "electricity"
  },
  "reason": "OCR misread invoice amount",
  "ip_address": "192.168.1.100",
  "created_at": "2025-10-25T10:40:00Z"
}
```

**Audit Trail Export (for external auditors):**
```python
def generate_audit_trail_report(company_id, start_date, end_date):
    """
    Generate comprehensive audit trail for period
    Used for CSRD assurance engagements
    """
    logs = get_audit_logs(
        company_id=company_id,
        start_date=start_date,
        end_date=end_date
    )
    
    report = {
        "company": get_company(company_id),
        "period": {"start": start_date, "end": end_date},
        "summary": {
            "total_events": len(logs),
            "uploads": count_by_type(logs, "upload"),
            "calculations": count_by_type(logs, "calculation"),
            "corrections": count_by_type(logs, "correction"),
            "reports_generated": count_by_type(logs, "report")
        },
        "data_lineage": build_lineage_graph(logs),
        "changes": group_changes(logs),
        "actors": list_unique_actors(logs)
    }
    
    return export_as_pdf(report)
```

**API Endpoints:**
```
GET  /api/audit/logs/:company_id?start=2025-01-01&end=2025-12-31
POST /api/audit/export (generates PDF for auditors)
GET  /api/audit/lineage/:emission_result_id (traces calculation back to source)
```

---

## 🔄 Agent Communication & Orchestration

### **n8n Workflow Example: Upload Processing Pipeline**

```json
{
  "name": "Upload Processing Pipeline",
  "nodes": [
    {
      "id": "1",
      "name": "Webhook: Upload Created",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "upload-created",
        "method": "POST"
      },
      "position": [250, 300]
    },
    {
      "id": "2",
      "name": "Agent 1: Data Intake",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.luma.es/api/agents/data-intake",
        "method": "POST",
        "bodyParameters": {
          "upload_id": "={{$json.upload_id}}"
        }
      },
      "position": [450, 300]
    },
    {
      "id": "3",
      "name": "Check Confidence Score",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$json.confidence_score}}",
              "operation": "larger",
              "value2": 0.7
            }
          ]
        }
      },
      "position": [650, 300]
    },
    {
      "id": "4",
      "name": "Agent 2: Calculate Emissions",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.luma.es/api/agents/calculate-emissions",
        "method": "POST"
      },
      "position": [850, 200]
    },
    {
      "id": "5",
      "name": "Parallel: Update Dashboard & Readiness",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [1050, 200]
    },
    {
      "id": "6",
      "name": "Agent 7: Analytics",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.luma.es/api/agents/analytics"
      },
      "position": [1250, 150]
    },
    {
      "id": "7",
      "name": "Agent 4: CSRD Readiness",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.luma.es/api/agents/csrd-readiness"
      },
      "position": [1250, 250]
    },
    {
      "id": "8",
      "name": "Agent 8: Send Success Email",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.luma.es/api/notifications/send",
        "method": "POST",
        "bodyParameters": {
          "template": "UPLOAD_SUCCESS"
        }
      },
      "position": [1450, 200]
    },
    {
      "id": "9",
      "name": "Flag for Review (Low Confidence)",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.luma.es/api/uploads/flag-review",
        "method": "POST"
      },
      "position": [850, 400]
    },
    {
      "id": "10",
      "name": "Agent 8: Send Review Needed Email",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.luma.es/api/notifications/send",
        "method": "POST",
        "bodyParameters": {
          "template": "DATA_REVIEW_NEEDED"
        }
      },
      "position": [1050, 400]
    }
  ],
  "connections": {
    "Webhook: Upload Created": {
      "main": [[{ "node": "Agent 1: Data Intake" }]]
    },
    "Agent 1: Data Intake": {
      "main": [[{ "node": "Check Confidence Score" }]]
    },
    "Check Confidence Score": {
      "main": [
        [{ "node": "Agent 2: Calculate Emissions" }],
        [{ "node": "Flag for Review (Low Confidence)" }]
      ]
    },
    "Agent 2: Calculate Emissions": {
      "main": [[{ "node": "Parallel: Update Dashboard & Readiness" }]]
    },
    "Parallel: Update Dashboard & Readiness": {
      "main": [
        [{ "node": "Agent 7: Analytics" }],
        [{ "node": "Agent 4: CSRD Readiness" }]
      ]
    },
    "Agent 7: Analytics": {
      "main": [[{ "node": "Agent 8: Send Success Email" }]]
    },
    "Agent 4: CSRD Readiness": {
      "main": [[{ "node": "Agent 8: Send Success Email" }]]
    },
    "Flag for Review (Low Confidence)": {
      "main": [[{ "node": "Agent 8: Send Review Needed Email" }]]
    }
  }
}
```

### **Event Flow Diagram**

```
USER ACTION: Upload Invoice
         ↓
[Supabase Storage] ← File Saved
         ↓
[Webhook] → n8n: "upload.created"
         ↓
[Agent 1: Data Intake]
  │ ├─ OCR Extraction
  │ ├─ Data Normalization
  │ └─ Confidence Check
         ↓
    ┌────┴────┐
    ↓         ↓
HIGH CONF   LOW CONF
    ↓         ↓
[Agent 2]  [Flag Review]
Calc CO2e     ↓
    ↓      [Agent 8]
    ↓      Email Admin
[Parallel Execution]
    ├──────┬──────┐
    ↓      ↓      ↓
[Agent 7] [Agent 4] [Agent 9]
Analytics  CSRD    Audit Log
    └──────┴──────┘
         ↓
    [Agent 8]
  Send Success Email
         ↓
  USER: Email Received
```

---

## 📊 Database Schema (Complete)

```sql
-- ============================================
-- CORE TABLES
-- ============================================

CREATE TABLE companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  sector VARCHAR(100),
  size VARCHAR(20), -- 'SME', 'Large', 'Listed'
  country_code CHAR(2) DEFAULT 'ES',
  material_topics JSON, -- ['E1', 'E2', 'S1']
  contact_email VARCHAR(255),
  approved BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) DEFAULT 'company', -- 'company', 'admin', 'auditor'
  approved BOOLEAN DEFAULT FALSE,
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- DATA INTAKE
-- ============================================

CREATE TABLE uploads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  file_name VARCHAR(255) NOT NULL,
  file_url TEXT NOT NULL,
  file_type VARCHAR(20) NOT NULL, -- 'pdf', 'csv', 'xlsx', 'image'
  file_size_bytes INTEGER,
  
  -- Extraction results
  status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processed', 'failed', 'review_needed'
  confidence_score DECIMAL(5,2),
  extracted_data JSON, -- Raw OCR/parser output
  normalized_data JSON, -- Cleaned and validated data
  
  -- Validation
  validation_status VARCHAR(20), -- 'valid', 'needs_review', 'rejected'
  validation_errors JSON,
  reviewed_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMP,
  
  uploaded_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP
);

-- ============================================
-- EMISSION FACTORS
-- ============================================

CREATE TABLE emission_factors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region VARCHAR(10) NOT NULL, -- 'ES', 'ES-MD', 'FR', 'PT', 'GLOBAL'
  category VARCHAR(50) NOT NULL, -- 'electricity', 'natural_gas', 'diesel', etc.
  scope INTEGER, -- 1, 2, or 3
  
  -- Factor details
  factor_value DECIMAL(15,6) NOT NULL, -- kg CO2e per unit
  unit VARCHAR(20) NOT NULL, -- 'kWh', 'm3', 'L', 'kg', 'km'
  methodology VARCHAR(100), -- 'Market-based', 'Location-based', 'IPCC 2006'
  
  -- Metadata
  source VARCHAR(100) NOT NULL, -- 'MITECO_2025_Q3', 'IPCC_2006'
  source_url TEXT,
  valid_from DATE NOT NULL,
  valid_until DATE,
  
  created_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT unique_factor UNIQUE (region, category, scope, valid_from)
);

CREATE INDEX idx_factors_lookup ON emission_factors(region, category, scope, valid_from, valid_until);

-- ============================================
-- EMISSION CALCULATIONS
-- ============================================

CREATE TABLE emission_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id UUID REFERENCES uploads(id) ON DELETE CASCADE,
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  
  -- Period
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  
  -- Usage data
  category VARCHAR(50) NOT NULL, -- 'electricity', 'natural_gas', etc.
  supplier VARCHAR(255),
  usage_value DECIMAL(15,2) NOT NULL,
  usage_unit VARCHAR(20) NOT NULL,
  
  -- Emission calculation
  scope INTEGER NOT NULL CHECK (scope IN (1, 2, 3)),
  emission_factor DECIMAL(15,6) NOT NULL,
  emission_factor_source VARCHAR(100) NOT NULL,
  co2e_kg DECIMAL(15,2) NOT NULL,
  
  -- Financial
  amount_total DECIMAL(15,2),
  currency VARCHAR(10) DEFAULT 'EUR',
  
  -- Metadata
  calculation_method VARCHAR(100),
  calculated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_emissions_company ON emission_results(company_id, period_start);
CREATE INDEX idx_emissions_scope ON emission_results(company_id, scope);

-- ============================================
-- CSRD READINESS
-- ============================================

CREATE TABLE csrd_readiness (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  
  esrs_module VARCHAR(10) NOT NULL, -- 'E1', 'E2', 'E3', 'E4', 'E5', 'S1-S4', 'G1'
  disclosure_code VARCHAR(20), -- 'E1-1', 'E1-2', etc. (NULL for module-level)
  
  -- Assessment
  required BOOLEAN DEFAULT TRUE, -- Based on materiality
  data_available BOOLEAN DEFAULT FALSE,
  completeness_pct DECIMAL(5,2) DEFAULT 0,
  
  -- Details
  required_fields JSON, -- ['scope1', 'scope2', 'targets']
  available_fields JSON, -- ['scope1', 'scope2']
  missing_items JSON, -- ['targets', 'policies']
  
  last_updated TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT unique_readiness UNIQUE (company_id, esrs_module, disclosure_code)
);

CREATE INDEX idx_readiness_company ON csrd_readiness(company_id);

-- ============================================
-- REPORTS
-- ============================================

CREATE TABLE reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  
  -- Report details
  report_type VARCHAR(50) NOT NULL, -- 'CSRD_Full', 'Carbon_Footprint', 'E1_Module'
  title VARCHAR(255),
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  
  -- ESRS coverage
  esrs_modules JSON, -- ['E1', 'E2', 'S1']
  completeness_score DECIMAL(5,2),
  
  -- Emissions summary
  total_emissions_kg DECIMAL(15,2),
  scope1_kg DECIMAL(15,2),
  scope2_kg DECIMAL(15,2),
  scope3_kg DECIMAL(15,2),
  
  -- Files
  file_url TEXT,
  xbrl_url TEXT, -- EU digital reporting format
  
  -- Generation metadata
  generated_by UUID REFERENCES users(id),
  generated_at TIMESTAMP DEFAULT NOW(),
  version INTEGER DEFAULT 1,
  
  -- Review
  reviewed BOOLEAN DEFAULT FALSE,
  review_score DECIMAL(5,2),
  reviewed_at TIMESTAMP
);

CREATE INDEX idx_reports_company ON reports(company_id, generated_at DESC);

-- ============================================
-- AUDIT TRAIL
-- ============================================

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  
  -- Event details
  event_type VARCHAR(50) NOT NULL, -- 'upload', 'calculation', 'correction', 'report'
  action VARCHAR(20) NOT NULL, -- 'create', 'update', 'delete', 'access'
  
  -- Actor
  actor VARCHAR(100) NOT NULL, -- user_id or 'system'
  actor_role VARCHAR(20), -- 'company', 'admin', 'system'
  
  -- Resource
  resource_type VARCHAR(50) NOT NULL, -- 'upload', 'emission_result', 'report'
  resource_id UUID NOT NULL,
  
  -- State changes
  before_state JSON,
  after_state JSON,
  reason TEXT,
  
  -- Context
  ip_address INET,
  user_agent TEXT,
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- Make audit logs immutable
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;

CREATE INDEX idx_audit_company ON audit_logs(company_id, created_at DESC);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);

-- ============================================
-- NOTIFICATIONS
-- ============================================

CREATE TABLE email_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  
  recipient_email VARCHAR(255) NOT NULL,
  template_name VARCHAR(50) NOT NULL,
  template_data JSON,
  priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
  
  status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'failed'
  attempts INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 3,
  
  scheduled_at TIMESTAMP DEFAULT NOW(),
  sent_at TIMESTAMP,
  failed_at TIMESTAMP,
  error_message TEXT,
  
  message_id VARCHAR(255), -- From email provider
  
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_email_queue_status ON email_queue(status, scheduled_at);

-- ============================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ============================================

-- Dashboard data cache
CREATE MATERIALIZED VIEW company_dashboard_summary AS
SELECT 
  c.id as company_id,
  c.name as company_name,
  
  -- Total emissions
  COALESCE(SUM(er.co2e_kg), 0) as total_emissions_kg,
  COALESCE(SUM(CASE WHEN er.scope = 1 THEN er.co2e_kg ELSE 0 END), 0) as scope1_kg,
  COALESCE(SUM(CASE WHEN er.scope = 2 THEN er.co2e_kg ELSE 0 END), 0) as scope2_kg,
  COALESCE(SUM(CASE WHEN er.scope = 3 THEN er.co2e_kg ELSE 0 END), 0) as scope3_kg,
  
  -- CSRD readiness
  COALESCE(AVG(cr.completeness_pct), 0) as csrd_readiness_pct,
  
  -- Activity
  COUNT(DISTINCT u.id) as total_uploads,
  COUNT(DISTINCT CASE WHEN u.status = 'processed' THEN u.id END) as processed_uploads,
  COUNT(DISTINCT CASE WHEN u.status = 'review_needed' THEN u.id END) as uploads_needing_review,
  
  -- Dates
  MAX(u.uploaded_at) as last_upload_date,
  MAX(er.calculated_at) as last_calculation_date,
  MAX(r.generated_at) as last_report_date,
  
  NOW() as refreshed_at

FROM companies c
LEFT JOIN emission_results er ON c.id = er.company_id
LEFT JOIN csrd_readiness cr ON c.id = cr.company_id
LEFT JOIN uploads u ON c.id = u.company_id
LEFT JOIN reports r ON c.id = r.company_id
GROUP BY c.id, c.name;

CREATE UNIQUE INDEX idx_dashboard_company ON company_dashboard_summary(company_id);

-- Monthly emissions trend
CREATE MATERIALIZED VIEW monthly_emissions AS
SELECT 
  company_id,
  DATE_TRUNC('month', period_start) as month,
  SUM(co2e_kg) as total_co2e_kg,
  SUM(CASE WHEN scope = 1 THEN co2e_kg ELSE 0 END) as scope1_kg,
  SUM(CASE WHEN scope = 2 THEN co2e_kg ELSE 0 END) as scope2_kg,
  SUM(CASE WHEN scope = 3 THEN co2e_kg ELSE 0 END) as scope3_kg,
  COUNT(*) as data_points
FROM emission_results
GROUP BY company_id, DATE_TRUNC('month', period_start);

CREATE INDEX idx_monthly_company ON monthly_emissions(company_id, month DESC);

-- Refresh views (run nightly or after major updates)
-- REFRESH MATERIALIZED VIEW company_dashboard_summary;
-- REFRESH MATERIALIZED VIEW monthly_emissions;
```

---

## 🎯 Implementation Checklist

### **Phase 1: Foundation (Weeks 1-2)**
- [ ] Set up n8n instance (Docker or cloud)
- [ ] Deploy PostgreSQL database (Supabase)
- [ ] Implement database schema
- [ ] Set up file storage (Supabase Storage or S3)
- [ ] Configure Resend email service

### **Phase 2: Core Agents (Weeks 3-5)**
- [ ] **Agent 1:** Data Intake (PDF + CSV extraction)
- [ ] **Agent 3:** Emission Factor Knowledge (hardcoded factors)
- [ ] **Agent 2:** Emission Calculation (basic Scope 1/2)
- [ ] **Agent 9:** Audit Trail (basic logging)
- [ ] **Agent 8:** Notification (email confirmations)

### **Phase 3: Dashboard & Readiness (Weeks 6-7)**
- [ ] **Agent 7:** Analytics & Visualization
- [ ] **Agent 4:** CSRD Readiness (E1 module only)
- [ ] Connect to frontend dashboard
- [ ] Implement real-time updates

### **Phase 4: Reporting (Weeks 8-9)**
- [ ] **Agent 5:** Report Generation (PDF only)
- [ ] Create ESRS E1 template
- [ ] Generate sample reports
- [ ] User testing

### **Phase 5: Intelligence (Weeks 10-11)**
- [ ] **Agent 6:** AI Review (rule-based checks)
- [ ] Implement data quality validations
- [ ] Add CSRD compliance checks
- [ ] (Optional) LLM integration

### **Phase 6: Polish & Scale (Weeks 12-13)**
- [ ] Add full ESRS coverage (E1-G1)
- [ ] Implement XBRL export
- [ ] Optimize database queries
- [ ] Load testing
- [ ] Security audit

---

## 🚀 Next Steps

**To start implementation, you need:**

1. **Environment Setup:**
   - n8n instance URL
   - Supabase project credentials
   - Resend API key
   - Backend API URL (Render)

2. **First Agent to Build:**
   - Start with **Agent 1 (Data Intake)** - foundation for everything
   - Test with sample PDFs and CSVs
   - Validate extraction accuracy

3. **n8n Workflow:**
   - Import the provided JSON workflow
   - Configure webhook URLs
   - Test end-to-end flow

4. **Database:**
   - Run SQL schema in Supabase
   - Seed emission factors (Spain 2025)
   - Create test company

**Would you like me to:**
- Provide detailed code for Agent 1 (Data Intake)?
- Create the complete n8n workflow JSON?
- Design the API endpoints in FastAPI?
- Help with ESRS template structure?

Let me know what to prioritize! 🚀
