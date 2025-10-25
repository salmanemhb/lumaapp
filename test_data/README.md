# Test Data for Agent 1

## Available Test Files

### 1. `sample_invoice_iberdrola.txt`
- **Type:** Electricity invoice
- **Supplier:** Iberdrola
- **Customer:** ZARA retail
- **Consumption:** 2,450 kWh
- **Period:** September 2025
- **Amount:** 524.39 EUR
- **Format:** Plain text (simulates OCR extracted text)

### 2. `sample_invoice_gas.csv`
- **Type:** Natural gas invoice
- **Supplier:** Gas Natural Fenosa
- **Customer:** ZARA retail
- **Consumption:** 850 m³
- **Period:** September 2025
- **Amount:** 1,245.80 EUR
- **Format:** CSV

## How to Test

### Option A: Via Frontend (Recommended)
1. Log in to https://getluma.es with test credentials
2. Navigate to Upload section
3. Upload one of these test files
4. Wait for Agent 1 to process
5. Check extracted data

### Option B: Via API (Direct)
1. Upload file to Supabase Storage first
2. Create upload record in database
3. Call Agent 1 endpoint:
```bash
POST https://luma-final.onrender.com/api/agents/data-intake
{
  "upload_id": "your-upload-uuid"
}
```

### Option C: Via Swagger UI
1. Open https://luma-final.onrender.com/docs
2. Find POST /api/agents/data-intake
3. Click "Try it out"
4. Enter upload_id and execute

## Expected Results

### Iberdrola Invoice
```json
{
  "status": "processed",
  "confidence_score": 0.95,
  "extracted_data": {
    "supplier": "IBERDROLA CLIENTES, S.A.U.",
    "category": "electricity",
    "usage_value": 2450,
    "usage_unit": "kWh",
    "amount_total": 524.39,
    "currency": "EUR",
    "period_start": "2025-09-01",
    "period_end": "2025-09-30",
    "invoice_number": "2025/10/001234"
  }
}
```

### Gas Invoice CSV
```json
{
  "status": "processed",
  "confidence_score": 1.0,
  "extracted_data": {
    "supplier": "Gas Natural Fenosa",
    "category": "natural_gas",
    "usage_value": 850,
    "usage_unit": "m3",
    "amount_total": 1245.80,
    "currency": "EUR",
    "period_start": "2025-09-01",
    "period_end": "2025-09-30"
  }
}
```

## Next Steps After Testing

Once Agent 1 successfully extracts data:
1. **Agent 2** will calculate emissions using emission_factors
2. **Expected emission calculation** for electricity: 2,450 kWh × 0.215 kg/kWh = 526.75 kg CO2e (Scope 2)
3. **Expected emission calculation** for gas: 850 m³ × 2.016 kg/m³ = 1,713.60 kg CO2e (Scope 1)
