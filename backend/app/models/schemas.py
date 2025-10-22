"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ===== Enums =====

class UserRole(str, Enum):
    ADMIN = "admin"
    COMPANY = "company"


class UploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class DocumentCategory(str, Enum):
    ELECTRICITY = "electricity"
    NATURAL_GAS = "natural_gas"
    FUEL = "fuel"
    FREIGHT = "freight"
    WATER = "water"
    OTHER = "other"


class ComplianceStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING = "missing"


# ===== Auth Schemas =====

class SignupRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    contact_email: EmailStr
    sector: Optional[str] = None


class SignupResponse(BaseModel):
    message: str
    company_id: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class TokenData(BaseModel):
    user_id: str
    company_id: str
    email: str
    role: UserRole


# ===== Upload Schemas =====

class UploadRecord(BaseModel):
    """Normalized extraction record"""
    supplier: Optional[str] = None
    category: Optional[DocumentCategory] = None
    scope: Optional[int] = Field(None, ge=1, le=3)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    issue_date: Optional[datetime] = None
    invoice_number: Optional[str] = None
    usage_value: Optional[float] = None
    usage_unit: Optional[str] = None
    amount_total: Optional[float] = None
    emission_factor: Optional[float] = None
    co2e_kg: Optional[float] = None
    currency: str = "EUR"
    vat_rate: Optional[float] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    meta: Optional[Dict[str, Any]] = None


class UploadResponse(BaseModel):
    file_id: str
    status: UploadStatus
    record: Optional[UploadRecord] = None
    error_message: Optional[str] = None


class UploadListItem(BaseModel):
    """Upload item for dashboard list"""
    file_id: str
    file_name: str
    status: str
    co2e_kg: Optional[float] = None
    uploaded_at: str
    supplier: Optional[str] = None
    category: Optional[str] = None


# ===== Dashboard Schemas =====

class DashboardKPIs(BaseModel):
    total_emissions_kg: float
    scope1_kg: float
    scope2_kg: float
    scope3_kg: float
    coverage_pct: float


class DashboardTrend(BaseModel):
    months: List[str]
    values_kg: List[float]


class DashboardScopePie(BaseModel):
    scope1: float
    scope2: float
    scope3: float


class DashboardResponse(BaseModel):
    kpis: DashboardKPIs
    trend: DashboardTrend
    scope_pie: DashboardScopePie
    uploads: List[UploadListItem]


# ===== Report Schemas =====

class ComplianceRequirement(BaseModel):
    id: str
    name: str
    status: ComplianceStatus


class ReportSummaryResponse(BaseModel):
    coverage: float
    requirements: List[ComplianceRequirement]


class GenerateReportRequest(BaseModel):
    period_start: datetime
    period_end: datetime
    language: str = "en"  # en or es


class GenerateReportResponse(BaseModel):
    report_id: str
    report_url: str
    coverage: float
    message: str


# ===== Company Approval (Admin) =====

class ApprovalRequest(BaseModel):
    company_name: str
    user_email: EmailStr
    password: Optional[str] = None  # If not provided, will be auto-generated


class ApprovalResponse(BaseModel):
    success: bool
    message: str
    credentials: Optional[Dict[str, str]] = None
