"""
File upload and processing routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from supabase import create_client, Client
from datetime import datetime
from pathlib import Path
from typing import List
import uuid
import tempfile
import os

from app.database import get_db
from app.config import settings
from app.models.database import User, Company, Upload, UploadStatus
from app.models.schemas import UploadResponse, UploadRecord
from app.services.auth import get_current_user, get_current_company
from app.services.ocr import DocumentParser

# Import Agent 1 for enhanced extraction
import sys
import re
sys.path.append(str(Path(__file__).parent.parent.parent))

router = APIRouter(prefix="/files", tags=["Files"])

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Upload and process invoice/document
    Accepts: PDF, CSV, XLSX
    Returns: Extracted emission data
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower().replace('.', '')
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Validate file size (in bytes)
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Create upload record (pending)
    upload_record = Upload(
        company_id=current_company.id,
        file_name=file.filename,
        file_url="",  # Will be updated after upload
        source_type=file_ext,
        status=UploadStatus.PENDING
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)
    
    try:
        # Upload to Supabase Storage
        file_content = await file.read()
        storage_path = f"{current_company.id}/{upload_record.id}_{file.filename}"
        
        # Upload file
        supabase.storage.from_("uploads").upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Get public URL
        file_url = supabase.storage.from_("uploads").get_public_url(storage_path)
        
        # Update file URL
        upload_record.file_url = file_url
        upload_record.status = UploadStatus.PROCESSING
        db.commit()
        
        # Save file temporarily for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        
        try:
            # Parse document - now returns List[UploadRecord]
            parsed_records: List[UploadRecord] = DocumentParser.parse_document(tmp_path, file_ext)
            
            # Handle single record vs multiple records
            if len(parsed_records) == 1:
                # Single record - update existing upload_record
                parsed_data = parsed_records[0]
                upload_record.supplier = parsed_data.supplier
                upload_record.category = parsed_data.category
                upload_record.scope = parsed_data.scope
                upload_record.period_start = parsed_data.period_start
                upload_record.period_end = parsed_data.period_end
                upload_record.issue_date = parsed_data.issue_date
                upload_record.invoice_number = parsed_data.invoice_number
                upload_record.usage_value = parsed_data.usage_value
                upload_record.usage_unit = parsed_data.usage_unit
                upload_record.amount_total = parsed_data.amount_total
                upload_record.currency = parsed_data.currency
                upload_record.emission_factor = parsed_data.emission_factor
                upload_record.co2e_kg = parsed_data.co2e_kg
                upload_record.vat_rate = parsed_data.vat_rate
                upload_record.confidence = parsed_data.confidence
                
                # Store extraction details in meta
                meta_dict = parsed_data.meta if isinstance(parsed_data.meta, dict) else {}
                meta_dict['extraction_summary'] = {
                    'fields_extracted': {
                        'supplier': bool(parsed_data.supplier),
                        'invoice_number': bool(parsed_data.invoice_number),
                        'usage_value': bool(parsed_data.usage_value),
                        'amount_total': bool(parsed_data.amount_total),
                        'dates': bool(parsed_data.period_start or parsed_data.issue_date),
                    },
                    'missing_fields': [],
                    'confidence': parsed_data.confidence
                }
                
                # Add missing field warnings
                if not parsed_data.usage_value:
                    meta_dict['extraction_summary']['missing_fields'].append('usage_value')
                if not parsed_data.invoice_number:
                    meta_dict['extraction_summary']['missing_fields'].append('invoice_number')
                if not parsed_data.amount_total:
                    meta_dict['extraction_summary']['missing_fields'].append('amount_total')
                    
                upload_record.meta = str(meta_dict)
                
                # Set status based on confidence
                if parsed_data.confidence and parsed_data.confidence >= 0.6:
                    upload_record.status = UploadStatus.PROCESSED
                else:
                    upload_record.status = UploadStatus.NEEDS_REVIEW
                
                upload_record.processed_at = datetime.utcnow()
                db.commit()
                db.refresh(upload_record)
                
                return_records = [parsed_data]
            
            elif len(parsed_records) > 1:
                # Multiple records - create additional upload entries
                all_uploads = [upload_record]
                
                for idx, parsed_data in enumerate(parsed_records):
                    if idx == 0:
                        # Update first record (existing upload_record)
                        current_upload = upload_record
                    else:
                        # Create new upload records for additional rows/sheets
                        current_upload = Upload(
                            company_id=current_company.id,
                            file_name=file.filename,
                            file_url=file_url,
                            source_type=file_ext,
                            status=UploadStatus.PROCESSING
                        )
                        db.add(current_upload)
                    
                    # Update with parsed data
                    current_upload.supplier = parsed_data.supplier
                    current_upload.category = parsed_data.category
                    current_upload.scope = parsed_data.scope
                    current_upload.period_start = parsed_data.period_start
                    current_upload.period_end = parsed_data.period_end
                    current_upload.issue_date = parsed_data.issue_date
                    current_upload.invoice_number = parsed_data.invoice_number
                    current_upload.usage_value = parsed_data.usage_value
                    current_upload.usage_unit = parsed_data.usage_unit
                    current_upload.amount_total = parsed_data.amount_total
                    current_upload.currency = parsed_data.currency
                    current_upload.emission_factor = parsed_data.emission_factor
                    current_upload.co2e_kg = parsed_data.co2e_kg
                    current_upload.vat_rate = parsed_data.vat_rate
                    current_upload.confidence = parsed_data.confidence
                    current_upload.meta = str(parsed_data.meta) if parsed_data.meta else None
                    
                    # Set status based on confidence
                    if parsed_data.confidence and parsed_data.confidence >= 0.6:
                        current_upload.status = UploadStatus.PROCESSED
                    else:
                        current_upload.status = UploadStatus.NEEDS_REVIEW
                    
                    current_upload.processed_at = datetime.utcnow()
                    
                    if idx > 0:
                        all_uploads.append(current_upload)
                
                db.commit()
                for upload in all_uploads:
                    db.refresh(upload)
                
                return_records = parsed_records
            
            else:
                # No records found
                upload_record.status = UploadStatus.FAILED
                upload_record.error_message = "No valid data extracted"
                db.commit()
                return_records = parsed_records
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        # Return response with info about processed records
        return {
            "file_id": upload_record.id,
            "status": upload_record.status.value,
            "records_processed": len(return_records),
            "total_emissions": sum(r.co2e_kg for r in return_records if r.co2e_kg),
            "message": f"Successfully processed {len(return_records)} record(s)" if return_records else "No valid data found"
        }
    
    except Exception as e:
        # Update status to failed
        upload_record.status = UploadStatus.FAILED
        upload_record.error_message = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.delete("/uploads/clear")
async def clear_all_uploads(
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Clear all uploads for current company
    """
    try:
        # Delete all uploads for the company
        deleted_count = db.query(Upload).filter(
            Upload.company_id == current_company.id
        ).delete()
        
        db.commit()
        
        return {
            "message": f"Successfully deleted {deleted_count} upload(s)",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear uploads: {str(e)}"
        )


@router.get("/uploads")
async def list_uploads(
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    List all uploads for current company
    """
    uploads = db.query(Upload).filter(
        Upload.company_id == current_company.id
    ).order_by(Upload.uploaded_at.desc()).all()
    
    return [
        {
            "file_id": u.id,
            "file_name": u.file_name,
            "status": u.status.value,
            "co2e_kg": u.co2e_kg,
            "uploaded_at": u.uploaded_at.isoformat() if u.uploaded_at else None,
            "supplier": u.supplier,
            "category": u.category.value if u.category else None,
            "confidence": u.confidence
        }
        for u in uploads
    ]


@router.get("/uploads/{file_id}")
async def get_upload_details(
    file_id: str,
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific upload
    """
    upload = db.query(Upload).filter(
        Upload.id == file_id,
        Upload.company_id == current_company.id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    return {
        "file_id": upload.id,
        "file_name": upload.file_name,
        "file_url": upload.file_url,
        "source_type": upload.source_type,
        "supplier": upload.supplier,
        "category": upload.category.value if upload.category else None,
        "scope": upload.scope,
        "period_start": upload.period_start.isoformat() if upload.period_start else None,
        "period_end": upload.period_end.isoformat() if upload.period_end else None,
        "issue_date": upload.issue_date.isoformat() if upload.issue_date else None,
        "invoice_number": upload.invoice_number,
        "usage_value": upload.usage_value,
        "usage_unit": upload.usage_unit,
        "amount_total": upload.amount_total,
        "currency": upload.currency,
        "emission_factor": upload.emission_factor,
        "co2e_kg": upload.co2e_kg,
        "vat_rate": upload.vat_rate,
        "confidence": upload.confidence,
        "status": upload.status.value,
        "uploaded_at": upload.uploaded_at.isoformat() if upload.uploaded_at else None,
        "processed_at": upload.processed_at.isoformat() if upload.processed_at else None,
        "error_message": upload.error_message
    }


@router.delete("/uploads/{file_id}")
async def delete_upload(
    file_id: str,
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Delete an upload (soft delete or remove from storage)
    """
    upload = db.query(Upload).filter(
        Upload.id == file_id,
        Upload.company_id == current_company.id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    # Optionally delete from Supabase Storage
    # (For now, just delete from DB - keeps file in storage)
    
    db.delete(upload)
    db.commit()
    
    return {"message": "Upload deleted successfully", "file_id": file_id}
