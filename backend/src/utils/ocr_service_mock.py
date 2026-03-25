"""
Mock OCR service used for local/dev and resilient fallbacks.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class OCRService:
    def process_document(self, file_path: str, preprocess: bool = True, classify: bool = True) -> dict[str, Any]:
        path = Path(file_path)
        name = path.name.lower()

        doc_type = self._classify_from_name(name)
        text = f"mock text extracted from {name}"

        return {
            "document_type": doc_type,
            "text": text,
            "confidence": 93.0,
        }

    def extract_field(self, text: str, field_name: str) -> Any:
        source = (text or "").lower()

        patterns = {
            "aadhaar_number": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
            "pan_number": r"\b[A-Z]{5}\d{4}[A-Z]\b",
            "passport_number": r"\b[A-Z]\d{7}\b",
            "voter_id_number": r"\b[A-Z]{3}\d{7}\b",
            "hba1c": r"hba1c\s*[:\-]?\s*(\d+(?:\.\d+)?)",
            "cholesterol": r"cholesterol\s*[:\-]?\s*(\d+(?:\.\d+)?)",
            "blood_sugar": r"blood\s+sugar\s*[:\-]?\s*(\d+(?:\.\d+)?)",
            "height": r"height\s*[:\-]?\s*(\d+(?:\.\d+)?)",
            "weight": r"weight\s*[:\-]?\s*(\d+(?:\.\d+)?)",
            "age": r"\bage\s*[:\-]?\s*(\d{1,3})\b",
            "monthly_income": r"(?:monthly\s+income|net\s+salary)\s*[:\-]?\s*([\d,]+)",
            "annual_income": r"(?:annual\s+income|income\s+annum)\s*[:\-]?\s*([\d,]+)",
            "bank_balance": r"(?:closing\s+balance|available\s+balance)\s*[:\-]?\s*([\d,]+)",
            "property_value": r"(?:property\s+value|market\s+value)\s*[:\-]?\s*([\d,]+)",
        }

        if field_name == "gender":
            if "female" in source:
                return "Female"
            if "male" in source:
                return "Male"
            return None

        if field_name == "name":
            m = re.search(r"(?:name|full\s+name)\s*[:\-]?\s*([a-z\s]{3,})", source)
            return m.group(1).strip().title() if m else None

        pattern = patterns.get(field_name)
        if not pattern:
            return None

        m = re.search(pattern, text or "", flags=re.IGNORECASE)
        if not m:
            return None

        if m.lastindex:
            return m.group(1)
        return m.group(0)

    @staticmethod
    def _classify_from_name(name: str) -> str:
        mapping = {
            "aadhaar": "aadhaar_card",
            "aadhar": "aadhaar_card",
            "voter": "voter_id",
            "pan": "pan_card",
            "passport": "passport",
            "salary": "salary_slip",
            "bank": "bank_statement",
            "statement": "bank_statement",
            "diagnostic": "diagnostic_report",
            "medical": "diagnostic_report",
            "property": "property_document",
            "itr": "itr",
            "form16": "itr_form16",
            "utility": "utility_bill",
            "gst": "gst_certificate",
            "trade": "trade_license",
            "cibil": "cibil_report",
        }
        for token, doc_type in mapping.items():
            if token in name:
                return doc_type
        return "unknown"
