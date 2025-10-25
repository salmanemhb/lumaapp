"""
Test Agent 1: Data Intake Agent

Tests the invoice extraction functionality without needing actual uploads.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from agents.data_intake_agent import DataIntakeAgent


def test_invoice_parsing():
    """Test the invoice text parser"""
    
    # Sample Spanish electricity invoice text
    sample_text = """
    FACTURA ELECTRICIDAD
    
    Iberdrola Clientes, S.A.U.
    
    DATOS DE LA FACTURA
    Número de Factura: INV-2025-09-001
    Periodo de facturación: 01/09/2025 - 30/09/2025
    
    CONSUMO ELÉCTRICO
    Consumo: 1.250,5 kWh
    Precio energía: 0,148 €/kWh
    
    IMPORTE TOTAL
    Base imponible: 157,21 €
    IVA (21%): 33,01 €
    Total: 190,22 €
    """
    
    agent = DataIntakeAgent()
    result = agent._parse_invoice_text(sample_text)
    
    print("✅ Test: Invoice Text Parsing")
    print(f"Extracted data: {result}")
    print()
    
    # Check expected fields
    assert result.get('supplier') == 'Iberdrola', "Supplier detection failed"
    assert result.get('category') == 'electricity', "Category detection failed"
    assert result.get('usage_value') == 1250.5, "Usage value extraction failed"
    assert result.get('usage_unit') == 'kWh', "Usage unit extraction failed"
    assert result.get('invoice_number'), "Invoice number extraction failed"
    
    print("✅ All assertions passed!")
    return True


def test_normalization():
    """Test data normalization"""
    
    agent = DataIntakeAgent()
    
    raw_data = {
        "supplier": "Iberdrola",
        "category": "electricity",
        "usage_value": 1250.5,
        "usage_unit": "kWh",
        "amount_total": 190.22,
        "invoice_number": "INV-2025-09-001"
    }
    
    normalized = agent._normalize_data(raw_data)
    
    print("✅ Test: Data Normalization")
    print(f"Normalized data: {normalized}")
    print()
    
    assert 'supplier' in normalized
    assert 'category' in normalized
    assert normalized.get('currency') == 'EUR', "Default currency not set"
    
    print("✅ All assertions passed!")
    return True


def test_file_type_detection():
    """Test file type detection"""
    
    agent = DataIntakeAgent()
    
    test_cases = [
        ("invoice.pdf", "pdf"),
        ("data.csv", "csv"),
        ("spreadsheet.xlsx", "excel"),
        ("receipt.jpg", "image"),
        ("document.png", "image"),
    ]
    
    print("✅ Test: File Type Detection")
    for filename, expected in test_cases:
        detected = agent._detect_file_type("", filename)
        print(f"  {filename} -> {detected}")
        assert detected == expected, f"Failed for {filename}"
    
    print("✅ All assertions passed!")
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 AGENT 1: DATA INTAKE - UNIT TESTS")
    print("=" * 50)
    print()
    
    try:
        test_file_type_detection()
        test_invoice_parsing()
        test_normalization()
        
        print("=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("1. Run database migration in Supabase")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Deploy backend to Render")
        print("4. Test with real file upload")
        
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
