"""
Agent endpoints for n8n workflow integration
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import sys
from pathlib import Path

# Add agents directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.ocr import DocumentParser
from app.config import settings
import httpx

router = APIRouter(prefix="/agents", tags=["Agents"])


class ExtractRequest(BaseModel):
    upload_id: str
    company_id: str


class CalculateRequest(BaseModel):
    upload_id: str


class FlagReviewRequest(BaseModel):
    upload_id: str
    confidence: float
    reason: str


@router.post("/extract")
async def agent_extract(data: ExtractRequest):
    """
    Agent 1: Extract data from uploaded file
    Called by n8n workflow after file upload
    """
    from supabase import create_client
    
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    # Get upload record
    response = supabase.table('upload').select('*').eq('id', data.upload_id).single().execute()
    upload = response.data
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Download file from storage
    file_path = upload['file_url']
    storage_response = supabase.storage.from_('uploads').download(file_path)
    
    # Save temporarily
    temp_path = f"/tmp/{upload['filename']}"
    with open(temp_path, 'wb') as f:
        f.write(storage_response)
    
    # Parse document
    parser = DocumentParser()
    records = parser.parse_document(temp_path)
    
    if not records or len(records) == 0:
        raise HTTPException(status_code=400, detail="Failed to parse document")
    
    # For now, handle single record (first record if multiple)
    record = records[0]
    
    # Update database with extracted data
    update_data = {
        'supplier': record.supplier,
        'category': record.category,
        'usage_value': record.usage_value,
        'usage_unit': record.usage_unit,
        'invoice_number': record.invoice_number,
        'amount_total': record.amount_total,
        'confidence': record.confidence,
        'status': 'extracted',
        'meta': record.meta
    }
    
    supabase.table('upload').update(update_data).eq('id', data.upload_id).execute()
    
    # Return data for n8n to use in next steps
    return {
        "upload_id": data.upload_id,
        "confidence_score": record.confidence,
        "supplier": record.supplier,
        "category": record.category,
        "usage_value": record.usage_value,
        "usage_unit": record.usage_unit,
        "filename": upload['filename'],
        "user_email": upload.get('user_email', 'user@example.com')
    }


@router.post("/calculate")
async def agent_calculate(data: CalculateRequest):
    """
    Agent 2: Calculate emissions from extracted data
    Called by n8n after successful extraction
    """
    from supabase import create_client
    
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    # Get upload record
    response = supabase.table('upload').select('*').eq('id', data.upload_id).single().execute()
    upload = response.data
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Calculate emissions based on category
    usage_value = upload.get('usage_value')
    category = upload.get('category')
    
    if not usage_value or not category:
        raise HTTPException(status_code=400, detail="Missing usage_value or category")
    
    # Apply emission factors
    co2e_kg = 0.0
    if category == 'electricity':
        co2e_kg = usage_value * settings.ELECTRICITY_FACTOR_KG_PER_KWH
    elif category == 'natural_gas' or category == 'gas':
        co2e_kg = usage_value * settings.GAS_FACTOR_KG_PER_M3
    elif category == 'fuel':
        co2e_kg = usage_value * settings.DIESEL_FACTOR_KG_PER_L
    elif category == 'freight':
        # Simplified calculation (would need weight in real scenario)
        co2e_kg = usage_value * 0.1  # placeholder
    
    # Update database
    supabase.table('upload').update({
        'co2e_kg': co2e_kg,
        'status': 'processed'
    }).eq('id', data.upload_id).execute()
    
    return {
        "upload_id": data.upload_id,
        "co2e_kg": co2e_kg,
        "filename": upload['filename'],
        "supplier": upload.get('supplier'),
        "user_email": upload.get('user_email', 'user@example.com'),
        "confidence_score": upload.get('confidence', 0) * 100
    }


@router.post("/flag-review")
async def agent_flag_review(data: FlagReviewRequest):
    """
    Agent 6: Flag upload for manual review
    Called by n8n when confidence is below threshold
    """
    from supabase import create_client
    
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    # Update status to review_needed
    supabase.table('upload').update({
        'status': 'review_needed',
        'review_reason': data.reason,
        'confidence': data.confidence
    }).eq('id', data.upload_id).execute()
    
    # TODO: Send notification to admin/reviewer
    # Could integrate with Slack, email, or internal notification system
    
    return {
        "upload_id": data.upload_id,
        "status": "flagged_for_review",
        "reason": data.reason
    }


@router.post("/trigger-workflow")
async def trigger_n8n_workflow(upload_id: str, company_id: str):
    """
    Utility endpoint to trigger n8n workflow
    Called from upload endpoint
    """
    if not settings.N8N_WEBHOOK_URL:
        raise HTTPException(status_code=500, detail="n8n webhook URL not configured")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                settings.N8N_WEBHOOK_URL,
                json={
                    "upload_id": upload_id,
                    "company_id": company_id
                },
                headers={
                    "X-N8N-Secret": settings.N8N_WEBHOOK_SECRET
                } if settings.N8N_WEBHOOK_SECRET else {},
                timeout=10.0
            )
            return {"status": "triggered", "n8n_response": response.status_code}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to trigger n8n: {str(e)}")
