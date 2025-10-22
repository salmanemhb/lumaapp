"""
OCR and document parsing service for Spanish invoices
Supports: Iberdrola, Endesa, Naturgy, fuel cards, freight, CSVs
"""
from __future__ import annotations
import re
import fitz  # PyMuPDF
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None  # Define pd as None if not available
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING
from pathlib import Path
import hashlib
import json

if TYPE_CHECKING:
    import pandas as pd

from app.config import settings
from app.models.schemas import UploadRecord, DocumentCategory


class DocumentParser:
    """Main parser orchestrator for different document types"""
    
    # Known Spanish utility suppliers
    ELECTRICITY_SUPPLIERS = ["iberdrola", "endesa", "naturgy", "edp", "totalenergies"]
    GAS_SUPPLIERS = ["naturgy", "endesa gas", "gas natural"]
    FUEL_SUPPLIERS = ["repsol", "cepsa", "galp", "shell", "bp"]
    
    @staticmethod
    def normalize_spanish_number(text: str) -> Optional[float]:
        """
        Convert Spanish number format to float
        Examples: "12.500,45" -> 12500.45, "2.500" -> 2500.0
        """
        if not text:
            return None
        
        # Remove spaces and currency symbols
        text = text.strip().replace(' ', '').replace('€', '').replace('EUR', '')
        
        # Check if it has both . and ,
        if '.' in text and ',' in text:
            # Spanish format: thousands separator = . , decimal separator = ,
            text = text.replace('.', '').replace(',', '.')
        elif ',' in text:
            # Could be decimal separator
            # If more than 2 digits after comma, it's thousands separator
            parts = text.split(',')
            if len(parts[-1]) <= 2:
                text = text.replace(',', '.')
            else:
                text = text.replace(',', '')
        
        try:
            return float(text)
        except ValueError:
            return None
    
    @staticmethod
    def parse_spanish_date(date_str: str) -> Optional[datetime]:
        """
        Parse Spanish date formats: DD/MM/YYYY or DD-MM-YYYY
        """
        if not date_str:
            return None
        
        # Clean the string
        date_str = date_str.strip()
        
        # Try different formats
        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d.%m.%Y",
            "%Y-%m-%d",  # ISO format
            "%d/%m/%y",
            "%d-%m-%y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF using PyMuPDF
        Returns: (text, metadata)
        """
        text = ""
        metadata = {"pages": 0, "method": "pymupdf"}
        
        try:
            doc = fitz.open(file_path)
            metadata["pages"] = len(doc)
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            
            # Create hash of raw text for deduplication
            metadata["raw_text_hash"] = hashlib.sha1(text.encode()).hexdigest()
            
        except Exception as e:
            metadata["error"] = str(e)
        
        return text, metadata
    
    @staticmethod
    def detect_supplier(text: str) -> Optional[str]:
        """Detect supplier from document text"""
        text_lower = text.lower()
        
        # Check for known suppliers
        suppliers = {
            "Iberdrola": ["iberdrola"],
            "Endesa": ["endesa"],
            "Naturgy": ["naturgy", "gas natural"],
            "EDP": ["edp"],
            "Repsol": ["repsol"],
            "Cepsa": ["cepsa"],
            "Galp": ["galp"],
            "Shell": ["shell"],
            "BP": ["bp"],
            "DHL": ["dhl"],
            "SEUR": ["seur"],
            "MRW": ["mrw"]
        }
        
        for supplier, keywords in suppliers.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return supplier
        
        return None
    
    @classmethod
    def parse_document(cls, file_path: str, source_type: str) -> UploadRecord:
        """
        Main entry point for document parsing
        
        Args:
            file_path: Path to uploaded file
            source_type: 'pdf', 'csv', or 'xlsx'
        
        Returns:
            UploadRecord with extracted data
        """
        if source_type == "pdf":
            return cls.parse_pdf_invoice(file_path)
        elif source_type == "csv":
            return cls.parse_csv(file_path)
        elif source_type == "xlsx":
            return cls.parse_xlsx(file_path)
        else:
            # Return empty record
            return UploadRecord(confidence=0.0, meta={"error": "Unsupported file type"})
    
    @classmethod
    def parse_pdf_invoice(cls, file_path: str) -> UploadRecord:
        """Parse PDF invoice (Spanish utilities)"""
        text, metadata = cls.extract_text_from_pdf(file_path)
        
        # Detect supplier
        supplier = cls.detect_supplier(text)
        
        # Route to specific parser based on supplier
        if supplier == "Iberdrola":
            return cls.parse_iberdrola_pdf(text, metadata)
        elif supplier == "Endesa":
            return cls.parse_endesa_pdf(text, metadata)
        elif supplier == "Naturgy":
            return cls.parse_naturgy_pdf(text, metadata)
        elif supplier in ["Repsol", "Cepsa", "Galp", "Shell", "BP"]:
            return cls.parse_fuel_pdf(text, metadata, supplier)
        else:
            return cls.parse_generic_pdf(text, metadata)
    
    @classmethod
    def parse_iberdrola_pdf(cls, text: str, metadata: Dict) -> UploadRecord:
        """Parse Iberdrola electricity invoice"""
        record = UploadRecord(
            supplier="Iberdrola",
            category=DocumentCategory.ELECTRICITY,
            scope=2,
            meta=metadata
        )
        
        confidence_score = 0.5  # Base score for supplier detection
        fields_found = 0
        total_fields = 6
        
        # Invoice number: Factura nº: ES-2025-00421
        invoice_match = re.search(r'Factura\s*n[ºo]:?\s*([A-Z0-9\-\/\.]+)', text, re.IGNORECASE)
        if invoice_match:
            record.invoice_number = invoice_match.group(1).strip()
            fields_found += 1
        
        # Issue date: Fecha de emisión: 02/06/2025
        date_match = re.search(r'Fecha de emisi[óo]n:?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})', text, re.IGNORECASE)
        if date_match:
            record.issue_date = cls.parse_spanish_date(date_match.group(1))
            fields_found += 1
        
        # Period: Periodo de facturación: 01/05/2025 - 31/05/2025
        period_match = re.search(
            r'Periodo de facturaci[óo]n:?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})\s*[-–]\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
            text,
            re.IGNORECASE
        )
        if period_match:
            record.period_start = cls.parse_spanish_date(period_match.group(1))
            record.period_end = cls.parse_spanish_date(period_match.group(2))
            fields_found += 1
        
        # Usage: Consumo total: 12.500 kWh
        usage_match = re.search(r'Consumo(?:\s*total)?:?\s*([\d\.\,]+)\s*(kWh)', text, re.IGNORECASE)
        if usage_match:
            record.usage_value = cls.normalize_spanish_number(usage_match.group(1))
            record.usage_unit = "kWh"
            fields_found += 1
        
        # Emission factor: Factor de emisión: 0,231 kg CO2/kWh
        emission_match = re.search(r'Factor de emisi[óo]n:?\s*([\d\.\,]+)\s*kg\s*CO2\/kWh', text, re.IGNORECASE)
        if emission_match:
            record.emission_factor = cls.normalize_spanish_number(emission_match.group(1))
            fields_found += 1
        else:
            # Use default grid factor
            record.emission_factor = settings.ELECTRICITY_FACTOR_KG_PER_KWH
        
        # Total amount: Importe total (IVA 21%): 2.500,45 €
        amount_match = re.search(r'Importe total.*?:\s*([\d\.\,]+)\s*€', text, re.IGNORECASE)
        if amount_match:
            record.amount_total = cls.normalize_spanish_number(amount_match.group(1))
            fields_found += 1
        
        # VAT rate
        vat_match = re.search(r'IVA\s*(\d{1,2})%', text, re.IGNORECASE)
        if vat_match:
            record.vat_rate = float(vat_match.group(1)) / 100
        
        # Calculate CO2e
        if record.usage_value and record.emission_factor:
            record.co2e_kg = record.usage_value * record.emission_factor
        
        # Calculate confidence
        confidence_score = 0.5 + (fields_found / total_fields) * 0.5
        record.confidence = confidence_score
        
        return record
    
    @classmethod
    def parse_endesa_pdf(cls, text: str, metadata: Dict) -> UploadRecord:
        """Parse Endesa electricity invoice"""
        record = UploadRecord(
            supplier="Endesa",
            category=DocumentCategory.ELECTRICITY,
            scope=2,
            meta=metadata
        )
        
        confidence_score = 0.5
        fields_found = 0
        total_fields = 5
        
        # kWh facturados: 12500 kWh
        usage_match = re.search(r'kWh facturados:?\s*([\d\.\,]+)\s*kWh', text, re.IGNORECASE)
        if usage_match:
            record.usage_value = cls.normalize_spanish_number(usage_match.group(1))
            record.usage_unit = "kWh"
            fields_found += 1
        
        # Fecha emisión: 02/06/2025
        date_match = re.search(r'Fecha emisi[óo]n:?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})', text, re.IGNORECASE)
        if date_match:
            record.issue_date = cls.parse_spanish_date(date_match.group(1))
            fields_found += 1
        
        # Period
        period_match = re.search(
            r'Periodo:?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})\s*[-–]\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
            text,
            re.IGNORECASE
        )
        if period_match:
            record.period_start = cls.parse_spanish_date(period_match.group(1))
            record.period_end = cls.parse_spanish_date(period_match.group(2))
            fields_found += 1
        
        # Total factura: 2500,45 €
        amount_match = re.search(r'Total factura:?\s*([\d\.\,]+)\s*€', text, re.IGNORECASE)
        if amount_match:
            record.amount_total = cls.normalize_spanish_number(amount_match.group(1))
            fields_found += 1
        
        # Emission factor (if present)
        emission_match = re.search(r'([\d\.\,]+)\s*kg\s*CO2\/kWh', text, re.IGNORECASE)
        if emission_match:
            record.emission_factor = cls.normalize_spanish_number(emission_match.group(1))
            fields_found += 1
        else:
            record.emission_factor = settings.ELECTRICITY_FACTOR_KG_PER_KWH
        
        # Calculate CO2e
        if record.usage_value and record.emission_factor:
            record.co2e_kg = record.usage_value * record.emission_factor
        
        confidence_score = 0.5 + (fields_found / total_fields) * 0.5
        record.confidence = confidence_score
        
        return record
    
    @classmethod
    def parse_naturgy_pdf(cls, text: str, metadata: Dict) -> UploadRecord:
        """Parse Naturgy gas invoice"""
        record = UploadRecord(
            supplier="Naturgy",
            category=DocumentCategory.NATURAL_GAS,
            scope=1,  # On-site combustion
            meta=metadata
        )
        
        confidence_score = 0.5
        fields_found = 0
        total_fields = 5
        
        # Consumo: 1200 m3 or kWh
        usage_match = re.search(r'Consumo.*?:?\s*([\d\.\,]+)\s*(m3|kWh)', text, re.IGNORECASE)
        if usage_match:
            value = cls.normalize_spanish_number(usage_match.group(1))
            unit = usage_match.group(2).lower()
            
            if unit == "m3":
                # Convert m3 to kWh if conversion factor available
                conversion_match = re.search(r'PCS.*?([\d\.\,]+)\s*kWh/m3', text, re.IGNORECASE)
                if conversion_match:
                    pcs = cls.normalize_spanish_number(conversion_match.group(1))
                    record.usage_value = value * pcs
                else:
                    record.usage_value = value * settings.NATURAL_GAS_M3_TO_KWH
                record.usage_unit = "kWh"
            else:
                record.usage_value = value
                record.usage_unit = "kWh"
            
            fields_found += 1
        
        # Emission factor for natural gas
        emission_match = re.search(r'([\d\.\,]+)\s*kg\s*CO2\/kWh', text, re.IGNORECASE)
        if emission_match:
            record.emission_factor = cls.normalize_spanish_number(emission_match.group(1))
            fields_found += 1
        else:
            record.emission_factor = settings.NATURAL_GAS_FACTOR_KG_PER_KWH
        
        # Date and period (similar to Iberdrola)
        date_match = re.search(r'Fecha.*?emisi[óo]n:?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})', text, re.IGNORECASE)
        if date_match:
            record.issue_date = cls.parse_spanish_date(date_match.group(1))
            fields_found += 1
        
        period_match = re.search(
            r'Periodo.*?:?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})\s*[-–]\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
            text,
            re.IGNORECASE
        )
        if period_match:
            record.period_start = cls.parse_spanish_date(period_match.group(1))
            record.period_end = cls.parse_spanish_date(period_match.group(2))
            fields_found += 1
        
        amount_match = re.search(r'Total.*?:?\s*([\d\.\,]+)\s*€', text, re.IGNORECASE)
        if amount_match:
            record.amount_total = cls.normalize_spanish_number(amount_match.group(1))
            fields_found += 1
        
        # Calculate CO2e
        if record.usage_value and record.emission_factor:
            record.co2e_kg = record.usage_value * record.emission_factor
        
        confidence_score = 0.5 + (fields_found / total_fields) * 0.5
        record.confidence = confidence_score
        
        return record
    
    @classmethod
    def parse_fuel_pdf(cls, text: str, metadata: Dict, supplier: str) -> UploadRecord:
        """Parse fuel card invoice (diesel/gasoline)"""
        record = UploadRecord(
            supplier=supplier,
            category=DocumentCategory.FUEL,
            scope=1,  # On-site combustion
            meta=metadata
        )
        
        confidence_score = 0.5
        fields_found = 0
        total_fields = 5
        
        # Litros or L
        usage_match = re.search(r'([\d\.\,]+)\s*(Litros|L)\b', text, re.IGNORECASE)
        if usage_match:
            record.usage_value = cls.normalize_spanish_number(usage_match.group(1))
            record.usage_unit = "L"
            fields_found += 1
        
        # Detect fuel type
        fuel_type = None
        if re.search(r'gas[óo]leo|diesel|di[ée]sel', text, re.IGNORECASE):
            fuel_type = "diesel"
            record.emission_factor = settings.DIESEL_FACTOR_KG_PER_L
        elif re.search(r'gasolina|gasoline|95|98', text, re.IGNORECASE):
            fuel_type = "gasoline"
            record.emission_factor = settings.GASOLINE_FACTOR_KG_PER_L
        
        if fuel_type:
            fields_found += 1
        
        # Date
        date_match = re.search(r'Fecha:?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})', text, re.IGNORECASE)
        if date_match:
            record.issue_date = cls.parse_spanish_date(date_match.group(1))
            fields_found += 1
        
        # Amount
        amount_match = re.search(r'Total.*?:?\s*([\d\.\,]+)\s*€', text, re.IGNORECASE)
        if amount_match:
            record.amount_total = cls.normalize_spanish_number(amount_match.group(1))
            fields_found += 1
        
        # Calculate CO2e
        if record.usage_value and record.emission_factor:
            record.co2e_kg = record.usage_value * record.emission_factor
            fields_found += 1
        
        confidence_score = 0.5 + (fields_found / total_fields) * 0.5
        record.confidence = confidence_score
        
        return record
    
    @classmethod
    def parse_generic_pdf(cls, text: str, metadata: Dict) -> UploadRecord:
        """Generic PDF parser for unrecognized suppliers"""
        record = UploadRecord(
            supplier=cls.detect_supplier(text),
            meta=metadata,
            confidence=0.3
        )
        
        # Try to extract basic info
        date_match = re.search(r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})', text)
        if date_match:
            record.issue_date = cls.parse_spanish_date(date_match.group(1))
        
        amount_match = re.search(r'([\d\.\,]+)\s*€', text)
        if amount_match:
            record.amount_total = cls.normalize_spanish_number(amount_match.group(1))
        
        return record
    
    @classmethod
    def parse_csv(cls, file_path: str) -> UploadRecord:
        """Parse CSV file with flexible column mapping"""
        try:
            df = pd.read_csv(file_path)
            return cls._parse_tabular_data(df)
        except Exception as e:
            return UploadRecord(confidence=0.0, meta={"error": str(e)})
    
    @classmethod
    def parse_xlsx(cls, file_path: str) -> UploadRecord:
        """Parse XLSX file with flexible column mapping"""
        try:
            df = pd.read_excel(file_path)
            return cls._parse_tabular_data(df)
        except Exception as e:
            return UploadRecord(confidence=0.0, meta={"error": str(e)})
    
    @classmethod
    def _parse_tabular_data(cls, df: Any) -> UploadRecord:
        """Parse DataFrame with flexible column mapping"""
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Column synonym mapping
        column_map = {
            'date': ['fecha', 'fecha_factura', 'posting_date', 'date'],
            'supplier': ['proveedor', 'vendor', 'empresa', 'supplier'],
            'category': ['categoria', 'tipo_gasto', 'naturaleza', 'category'],
            'usage_value': ['consumo', 'kwh', 'm3', 'litros', 'l', 'distancia_km', 'km', 'usage'],
            'usage_unit': ['unidad', 'unidad_consumo', 'uom', 'unit'],
            'amount_total': ['importe_total', 'total', 'importe', 'amount'],
            'invoice_number': ['num_factura', 'factura', 'invoice'],
            'scope': ['alcance', 'scope'],
        }
        
        # Extract first row data
        if len(df) == 0:
            return UploadRecord(confidence=0.0, meta={"error": "Empty file"})
        
        row = df.iloc[0]
        record = UploadRecord()
        fields_found = 0
        
        # Map columns
        for target, synonyms in column_map.items():
            for syn in synonyms:
                if syn in df.columns:
                    value = row[syn]
                    if pd.notna(value):
                        if target == 'date':
                            record.issue_date = pd.to_datetime(value, errors='coerce')
                        elif target == 'supplier':
                            record.supplier = str(value)
                        elif target == 'usage_value':
                            record.usage_value = float(value) if isinstance(value, (int, float)) else None
                        elif target == 'usage_unit':
                            record.usage_unit = str(value)
                        elif target == 'amount_total':
                            record.amount_total = float(value) if isinstance(value, (int, float)) else None
                        elif target == 'invoice_number':
                            record.invoice_number = str(value)
                        elif target == 'scope':
                            record.scope = int(value) if isinstance(value, (int, float)) else None
                        fields_found += 1
                    break
        
        # Determine category and scope from usage_unit or context
        if record.usage_unit:
            unit_lower = record.usage_unit.lower()
            if 'kwh' in unit_lower:
                record.category = DocumentCategory.ELECTRICITY
                record.scope = 2
                record.emission_factor = settings.ELECTRICITY_FACTOR_KG_PER_KWH
            elif 'm3' in unit_lower:
                record.category = DocumentCategory.NATURAL_GAS
                record.scope = 1
                record.emission_factor = settings.NATURAL_GAS_FACTOR_KG_PER_KWH
            elif 'l' in unit_lower or 'litros' in unit_lower:
                record.category = DocumentCategory.FUEL
                record.scope = 1
                record.emission_factor = settings.DIESEL_FACTOR_KG_PER_L
            elif 'km' in unit_lower or 'tkm' in unit_lower:
                record.category = DocumentCategory.FREIGHT
                record.scope = 3
                record.emission_factor = settings.ROAD_FREIGHT_FACTOR_KG_PER_TKM
        
        # Calculate CO2e
        if record.usage_value and record.emission_factor:
            record.co2e_kg = record.usage_value * record.emission_factor
        
        # Confidence based on fields found
        record.confidence = min(0.3 + (fields_found / 6) * 0.7, 1.0)
        record.meta = {"source": "csv/xlsx", "fields_found": fields_found}
        
        return record
