# Multi-Sheet Test File Documentation

## File: `multi_sheet_invoices_12.xlsx`

**Total Sheets:** 12  
**Total Invoice Rows:** 146  
**Purpose:** Test Agent 1's ability to process multiple sheets and multiple rows per sheet

---

## Sheet Breakdown

### 1. **Jan_Electricity** (8 rows)
- **Supplier:** Iberdrola
- **Category:** Electricity
- **Unit:** kWh
- **Consumption Range:** 2,450 - 3,450 kWh
- **Expected Emissions:** ~6,530 kg CO₂e (using 0.231 kg/kWh)
- **Invoice Numbers:** IBE-2024-01-001 to IBE-2024-01-008

### 2. **Jan_Gas** (10 rows)
- **Supplier:** Naturgy
- **Category:** Natural Gas
- **Unit:** m³
- **Consumption Range:** 780 - 950 m³
- **Expected Emissions:** ~17,293 kg CO₂e (using 2.016 kg/m³)
- **Invoice Numbers:** NAT-2024-01-001 to NAT-2024-01-010

### 3. **Feb_Electricity** (6 rows)
- **Supplier:** Endesa
- **Category:** Electricity
- **Unit:** kWh
- **Consumption Range:** 2,650 - 3,120 kWh
- **Expected Emissions:** ~3,826 kg CO₂e
- **Invoice Numbers:** END-2024-02-001 to END-2024-02-006

### 4. **Feb_Fuel** (12 rows)
- **Supplier:** Repsol
- **Category:** Fuel (Diesel)
- **Unit:** liters
- **Consumption Range:** 450 - 550 liters
- **Expected Emissions:** ~16,104 kg CO₂e (using 2.68 kg/L)
- **Invoice Numbers:** REP-2024-02-001 to REP-2024-02-012

### 5. **Mar_Electricity** (9 rows)
- **Suppliers:** Mixed (Iberdrola & Endesa)
- **Category:** Electricity
- **Unit:** kWh
- **Consumption Range:** 2,750 - 3,250 kWh
- **Expected Emissions:** ~6,619 kg CO₂e
- **Invoice Numbers:** MIX-2024-03-001 to MIX-2024-03-009

### 6. **Mar_Gas** (15 rows)
- **Supplier:** Naturgy
- **Category:** Natural Gas
- **Unit:** m³
- **Consumption Range:** 690 - 850 m³
- **Expected Emissions:** ~23,650 kg CO₂e
- **Invoice Numbers:** NAT-2024-03-001 to NAT-2024-03-015

### 7. **Q1_Freight** (13 rows)
- **Supplier:** DHL
- **Category:** Freight
- **Unit:** tkm (ton-kilometers)
- **Consumption Range:** 1,250 - 1,670 tkm
- **Expected Emissions:** ~1,195 kg CO₂e (using 0.062 kg/tkm)
- **Invoice Numbers:** DHL-2024-Q1-001 to DHL-2024-Q1-013

### 8. **Q1_Summary** (4 rows)
- **Purpose:** Quarterly summary data
- **Categories:** Electricity, Gas Natural, Combustible, Transporte
- **Note:** This is aggregated data, not individual invoices
- **Contains:** Pre-calculated total emissions

### 9. **Apr_Mixed_1** (18 rows)
- **Suppliers:** Iberdrola (9) + Naturgy (9)
- **Categories:** Electricity + Natural Gas
- **Mixed Units:** kWh + m³
- **Expected Emissions:** ~20,602 kg CO₂e
- **Invoice Numbers:** APR-ELE-001 to APR-GAS-009

### 10. **May_Mixed_2** (20 rows)
- **Suppliers:** Repsol (10) + Cepsa (10)
- **Category:** Fuel (Diesel)
- **Unit:** liters
- **Consumption Range:** 460 - 540 liters
- **Expected Emissions:** ~27,176 kg CO₂e
- **Invoice Numbers:** MAY-REP-001 to MAY-CEP-010

### 11. **Jun_All_Types** (25 rows)
- **Suppliers:** Iberdrola, Endesa, Naturgy, Repsol, DHL (5 each)
- **Categories:** ALL types (Electricity, Gas, Fuel, Freight)
- **Mixed Units:** kWh, m³, l, tkm
- **Expected Emissions:** ~15,297 kg CO₂e
- **Invoice Numbers:** JUN-A-001 to JUN-E-005 (organized by category)

### 12. **H1_2024_Analysis** (6 rows)
- **Purpose:** Half-year monthly summary
- **Months:** Enero to Junio (January to June)
- **Note:** Contains pre-calculated totals per month
- **Contains:** Month-by-month breakdown of all categories

---

## Expected Test Results

### Total Expected Database Records
**146 Upload records** (one for each invoice row across all sheets)

### Expected Emissions by Category
- **Electricity:** ~17,000 kg CO₂e (23 + 6 + 9 + 9 + 10 invoices = 67,610 kWh × 0.231)
- **Natural Gas:** ~40,940 kg CO₂e (10 + 15 + 9 invoices = 20,305 m³ × 2.016)
- **Fuel:** ~43,280 kg CO₂e (12 + 20 invoices = 16,145 liters × 2.68)
- **Freight:** ~1,195 kg CO₂e (13 invoices = 19,280 tkm × 0.062)

**Grand Total:** ~102,415 kg CO₂e (102.4 tonnes)

### Dashboard Verification
After uploading this file, the dashboard should show:
- **Total Uploads:** 146 files
- **Total Emissions:** ~102.4 tonnes CO₂e
- **Scope 1:** ~84,220 kg (Gas + Fuel)
- **Scope 2:** ~17,000 kg (Electricity)
- **Scope 3:** ~1,195 kg (Freight)

### Suppliers in Recent Uploads Table
- Iberdrola (17 invoices)
- Naturgy (34 invoices)
- Endesa (11 invoices)
- Repsol (22 invoices)
- Cepsa (10 invoices)
- DHL (18 invoices)

---

## Test Scenarios Covered

✅ **Multi-Sheet Processing** - 12 different sheets  
✅ **Multi-Row Processing** - Up to 25 rows per sheet  
✅ **Mixed Suppliers** - 6 different suppliers  
✅ **All Categories** - Electricity, Gas, Fuel, Freight  
✅ **All Units** - kWh, m³, liters, tkm  
✅ **All Scopes** - Scope 1, 2, and 3  
✅ **Date Ranges** - 6 months (Jan-Jun 2024)  
✅ **Invoice Numbering** - Diverse formats (IBE, NAT, END, REP, etc.)

---

## How to Test

1. **Upload file via dashboard:**
   ```
   Navigate to https://getluma.es/dashboard
   Click "Upload" or drag file to upload area
   Select: test_data/multi_sheet_invoices_12.xlsx
   ```

2. **Expected backend behavior:**
   - Agent 1 reads all 12 sheets
   - Processes 146 total rows
   - Creates 146 separate Upload records in database
   - Calculates emissions for each record
   - Sets status to PROCESSED (confidence ≥ 60%)

3. **Verify in database:**
   ```sql
   SELECT COUNT(*) FROM uploads WHERE company_id = 'YOUR_COMPANY_ID';
   -- Should return: 146

   SELECT SUM(co2e_kg) FROM uploads WHERE company_id = 'YOUR_COMPANY_ID';
   -- Should return: ~102,415

   SELECT scope, COUNT(*), SUM(co2e_kg) 
   FROM uploads 
   WHERE company_id = 'YOUR_COMPANY_ID'
   GROUP BY scope;
   -- Should show breakdown by scope
   ```

4. **Verify in dashboard:**
   - Total Emissions card shows ~102.4 tonnes
   - Recent Uploads table shows 146 rows
   - Scope breakdown chart shows correct distribution
   - Category breakdown shows 4 types

---

## Notes

- **Summary sheets (Q1_Summary, H1_2024_Analysis):** May not process correctly as they don't have invoice-level detail. Expected to be skipped or processed as low-confidence records.

- **Mixed supplier sheets:** Should correctly identify supplier from each row's 'proveedor' column.

- **File naming in dashboard:** Each row will create a record with filename indicating the sheet/row number (e.g., "multi_sheet_invoices_12.xlsx (row 5)").

- **Performance:** Processing 146 records may take 30-60 seconds depending on server resources.

---

## Troubleshooting

**If fewer than 146 records are created:**
- Check summary sheets - they may have 0 valid rows
- Verify column mapping in `_parse_tabular_data()`
- Check logs for parsing errors

**If emissions don't match:**
- Verify emission factors in config.py
- Check unit detection logic (kWh vs m³ vs l vs tkm)
- Review category assignment

**If upload fails:**
- Check file size (should be < 50MB)
- Verify .xlsx format
- Check Supabase Storage connection
- Review backend logs for errors
