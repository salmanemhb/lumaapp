"""
Agent 1: Data Intake Agent

Purpose: Extract and normalize data from uploaded files (PDF, CSV, Excel, Images)

Triggers:
- User uploads file to dashboard
- File saved to Supabase Storage
- Webhook from n8n

Process:
1. Download file from storage
2. Detect file type
3. Extract data using appropriate parser
4. Normalize to standard format
5. Calculate confidence score
6. Flag for review if needed
7. Store results in database
"""

import os
import tempfile
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json

# PDF Processing
import pdfplumber
import pytesseract
from PIL import Image

# CSV/Excel Processing
import pandas as pd

# Image Processing
import cv2
import numpy as np

# Database
from sqlalchemy import select, update
from app.models.database import Upload, Company
from app.database import get_db

# Supabase Storage
from supabase import create_client, Client
from app.config import settings


class DataIntakeAgent:
    """Agent 1: Extract and normalize data from uploaded files"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        
        # Set tesseract path for Windows
        if os.name == 'nt':  # Windows
            tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    async def process_upload(self, upload_id: str) -> Dict[str, Any]:
        """
        Main entry point: Process an uploaded file
        
        Args:
            upload_id: UUID of the upload record
            
        Returns:
            {
                "status": "processed" | "review_needed" | "failed",
                "confidence_score": 0.0-1.0,
                "extracted_data": {...},
                "error": "..." (if failed)
            }
        """
        try:
            # 1. Fetch upload record from database
            async for db in get_db():
                result = await db.execute(
                    select(Upload).where(Upload.id == upload_id)
                )
                upload = result.scalar_one_or_none()
                
                if not upload:
                    return {"status": "failed", "error": "Upload not found"}
                
                # 2. Download file from Supabase Storage
                file_path = await self._download_file(upload.file_url)
                
                # 3. Detect file type
                file_type = self._detect_file_type(file_path, upload.file_name)
                
                # 4. Extract data based on file type
                extracted_data, confidence = await self._extract_data(
                    file_path, file_type
                )
                
                # 5. Normalize data to standard format
                normalized_data = self._normalize_data(extracted_data)
                
                # 6. Determine status based on confidence
                status = "processed" if confidence >= 0.7 else "review_needed"
                
                # 7. Update database
                await db.execute(
                    update(Upload)
                    .where(Upload.id == upload_id)
                    .values(
                        status=status,
                        confidence_score=confidence,
                        extracted_data=extracted_data,
                        normalized_data=normalized_data,
                        file_type=file_type,
                        processed_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # 8. Clean up temporary file
                os.unlink(file_path)
                
                return {
                    "status": status,
                    "confidence_score": confidence,
                    "extracted_data": normalized_data
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _download_file(self, file_url: str) -> str:
        """Download file from Supabase Storage to temp directory"""
        # Extract bucket and path from URL
        # Example: https://vlecbtkfvwkntlyaluvr.supabase.co/storage/v1/object/public/uploads/company_id/file.pdf
        parts = file_url.split('/storage/v1/object/public/')
        if len(parts) != 2:
            raise ValueError(f"Invalid file URL: {file_url}")
        
        bucket_and_path = parts[1].split('/', 1)
        bucket = bucket_and_path[0]
        file_path = bucket_and_path[1]
        
        # Download file
        response = self.supabase.storage.from_(bucket).download(file_path)
        
        # Save to temp file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"luma_{os.path.basename(file_path)}")
        
        with open(temp_path, 'wb') as f:
            f.write(response)
        
        return temp_path
    
    def _detect_file_type(self, file_path: str, file_name: str) -> str:
        """Detect file type from extension and content"""
        ext = Path(file_name).suffix.lower()
        
        type_mapping = {
            '.pdf': 'pdf',
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image'
        }
        
        return type_mapping.get(ext, 'unknown')
    
    async def _extract_data(self, file_path: str, file_type: str) -> Tuple[Dict, float]:
        """
        Extract data based on file type
        
        Returns:
            (extracted_data, confidence_score)
        """
        if file_type == 'pdf':
            return self._extract_from_pdf(file_path)
        elif file_type == 'csv':
            return self._extract_from_csv(file_path)
        elif file_type == 'excel':
            return self._extract_from_excel(file_path)
        elif file_type == 'image':
            return self._extract_from_image(file_path)
        else:
            return {}, 0.0
    
    def _extract_from_pdf(self, file_path: str) -> Tuple[Dict, float]:
        """Extract data from PDF using pdfplumber + OCR fallback"""
        data = {}
        confidence = 0.0
        
        try:
            with pdfplumber.open(file_path) as pdf:
                # Try text extraction first (for native PDFs)
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                
                if text.strip():
                    # Native PDF with selectable text
                    data = self._parse_invoice_text(text)
                    confidence = 0.95  # High confidence for native PDFs
                else:
                    # Image-based PDF, use OCR
                    for page in pdf.pages:
                        image = page.to_image(resolution=300)
                        pil_image = image.original
                        
                        # Run OCR
                        ocr_data = pytesseract.image_to_data(
                            pil_image, 
                            output_type=pytesseract.Output.DICT
                        )
                        
                        # Calculate OCR confidence
                        confidences = [
                            int(conf) for conf in ocr_data['conf'] 
                            if conf != '-1'
                        ]
                        confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.0
                        
                        # Extract text
                        text = pytesseract.image_to_string(pil_image)
                        data = self._parse_invoice_text(text)
                        
                        break  # Only process first page for now
        
        except Exception as e:
            print(f"PDF extraction error: {e}")
            data = {"error": str(e)}
            confidence = 0.0
        
        return data, confidence
    
    def _extract_from_csv(self, file_path: str) -> Tuple[Dict, float]:
        """Extract data from CSV file"""
        try:
            df = pd.read_csv(file_path)
            
            # Convert to dict (first row as sample)
            data = df.iloc[0].to_dict() if len(df) > 0 else {}
            
            # CSV is structured data, high confidence
            confidence = 1.0
            
            return data, confidence
        
        except Exception as e:
            print(f"CSV extraction error: {e}")
            return {"error": str(e)}, 0.0
    
    def _extract_from_excel(self, file_path: str) -> Tuple[Dict, float]:
        """Extract data from Excel file"""
        try:
            df = pd.read_excel(file_path, sheet_name=0)
            
            # Convert to dict (first row as sample)
            data = df.iloc[0].to_dict() if len(df) > 0 else {}
            
            # Excel is structured data, high confidence
            confidence = 1.0
            
            return data, confidence
        
        except Exception as e:
            print(f"Excel extraction error: {e}")
            return {"error": str(e)}, 0.0
    
    def _extract_from_image(self, file_path: str) -> Tuple[Dict, float]:
        """Extract data from image using OCR"""
        try:
            # Load image
            image = Image.open(file_path)
            
            # Preprocess image for better OCR
            image = self._preprocess_image(image)
            
            # Run OCR with confidence scores
            ocr_data = pytesseract.image_to_data(
                image, 
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [
                int(conf) for conf in ocr_data['conf'] 
                if conf != '-1'
            ]
            confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.0
            
            # Extract text
            text = pytesseract.image_to_string(image)
            data = self._parse_invoice_text(text)
            
            return data, confidence
        
        except Exception as e:
            print(f"Image extraction error: {e}")
            return {"error": str(e)}, 0.0
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert PIL to OpenCV
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Threshold
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL
        return Image.fromarray(thresh)
    
    def _parse_invoice_text(self, text: str) -> Dict[str, Any]:
        """
        Parse invoice text to extract key fields
        
        This is a simple pattern-matching approach.
        For production, consider using:
        - spaCy NER (Named Entity Recognition)
        - Fine-tuned BERT model
        - GPT-4 Vision API
        """
        import re
        
        data = {}
        text_lower = text.lower()
        
        # Detect supplier
        if 'iberdrola' in text_lower:
            data['supplier'] = 'Iberdrola'
        elif 'endesa' in text_lower:
            data['supplier'] = 'Endesa'
        elif 'naturgy' in text_lower:
            data['supplier'] = 'Naturgy'
        elif 'repsol' in text_lower:
            data['supplier'] = 'Repsol'
        
        # Detect category
        if any(keyword in text_lower for keyword in ['electricidad', 'electricity', 'kwh']):
            data['category'] = 'electricity'
        elif any(keyword in text_lower for keyword in ['gas natural', 'natural gas', 'm3', 'm³']):
            data['category'] = 'natural_gas'
        elif any(keyword in text_lower for keyword in ['gasoil', 'diesel', 'gasóleo']):
            data['category'] = 'diesel'
        
        # Extract consumption (e.g., "1.250,5 kWh" or "1250.5 kWh")
        kwh_pattern = r'([\d.,]+)\s*kwh'
        kwh_match = re.search(kwh_pattern, text_lower)
        if kwh_match:
            usage_str = kwh_match.group(1).replace('.', '').replace(',', '.')
            try:
                data['usage_value'] = float(usage_str)
                data['usage_unit'] = 'kWh'
            except:
                pass
        
        # Extract m3 for gas
        m3_pattern = r'([\d.,]+)\s*m[³3]'
        m3_match = re.search(m3_pattern, text_lower)
        if m3_match:
            usage_str = m3_match.group(1).replace('.', '').replace(',', '.')
            try:
                data['usage_value'] = float(usage_str)
                data['usage_unit'] = 'm3'
            except:
                pass
        
        # Extract total amount (e.g., "Total: 185,75 €")
        amount_pattern = r'total[:\s]*([\d.,]+)\s*€'
        amount_match = re.search(amount_pattern, text_lower)
        if amount_match:
            amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
            try:
                data['amount_total'] = float(amount_str)
                data['currency'] = 'EUR'
            except:
                pass
        
        # Extract dates (e.g., "01/09/2025" or "September 2025")
        date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        dates = re.findall(date_pattern, text)
        if dates:
            # Assume first date is period_start
            day, month, year = dates[0]
            data['period_start'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # If second date exists, use as period_end
            if len(dates) > 1:
                day, month, year = dates[1]
                data['period_end'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Extract invoice number
        invoice_pattern = r'factura[:\s#]*([a-z0-9-]+)'
        invoice_match = re.search(invoice_pattern, text_lower)
        if invoice_match:
            data['invoice_number'] = invoice_match.group(1).upper()
        
        return data
    
    def _normalize_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize extracted data to standard format
        
        Output format:
        {
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
        """
        normalized = {}
        
        # Required fields
        required_fields = [
            'supplier', 'category', 'usage_value', 'usage_unit'
        ]
        
        # Copy fields if present
        for field in required_fields:
            if field in extracted_data:
                normalized[field] = extracted_data[field]
        
        # Optional fields
        optional_fields = [
            'period_start', 'period_end', 'amount_total', 
            'currency', 'invoice_number'
        ]
        
        for field in optional_fields:
            if field in extracted_data:
                normalized[field] = extracted_data[field]
        
        # Set defaults
        if 'currency' not in normalized:
            normalized['currency'] = 'EUR'
        
        return normalized


# ============================================
# FastAPI Endpoint
# ============================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/agents/data-intake", tags=["Agent 1"])

class ProcessUploadRequest(BaseModel):
    upload_id: str

class ProcessUploadResponse(BaseModel):
    status: str
    confidence_score: Optional[float] = None
    extracted_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("", response_model=ProcessUploadResponse)
async def process_upload(request: ProcessUploadRequest):
    """
    Agent 1: Process uploaded file
    
    Extracts data from PDF, CSV, Excel, or Image files.
    """
    agent = DataIntakeAgent()
    result = await agent.process_upload(request.upload_id)
    
    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))
    
    return ProcessUploadResponse(**result)
