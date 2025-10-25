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
    def parse_document(cls, file_path: str, source_type: str) -> List[UploadRecord]:
        """
        Main entry point for document parsing
        
        Args:
            file_path: Path to uploaded file
            source_type: 'pdf', 'csv', 'xlsx', 'xls', 'txt'
        
        Returns:
            List[UploadRecord] with extracted data
        """
        if source_type == "pdf":
            return [cls.parse_pdf_invoice(file_path)]
        elif source_type == "csv":
            return cls.parse_csv(file_path)
        elif source_type in ["xlsx", "xls"]:
            return cls.parse_xlsx(file_path)
        elif source_type == "txt":
            # Treat TXT files like extracted PDF text
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            metadata = {"pages": 1, "file_type": "txt"}
            # Detect supplier and route to appropriate parser
            supplier = cls.detect_supplier(text)
            if supplier == "Iberdrola":
                return [cls.parse_iberdrola_pdf(text, metadata)]
            elif supplier == "Endesa":
                return [cls.parse_endesa_pdf(text, metadata)]
            elif supplier == "Naturgy":
                return [cls.parse_naturgy_pdf(text, metadata)]
            elif supplier in ["Repsol", "Cepsa", "Galp", "Shell", "BP"]:
                return [cls.parse_fuel_pdf(text, metadata, supplier)]
            else:
                return [cls.parse_generic_pdf(text, metadata)]
        else:
            # Return empty record
            return [UploadRecord(confidence=0.0, meta={"error": "Unsupported file type"})]
    
    @classmethod
    def parse_pdf_invoice(cls, file_path: str) -> UploadRecord:
        """Parse PDF invoice (Spanish utilities) with detailed extraction logging"""
        text, metadata = cls.extract_text_from_pdf(file_path)
        
        # Add extraction log for debugging
        extraction_log = {
            "ocr_text_length": len(text),
            "ocr_text_preview": text[:500] if text else "No text extracted",
            "patterns_tried": [],
            "fields_found": [],
            "fields_missing": []
        }
        
        # Detect supplier
        supplier = cls.detect_supplier(text)
        extraction_log["patterns_tried"].append({"field": "supplier", "result": supplier or "Not detected"})
        
        # Route to specific parser based on supplier
        if supplier == "Iberdrola":
            result = cls.parse_iberdrola_pdf(text, metadata)
        elif supplier == "Endesa":
            result = cls.parse_endesa_pdf(text, metadata)
        elif supplier == "Naturgy":
            result = cls.parse_naturgy_pdf(text, metadata)
        elif supplier in ["Repsol", "Cepsa", "Galp", "Shell", "BP"]:
            result = cls.parse_fuel_pdf(text, metadata, supplier)
        else:
            result = cls.parse_generic_pdf(text, metadata)
        
        # Add extraction log to result
        if not result.meta:
            result.meta = {}
        if isinstance(result.meta, dict):
            result.meta["extraction_log"] = extraction_log
        
        return result
    
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
        """Generic PDF parser for unrecognized suppliers with detailed logging"""
        supplier = cls.detect_supplier(text)
        record = UploadRecord(
            supplier=supplier,
            meta=metadata if metadata else {},
            confidence=0.3
        )
        
        fields_found = 0
        extraction_attempts = []  # Track what we tried
        
        # Invoice number
        invoice_patterns = [
            r'Invoice\s*Number:?\s*([A-Z0-9\-\/\.]+)',
            r'N[ºo]\s*Factura:?\s*([A-Z0-9\-\/\.]+)',
            r'Factura:?\s*([A-Z0-9\-\/\.]+)'
        ]
        invoice_found = False
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                record.invoice_number = match.group(1).strip()
                fields_found += 1
                invoice_found = True
                extraction_attempts.append({"field": "invoice_number", "status": "found", "value": record.invoice_number})
                break
        if not invoice_found:
            extraction_attempts.append({"field": "invoice_number", "status": "missing", "patterns_tried": len(invoice_patterns)})
        
        # Date (try multiple formats)
        date_patterns = [
            r'Date:?\s*(\d{1,2}[\s\/\-]\w+[\s\/\-]\d{4})',  # 15 de Enero 2025
            r'Fecha:?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
            r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})'
        ]
        date_found = False
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    record.issue_date = cls.parse_spanish_date(match.group(1))
                    fields_found += 1
                    date_found = True
                    extraction_attempts.append({"field": "date", "status": "found", "value": str(record.issue_date)})
                    break
                except:
                    pass
        
        # Period
        period_match = re.search(
            r'Per[ií]odo:?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})\s*[-–]\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
            text,
            re.IGNORECASE
        )
        if period_match:
            record.period_start = cls.parse_spanish_date(period_match.group(1))
            record.period_end = cls.parse_spanish_date(period_match.group(2))
            fields_found += 1
        
        # Try to detect category and extract usage
        # Electricity
        if re.search(r'electric|kWh|energ[ií]a', text, re.IGNORECASE):
            record.category = DocumentCategory.ELECTRICITY
            record.scope = 2
            extraction_attempts.append({"field": "category", "status": "detected", "value": "electricity"})
            
            usage_patterns = [
                r'([\d\.\,]+)\s*kWh',
                r'Consumo.*?:?\s*([\d\.\,]+)\s*kWh',
                r'Energy\s*Consumption:?\s*([\d\.\,]+)\s*kWh'
            ]
            usage_found = False
            for pattern in usage_patterns:
                usage_match = re.search(pattern, text, re.IGNORECASE)
                if usage_match:
                    record.usage_value = cls.normalize_spanish_number(usage_match.group(1))
                    record.usage_unit = "kWh"
                    record.emission_factor = settings.ELECTRICITY_FACTOR_KG_PER_KWH
                    fields_found += 1
                    usage_found = True
                    extraction_attempts.append({
                        "field": "usage_value",
                        "status": "found",
                        "value": record.usage_value,
                        "pattern": pattern,
                        "matched_text": usage_match.group(0)
                    })
                    break
            
            if not usage_found:
                # Find sample text around kWh for debugging
                sample_text = ""
                idx = text.lower().find('kwh')
                if idx != -1:
                    sample_text = text[max(0, idx-80):min(len(text), idx+50)]
                extraction_attempts.append({
                    "field": "usage_value",
                    "status": "missing",
                    "patterns_tried": usage_patterns,
                    "text_sample": sample_text or text[:200]
                })
        
        # Gas
        elif re.search(r'gas|m³|m3', text, re.IGNORECASE):
            record.category = DocumentCategory.NATURAL_GAS
            record.scope = 1
            extraction_attempts.append({"field": "category", "status": "detected", "value": "gas"})
            
            usage_patterns = [
                r'([\d\.\,]+)\s*m[³3]',
                r'Consumo.*?:?\s*([\d\.\,]+)\s*m[³3]',
                r'Volume:?\s*([\d\.\,]+)\s*m[³3]'
            ]
            usage_found = False
            for pattern in usage_patterns:
                usage_match = re.search(pattern, text, re.IGNORECASE)
                if usage_match:
                    record.usage_value = cls.normalize_spanish_number(usage_match.group(1))
                    record.usage_unit = "m3"
                    record.emission_factor = settings.GAS_FACTOR_KG_PER_M3
                    fields_found += 1
                    usage_found = True
                    extraction_attempts.append({
                        "field": "usage_value",
                        "status": "found",
                        "value": record.usage_value,
                        "pattern": pattern,
                        "matched_text": usage_match.group(0)
                    })
                    break
            
            if not usage_found:
                sample_text = ""
                idx = text.lower().find('m³') if 'm³' in text.lower() else text.lower().find('m3')
                if idx != -1:
                    sample_text = text[max(0, idx-80):min(len(text), idx+50)]
                extraction_attempts.append({
                    "field": "usage_value",
                    "status": "missing",
                    "patterns_tried": usage_patterns,
                    "text_sample": sample_text or text[:200]
                })
        
        # Fuel
        elif re.search(r'diesel|gasolina|combustible|litros?|L\b', text, re.IGNORECASE):
            record.category = DocumentCategory.FUEL
            record.scope = 1
            extraction_attempts.append({"field": "category", "status": "detected", "value": "fuel"})
            
            usage_patterns = [
                r'([\d\.\,]+)\s*(Litros|L)\b',
                r'Volume:?\s*([\d\.\,]+)\s*L',
                r'Cantidad:?\s*([\d\.\,]+)\s*Litros'
            ]
            usage_found = False
            for pattern in usage_patterns:
                usage_match = re.search(pattern, text, re.IGNORECASE)
                if usage_match:
                    record.usage_value = cls.normalize_spanish_number(usage_match.group(1))
                    record.usage_unit = "L"
                    if re.search(r'diesel', text, re.IGNORECASE):
                        record.emission_factor = settings.DIESEL_FACTOR_KG_PER_L
                    else:
                        record.emission_factor = settings.GASOLINE_FACTOR_KG_PER_L
                    fields_found += 1
                    usage_found = True
                    extraction_attempts.append({
                        "field": "usage_value",
                        "status": "found",
                        "value": record.usage_value,
                        "pattern": pattern,
                        "matched_text": usage_match.group(0)
                    })
                    break
            
            if not usage_found:
                sample_text = ""
                for keyword in ['litros', 'liters', 'l\b']:
                    idx = text.lower().find(keyword[:5])
                    if idx != -1:
                        sample_text = text[max(0, idx-80):min(len(text), idx+50)]
                        break
                extraction_attempts.append({
                    "field": "usage_value",
                    "status": "missing",
                    "patterns_tried": usage_patterns,
                    "text_sample": sample_text or text[:200]
                })
        
        # Freight
        elif re.search(r'transport|freight|env[ií]o|distancia|km', text, re.IGNORECASE):
            record.category = DocumentCategory.FREIGHT
            record.scope = 3
            extraction_attempts.append({"field": "category", "status": "detected", "value": "freight"})
            
            distance_patterns = [
                r'([\d\.\,]+)\s*km',
                r'Distance:?\s*([\d\.\,]+)\s*km',
                r'Distancia:?\s*([\d\.\,]+)\s*km'
            ]
            distance_found = False
            for pattern in distance_patterns:
                distance_match = re.search(pattern, text, re.IGNORECASE)
                if distance_match:
                    distance = cls.normalize_spanish_number(distance_match.group(1))
                    distance_found = True
                    extraction_attempts.append({
                        "field": "distance",
                        "status": "found",
                        "value": distance,
                        "pattern": pattern
                    })
                    break
            
            weight_patterns = [
                r'([\d\.\,]+)\s*kg',
                r'Weight:?\s*([\d\.\,]+)\s*kg',
                r'Peso:?\s*([\d\.\,]+)\s*kg'
            ]
            weight_found = False
            for pattern in weight_patterns:
                weight_match = re.search(pattern, text, re.IGNORECASE)
                if weight_match:
                    weight = cls.normalize_spanish_number(weight_match.group(1))
                    weight_found = True
                    extraction_attempts.append({
                        "field": "weight",
                        "status": "found",
                        "value": weight,
                        "pattern": pattern
                    })
                    break
            
            if distance_found and weight_found:
                record.usage_value = distance
                record.usage_unit = "km"
                # Simplified freight calculation
                record.co2e_kg = (distance * weight * 0.00012)  # Rough estimate
                fields_found += 1
                extraction_attempts.append({
                    "field": "emissions",
                    "status": "calculated",
                    "value": f"{record.co2e_kg:.2f} kg",
                    "formula": f"{distance} km × {weight} kg × 0.00012"
                })
            else:
                if not distance_found:
                    extraction_attempts.append({
                        "field": "distance",
                        "status": "missing",
                        "patterns_tried": distance_patterns
                    })
                if not weight_found:
                    extraction_attempts.append({
                        "field": "weight",
                        "status": "missing",
                        "patterns_tried": weight_patterns
                    })
        else:
            extraction_attempts.append({"field": "category", "status": "not_detected", "keywords_searched": ["electric", "gas", "fuel", "freight"]})
        
        # Amount
        amount_patterns = [
            r'Total:?\s*([\d\.\,]+)\s*EUR',
            r'Importe:?\s*([\d\.\,]+)\s*€',
            r'([\d\.\,]+)\s*EUR',
            r'([\d\.\,]+)\s*€'
        ]
        amount_found = False
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                record.amount_total = cls.normalize_spanish_number(match.group(1))
                record.currency = "EUR"
                fields_found += 1
                amount_found = True
                extraction_attempts.append({
                    "field": "amount_total",
                    "status": "found",
                    "value": record.amount_total,
                    "pattern": pattern,
                    "matched_text": match.group(0)
                })
                break
        
        if not amount_found:
            extraction_attempts.append({
                "field": "amount_total",
                "status": "missing",
                "patterns_tried": amount_patterns
            })
        
        # Calculate emissions if we have usage and factor
        if record.usage_value and record.emission_factor and not record.co2e_kg:
            record.co2e_kg = record.usage_value * record.emission_factor
            fields_found += 1
            extraction_attempts.append({
                "field": "emissions",
                "status": "calculated",
                "value": f"{record.co2e_kg:.2f} kg",
                "formula": f"{record.usage_value} {record.usage_unit} × {record.emission_factor}"
            })
        elif not record.co2e_kg:
            extraction_attempts.append({
                "field": "emissions",
                "status": "not_calculated",
                "reason": f"missing_usage_value={not record.usage_value}, missing_factor={not record.emission_factor}"
            })
        
        # Update confidence based on fields found
        record.confidence = 0.3 + (fields_found / 8) * 0.6  # Max 0.9
        
        # Store extraction log in meta
        if not isinstance(record.meta, dict):
            record.meta = {}
        record.meta['extraction_attempts'] = extraction_attempts
        record.meta['fields_found_count'] = fields_found
        
        return record
    
    @classmethod
    def parse_csv(cls, file_path: str) -> List[UploadRecord]:
        """Parse CSV file with flexible column mapping - returns list of records for multi-row support"""
        try:
            df = pd.read_csv(file_path)
            return cls._parse_tabular_data(df)
        except Exception as e:
            return [UploadRecord(confidence=0.0, meta={"error": str(e)})]
    
    @classmethod
    def parse_xlsx(cls, file_path: str) -> List[UploadRecord]:
        """Parse Excel file with flexible column mapping - supports multiple sheets and rows"""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            all_records = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_records = cls._parse_tabular_data(df, sheet_name=sheet_name)
                all_records.extend(sheet_records)
            
            return all_records if all_records else [UploadRecord(confidence=0.0, meta={"error": "No data found"})]
        except Exception as e:
            return [UploadRecord(confidence=0.0, meta={"error": str(e)})]
    
    @classmethod
    def _parse_tabular_data(cls, df: Any, sheet_name: str = None) -> List[UploadRecord]:
        """Parse DataFrame with flexible column mapping - processes ALL rows with detailed logging"""
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Column synonym mapping
        column_map = {
            'date': ['fecha', 'fecha_factura', 'posting_date', 'date'],
            'supplier': ['proveedor', 'vendor', 'empresa', 'supplier'],
            'category': ['categoria', 'tipo_gasto', 'naturaleza', 'category'],
            'usage_value': ['consumo', 'kwh', 'm3', 'litros', 'l', 'distancia_km', 'km', 'usage', 'usage_value'],
            'usage_unit': ['unidad', 'unidad_consumo', 'uom', 'unit', 'usage_unit'],
            'amount_total': ['importe_total', 'total', 'importe', 'amount', 'amount_total'],
            'invoice_number': ['num_factura', 'factura', 'invoice', 'invoice_number'],
            'scope': ['alcance', 'scope'],
        }
        
        # Process ALL rows instead of just first
        if len(df) == 0:
            return [UploadRecord(confidence=0.0, meta={"error": "Empty file"})]
        
        records = []
        
        # Loop through each row in the dataframe
        for idx, row in df.iterrows():
            record = UploadRecord()
            fields_found = 0
            extraction_log = {
                "columns_available": list(df.columns),
                "column_mappings": {},
                "unmapped_fields": []
            }
            
            # Add sheet/row info to meta
            if sheet_name:
                record.meta = {"sheet": sheet_name, "row": idx + 2}  # +2 for header + 0-index
            else:
                record.meta = {"row": idx + 1}
            
            # Map columns with logging
            for target, synonyms in column_map.items():
                mapped = False
                for syn in synonyms:
                    if syn in df.columns:
                        value = row[syn]
                        if pd.notna(value):
                            extraction_log["column_mappings"][target] = {"column": syn, "value": str(value)[:100]}
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
                            mapped = True
                        break
                
                if not mapped:
                    extraction_log["unmapped_fields"].append({
                        "field": target,
                        "searched_columns": synonyms,
                        "status": "not_found_in_csv"
                    })
            
            # Determine category and scope from usage_unit or context
            if record.usage_unit:
                unit_lower = record.usage_unit.lower()
                if 'kwh' in unit_lower:
                    record.category = DocumentCategory.ELECTRICITY
                    record.scope = 2
                    record.emission_factor = settings.ELECTRICITY_FACTOR_KG_PER_KWH
                    extraction_log["category_detection"] = {"method": "from_unit", "unit": unit_lower, "category": "electricity"}
                elif 'm3' in unit_lower:
                    record.category = DocumentCategory.NATURAL_GAS
                    record.scope = 1
                    # Use IPCC 2006 factor for natural gas: 2.016 kg CO2e per m³
                    record.emission_factor = 2.016
                    extraction_log["category_detection"] = {"method": "from_unit", "unit": unit_lower, "category": "gas"}
                elif 'l' in unit_lower or 'litros' in unit_lower:
                    record.category = DocumentCategory.FUEL
                    record.scope = 1
                    record.emission_factor = settings.DIESEL_FACTOR_KG_PER_L
                    extraction_log["category_detection"] = {"method": "from_unit", "unit": unit_lower, "category": "fuel"}
                elif 'km' in unit_lower or 'tkm' in unit_lower:
                    record.category = DocumentCategory.FREIGHT
                    record.scope = 3
                    record.emission_factor = settings.ROAD_FREIGHT_FACTOR_KG_PER_TKM
                    extraction_log["category_detection"] = {"method": "from_unit", "unit": unit_lower, "category": "freight"}
                else:
                    extraction_log["category_detection"] = {"method": "from_unit", "unit": unit_lower, "category": "unknown_unit"}
            else:
                extraction_log["category_detection"] = {"method": "not_detected", "reason": "no_usage_unit_found"}
            
            # Calculate CO2e
            if record.usage_value and record.emission_factor:
                record.co2e_kg = record.usage_value * record.emission_factor
                extraction_log["emissions_calculation"] = {
                    "status": "calculated",
                    "formula": f"{record.usage_value} × {record.emission_factor}",
                    "result": f"{record.co2e_kg:.2f} kg"
                }
            else:
                extraction_log["emissions_calculation"] = {
                    "status": "not_calculated",
                    "reason": f"usage_value={record.usage_value}, emission_factor={record.emission_factor}"
                }
            
            # Confidence based on fields found
            record.confidence = min(0.3 + (fields_found / 6) * 0.7, 1.0)
            record.meta.update({
                "source": "csv/xlsx",
                "fields_found": fields_found,
                "extraction_log": extraction_log
            })
            
            # Only add records with some valid data
            if fields_found > 0:
                records.append(record)
        
        return records if records else [UploadRecord(confidence=0.0, meta={"error": "No valid data found"})]
