"""
Factory for OCR service selection.
"""

from __future__ import annotations

import os

from src.utils.ocr_service import OCRService
from src.utils.ocr_service_mock import OCRService as MockOCRService


def get_ocr_service(groq_api_key: str | None = None):
    mode = os.getenv("OCR_MODE", "mock").strip().lower()
    if mode == "production":
        return OCRService(groq_api_key=groq_api_key)
    return MockOCRService()
