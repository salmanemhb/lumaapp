"""
SQLAlchemy database models for Luma
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum


Base = declarative_base()


def generate_uuid():
    """Generate UUID string"""
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    COMPANY = "company"


class Company(Base):
    """Company table - stores company information"""
    __tablename__ = "companies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    sector = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=True)
    approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    uploads = relationship("Upload", back_populates="company", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="company", cascade="all, delete-orphan")


class User(Base):
    """User table - stores user credentials"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    approved = Column(Boolean, default=False, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.COMPANY, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="users")


class UploadStatus(str, enum.Enum):
    """Upload processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class DocumentCategory(str, enum.Enum):
    """Document category enumeration"""
    ELECTRICITY = "electricity"
    NATURAL_GAS = "natural_gas"
    FUEL = "fuel"
    FREIGHT = "freight"
    WATER = "water"
    OTHER = "other"


class Upload(Base):
    """Upload table - stores uploaded files and extracted data"""
    __tablename__ = "uploads"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    # File metadata
    file_name = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    source_type = Column(String(20), nullable=False)  # pdf, csv, xlsx, image
    
    # Extracted data
    supplier = Column(String(255), nullable=True)
    category = Column(SQLEnum(DocumentCategory), nullable=True)
    scope = Column(Integer, nullable=True)  # 1, 2, or 3
    
    # Period & invoice info
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    issue_date = Column(DateTime, nullable=True)
    invoice_number = Column(String(100), nullable=True)
    
    # Usage & emissions
    usage_value = Column(Float, nullable=True)
    usage_unit = Column(String(20), nullable=True)  # kWh, m3, L, km, tkm
    amount_total = Column(Float, nullable=True)
    currency = Column(String(10), default="EUR")
    emission_factor = Column(Float, nullable=True)  # kg CO2e per unit
    co2e_kg = Column(Float, nullable=True)
    vat_rate = Column(Float, nullable=True)
    
    # Processing metadata
    confidence = Column(Float, nullable=True)  # 0-1 score
    status = Column(SQLEnum(UploadStatus), default=UploadStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    meta = Column(Text, nullable=True)  # JSON string for additional data
    
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="uploads")


class Report(Base):
    """Report table - stores generated sustainability reports"""
    __tablename__ = "reports"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    # Report metadata
    title = Column(String(255), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Coverage & metrics
    coverage = Column(Float, nullable=True)  # 0-100 percentage
    total_emissions_kg = Column(Float, nullable=True)
    scope1_kg = Column(Float, nullable=True)
    scope2_kg = Column(Float, nullable=True)
    scope3_kg = Column(Float, nullable=True)
    
    # File
    report_url = Column(Text, nullable=True)
    report_format = Column(String(20), default="pdf")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="reports")
    compliance_metrics = relationship("ComplianceMetric", back_populates="report", cascade="all, delete-orphan")


class ComplianceStatus(str, enum.Enum):
    """CSRD requirement status"""
    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING = "missing"


class ComplianceMetric(Base):
    """Compliance metrics - tracks CSRD/ESRS requirements"""
    __tablename__ = "compliance_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    report_id = Column(String, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    
    requirement_code = Column(String(50), nullable=False)  # e.g., "E1-1"
    requirement_name = Column(String(255), nullable=False)
    status = Column(SQLEnum(ComplianceStatus), default=ComplianceStatus.MISSING, nullable=False)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    report = relationship("Report", back_populates="compliance_metrics")
