"""
Report generation routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile
import os

from app.database import get_db
from app.config import settings
from app.models.database import User, Company, Upload, Report, UploadStatus
from app.models.schemas import GenerateReportRequest, GenerateReportResponse
from app.services.auth import get_current_user, get_current_company
from app.services.email import EmailService
from supabase import create_client, Client

router = APIRouter(prefix="/reports", tags=["Reports"])

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


@router.post("/generate", response_model=GenerateReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Generate sustainability PDF report for specified period
    """
    # Get uploads in period
    uploads = db.query(Upload).filter(
        Upload.company_id == current_company.id,
        Upload.status == UploadStatus.PROCESSED,
        Upload.period_end >= request.period_start,
        Upload.period_end <= request.period_end
    ).all()
    
    # Calculate totals
    total_emissions = sum(u.co2e_kg or 0 for u in uploads)
    scope1_total = sum(u.co2e_kg or 0 for u in uploads if u.scope == 1)
    scope2_total = sum(u.co2e_kg or 0 for u in uploads if u.scope == 2)
    scope3_total = sum(u.co2e_kg or 0 for u in uploads if u.scope == 3)
    
    # Calculate coverage (simplified)
    has_data = len(uploads) > 0
    has_scopes = bool(scope1_total or scope2_total)
    coverage = 50.0 if has_data else 0.0
    if has_scopes:
        coverage += 30.0
    if scope3_total:
        coverage += 20.0
    
    # Generate PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf_path = tmp_file.name
    
    try:
        # Create PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_text = f"Luma – Sustainability Summary<br/>{current_company.name}"
        title = Paragraph(title_text, styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.3 * inch))
        
        # Period
        period_text = f"Period: {request.period_start.strftime('%d/%m/%Y')} - {request.period_end.strftime('%d/%m/%Y')}"
        story.append(Paragraph(period_text, styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Emissions', f'{total_emissions:.2f} kg CO2e'],
            ['Scope 1', f'{scope1_total:.2f} kg CO2e'],
            ['Scope 2', f'{scope2_total:.2f} kg CO2e'],
            ['Scope 3', f'{scope3_total:.2f} kg CO2e'],
            ['CSRD Coverage', f'{coverage:.0f}%'],
            ['Number of Records', str(len(uploads))]
        ]
        
        summary_table = Table(summary_data, colWidths=[3 * inch, 3 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Upload details
        if uploads:
            story.append(Paragraph("Upload Details", styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            
            upload_data = [['Date', 'Supplier', 'Category', 'CO2e (kg)']]
            for u in uploads[:20]:  # Limit to 20 for space
                upload_data.append([
                    u.period_end.strftime('%d/%m/%Y') if u.period_end else 'N/A',
                    u.supplier or 'Unknown',
                    u.category.value if u.category else 'N/A',
                    f'{u.co2e_kg:.2f}' if u.co2e_kg else 'N/A'
                ])
            
            upload_table = Table(upload_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
            upload_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
            ]))
            
            story.append(upload_table)
        
        # Footer
        story.append(Spacer(1, 0.5 * inch))
        footer_text = f"Generated by Luma ESG Platform | {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC"
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Upload to Supabase Storage
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        report_filename = f"report_{current_company.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        storage_path = f"{current_company.id}/reports/{report_filename}"
        
        supabase.storage.from_("reports").upload(
            path=storage_path,
            file=pdf_content,
            file_options={"content-type": "application/pdf"}
        )
        
        report_url = supabase.storage.from_("reports").get_public_url(storage_path)
        
        # Save report record
        report = Report(
            company_id=current_company.id,
            title=f"Sustainability Report {request.period_start.strftime('%B %Y')}",
            period_start=request.period_start,
            period_end=request.period_end,
            coverage=coverage,
            total_emissions_kg=total_emissions,
            scope1_kg=scope1_total,
            scope2_kg=scope2_total,
            scope3_kg=scope3_total,
            report_url=report_url,
            report_format="pdf"
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        # Send email notification
        try:
            EmailService.send_report_ready_email(
                to_email=current_company.contact_email or current_user.email,
                company_name=current_company.name,
                report_url=report_url,
                coverage=coverage,
                language=request.language
            )
        except Exception as e:
            print(f"Failed to send report email: {e}")
        
        return GenerateReportResponse(
            report_id=report.id,
            report_url=report_url,
            coverage=coverage,
            message="Report generated successfully"
        )
    
    finally:
        # Clean up temp file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


@router.get("/list")
async def list_reports(
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    List all generated reports for company
    """
    reports = db.query(Report).filter(
        Report.company_id == current_company.id
    ).order_by(Report.created_at.desc()).all()
    
    return [
        {
            "report_id": r.id,
            "title": r.title,
            "period_start": r.period_start.isoformat() if r.period_start else None,
            "period_end": r.period_end.isoformat() if r.period_end else None,
            "coverage": r.coverage,
            "total_emissions_kg": r.total_emissions_kg,
            "report_url": r.report_url,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in reports
    ]
