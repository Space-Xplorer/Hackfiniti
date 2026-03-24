from .mock import run_mock_ocr
from .production import run_production_ocr


def run_ocr(payload: dict, mode: str = "mock") -> dict:
    if mode == "production":
        return run_production_ocr(payload)
    return run_mock_ocr(payload)
