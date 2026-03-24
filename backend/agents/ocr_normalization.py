"""
Shared OCR normalization helpers for downstream agents.
"""

from __future__ import annotations

from typing import Any, Dict


def normalize_ocr_data(ocr_data: Dict[str, Any] | None, declared_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Normalize OCR payload to canonical keys consumed by feature/fraud agents.
    """
    ocr = (ocr_data or {}).copy()
    declared = declared_data or {}

    income_annum = _to_float(
        ocr.get("income_annum")
        or ocr.get("annual_income")
        or declared.get("annual_income")
        or declared.get("income_annum")
    )

    monthly_income = _to_float(
        ocr.get("declared_monthly_income")
        or ocr.get("monthly_income")
        or declared.get("declared_monthly_income")
    )

    if monthly_income is None and income_annum is not None:
        monthly_income = income_annum / 12.0

    existing_emi = _to_float(
        ocr.get("detected_existing_emi")
        or ocr.get("existing_emi")
        or ocr.get("declared_existing_emi")
        or declared.get("declared_existing_emi")
        or declared.get("existing_emi")
    )

    age = _to_float(
        ocr.get("age")
        or declared.get("age")
    )

    diagnosed_conditions = _to_list(
        ocr.get("diagnosed_conditions")
        or ocr.get("pre_existing_conditions")
        or ocr.get("pre_existing_diseases")
    )

    normalized = {
        **ocr,
        "avg_salary_6m": monthly_income,
        "bank_salary_credits": monthly_income,
        "detected_existing_emi": existing_emi,
        "existing_emi": existing_emi,
        "age": age,
        "diagnosed_conditions": diagnosed_conditions,
        "pre_existing_conditions": diagnosed_conditions,
    }

    return normalized


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []
