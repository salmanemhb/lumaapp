"""
Dashboard and reporting routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import List, Dict
from calendar import month_abbr

from app.database import get_db
from app.models.database import User, Company, Upload, Report, ComplianceMetric, UploadStatus, ComplianceStatus
from app.models.schemas import (
    DashboardResponse, DashboardKPIs, DashboardTrend, DashboardScopePie,
    ReportSummaryResponse, ComplianceRequirement, UploadListItem
)
from app.services.auth import get_current_user, get_current_company

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def calculate_csrd_coverage(db: Session, company_id: str) -> float:
    """
    Calculate CSRD/ESRS E1 coverage percentage
    Based on available data fields from uploads
    """
    # Check what data we have
    uploads = db.query(Upload).filter(
        Upload.company_id == company_id,
        Upload.status == UploadStatus.PROCESSED
    ).all()
    
    if not uploads:
        return 0.0
    
    # Requirements checklist (simplified for MVP)
    requirements = {
        "has_scope1": False,
        "has_scope2": False,
        "has_scope3": False,
        "has_energy_data": False,
        "has_period_coverage": False,
        "has_emission_factors": False
    }
    
    for upload in uploads:
        if upload.scope == 1:
            requirements["has_scope1"] = True
        if upload.scope == 2:
            requirements["has_scope2"] = True
        if upload.scope == 3:
            requirements["has_scope3"] = True
        if upload.usage_value and upload.usage_unit:
            requirements["has_energy_data"] = True
        if upload.period_start and upload.period_end:
            requirements["has_period_coverage"] = True
        if upload.emission_factor:
            requirements["has_emission_factors"] = True
    
    # Calculate percentage
    completed = sum(1 for v in requirements.values() if v)
    total = len(requirements)
    
    return round((completed / total) * 100, 1)


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Get dashboard data with KPIs, trends, and recent uploads
    """
    # Get all processed uploads
    uploads = db.query(Upload).filter(
        Upload.company_id == current_company.id,
        Upload.status == UploadStatus.PROCESSED
    ).all()
    
    # Calculate total emissions by scope
    total_emissions = 0.0
    scope1_total = 0.0
    scope2_total = 0.0
    scope3_total = 0.0
    
    for upload in uploads:
        if upload.co2e_kg:
            total_emissions += upload.co2e_kg
            
            if upload.scope == 1:
                scope1_total += upload.co2e_kg
            elif upload.scope == 2:
                scope2_total += upload.co2e_kg
            elif upload.scope == 3:
                scope3_total += upload.co2e_kg
    
    # Calculate coverage
    coverage = calculate_csrd_coverage(db, current_company.id)
    
    # KPIs
    kpis = DashboardKPIs(
        total_emissions_kg=round(total_emissions, 2),
        scope1_kg=round(scope1_total, 2),
        scope2_kg=round(scope2_total, 2),
        scope3_kg=round(scope3_total, 2),
        coverage_pct=coverage
    )
    
    # Trend data (last 6 months)
    now = datetime.utcnow()
    months_data = {}
    
    for i in range(6):
        month_date = now - timedelta(days=30 * i)
        month_key = month_date.strftime("%b")
        months_data[month_key] = 0.0
    
    # Aggregate emissions by month
    for upload in uploads:
        if upload.period_end:
            month_key = upload.period_end.strftime("%b")
            if month_key in months_data and upload.co2e_kg:
                months_data[month_key] += upload.co2e_kg
    
    # Reverse to show oldest first
    months_list = list(reversed(list(months_data.keys())))
    values_list = [round(months_data[m], 2) for m in months_list]
    
    trend = DashboardTrend(
        months=months_list,
        values_kg=values_list
    )
    
    # Scope pie chart
    scope_pie = DashboardScopePie(
        scope1=round(scope1_total, 2),
        scope2=round(scope2_total, 2),
        scope3=round(scope3_total, 2)
    )
    
    # Recent uploads (last 10)
    recent_uploads = db.query(Upload).filter(
        Upload.company_id == current_company.id
    ).order_by(Upload.uploaded_at.desc()).limit(10).all()
    
    uploads_list = [
        UploadListItem(
            file_id=u.id,
            file_name=u.file_name,
            status=u.status.value,
            co2e_kg=u.co2e_kg,
            uploaded_at=u.uploaded_at.isoformat() if u.uploaded_at else "",
            supplier=u.supplier,
            category=u.category.value if u.category else None
        )
        for u in recent_uploads
    ]
    
    return DashboardResponse(
        kpis=kpis,
        trend=trend,
        scope_pie=scope_pie,
        uploads=uploads_list
    )


@router.get("/summary", response_model=ReportSummaryResponse)
async def get_report_summary(
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Get CSRD compliance summary with requirement breakdown
    """
    coverage = calculate_csrd_coverage(db, current_company.id)
    
    # Check requirements
    uploads = db.query(Upload).filter(
        Upload.company_id == current_company.id,
        Upload.status == UploadStatus.PROCESSED
    ).all()
    
    has_scope1 = any(u.scope == 1 for u in uploads)
    has_scope2 = any(u.scope == 2 for u in uploads)
    has_scope3 = any(u.scope == 3 for u in uploads)
    has_energy = any(u.usage_value and u.usage_unit for u in uploads)
    has_factors = any(u.emission_factor for u in uploads)
    
    requirements = [
        ComplianceRequirement(
            id="E1-1",
            name="Scope 1, 2, 3 GHG Emissions",
            status=ComplianceStatus.COMPLETE if (has_scope1 and has_scope2) else 
                   ComplianceStatus.PARTIAL if (has_scope1 or has_scope2) else 
                   ComplianceStatus.MISSING
        ),
        ComplianceRequirement(
            id="E1-2",
            name="Energy Consumption",
            status=ComplianceStatus.COMPLETE if has_energy else ComplianceStatus.MISSING
        ),
        ComplianceRequirement(
            id="E1-3",
            name="Emission Intensity (tCO2e/€)",
            status=ComplianceStatus.PARTIAL if (has_energy and has_factors) else ComplianceStatus.MISSING
        ),
        ComplianceRequirement(
            id="E1-4",
            name="Scope 3 Coverage",
            status=ComplianceStatus.COMPLETE if has_scope3 else ComplianceStatus.MISSING
        )
    ]
    
    return ReportSummaryResponse(
        coverage=coverage,
        requirements=requirements
    )
