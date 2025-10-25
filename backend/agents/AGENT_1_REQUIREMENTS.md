# Agent 1: Data Intake Agent Requirements

## Installation

```bash
cd backend
pip install pdfplumber pytesseract opencv-python pandas openpyxl pillow
```

### Tesseract OCR (for image-based PDFs)

**Windows:**
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to `C:\Program Files\Tesseract-OCR`
3. Add to PATH or set in code:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

## What Agent 1 Does

1. **Receives upload notification** from frontend/n8n
2. **Downloads file** from Supabase Storage
3. **Detects file type** (PDF, CSV, Excel, Image)
4. **Extracts data** using appropriate parser
5. **Normalizes data** to standard format
6. **Calculates confidence score** (OCR quality)
7. **Flags for review** if confidence < 70%
8. **Stores results** in database
9. **Triggers next agent** (Emission Calculation)

## Expected Output Format

```json
{
  "upload_id": "uuid",
  "status": "processed",
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

## Supported File Types

- ✅ PDF (text-based)
- ✅ PDF (image-based with OCR)
- ✅ CSV
- ✅ Excel (.xlsx)
- ✅ Images (JPG, PNG)
