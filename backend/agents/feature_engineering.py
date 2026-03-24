"""
Feature Engineering Agent for derived underwriting features.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.schemas.state import ApplicationState
from src.utils.logging import log_agent_execution, log_error
from src.utils.storage import save_derived_features

logger = logging.getLogger(__name__)


class FeatureEngineeringAgent:
    """Compute derived features for loan and health underwriting."""

    def process(self, state: ApplicationState) -> ApplicationState:
        request_id = state.get("request_id", "unknown")
        log_agent_execution("FeatureEngineeringAgent", request_id, "started")

        try:
            request_type = state.get("request_type")
            declared = state.get("declared_data", {}) or {}
            ocr_data = state.get("ocr_extracted_data", {}) or {}

            derived: Dict[str, Any] = {
                "loan": {},
                "health": {}
            }

            if request_type in ["loan", "both"]:
                derived["loan"] = self._compute_loan_features(declared, ocr_data)

            if request_type in ["insurance", "health", "both"]:
                derived["health"] = self._compute_health_features(declared, ocr_data)

            state["derived_features"] = derived

            if state.get("application_id"):
                save_derived_features(
                    state["application_id"],
                    derived,
                    metadata={
                        "request_id": request_id,
                        "request_type": request_type
                    }
                )

            log_agent_execution("FeatureEngineeringAgent", request_id, "completed")
            return state

        except Exception as exc:
            error_msg = f"Feature engineering failed: {exc}"
            state.setdefault("errors", []).append(error_msg)
            log_error("feature_engineering", error_msg, request_id)
            log_agent_execution("FeatureEngineeringAgent", request_id, "failed")
            return state

    def _compute_loan_features(self, declared: Dict[str, Any], ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        loan_type = (declared.get("loan_type") or declared.get("loanType") or "home").lower()
        loan_amount = _to_float(
            declared.get("loan_amount_requested")
            or declared.get("loan_amount")
            or ocr_data.get("loan_amount")
        )
        tenure_months = _to_float(
            declared.get("tenure_months")
            or declared.get("loan_tenure_months")
            or declared.get("tenure")
        )
        property_value = _to_float(
            declared.get("property_value")
            or ocr_data.get("property_value")
        )
        existing_emi = _to_float(
            declared.get("declared_existing_emi")
            or declared.get("existing_emi")
            or ocr_data.get("existing_emi")
        )
        if existing_emi is None:
            existing_emi = 0.0

        avg_salary_6m = _to_float(
            ocr_data.get("avg_salary_6m")
            or declared.get("declared_monthly_income")
        )
        if avg_salary_6m is None:
            income_annum = _to_float(
                declared.get("annual_income")
                or declared.get("income_annum")
                or ocr_data.get("income_annum")
            )
            avg_salary_6m = (income_annum / 12.0) if income_annum else None

        emi = _compute_emi(loan_amount, tenure_months, loan_type)
        foir = None
        if avg_salary_6m and avg_salary_6m > 0 and emi is not None:
            foir = (existing_emi + emi) / avg_salary_6m

        ltv = None
        if loan_amount is not None and property_value:
            ltv = loan_amount / property_value

        credit_score = _to_float(
            declared.get("credit_score")
            or declared.get("cibil_score")
            or ocr_data.get("cibil_score")
        )
        age = _to_float(declared.get("age") or ocr_data.get("age"))
        total_exp = _to_float(declared.get("total_work_experience"))
        tenure_years = _to_float(declared.get("current_company_tenure"))

        income_stability_score = _compute_income_stability(total_exp, tenure_years)
        credit_risk_bucket = _credit_bucket(credit_score)
        age_risk_bucket = _age_bucket(age)

        return {
            "loan_type": loan_type,
            "loan_amount_requested": loan_amount,
            "tenure_months": tenure_months,
            "property_value": property_value,
            "emi": emi,
            "foir": foir,
            "ltv": ltv,
            "avg_salary_6m": avg_salary_6m,
            "existing_emi": existing_emi,
            "income_stability_score": income_stability_score,
            "credit_risk_bucket": credit_risk_bucket,
            "age_risk_bucket": age_risk_bucket,
            "credit_score": credit_score
        }

    def _compute_health_features(self, declared: Dict[str, Any], ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        height_cm = _to_float(declared.get("height") or declared.get("height_cm") or ocr_data.get("height_cm"))
        weight_kg = _to_float(declared.get("weight") or declared.get("weight_kg") or ocr_data.get("weight_kg"))
        bmi = _to_float(declared.get("bmi") or ocr_data.get("bmi"))
        if bmi is None and height_cm and weight_kg:
            bmi = round(weight_kg / ((height_cm / 100.0) ** 2), 2)

        age = _to_float(declared.get("age") or ocr_data.get("age"))
        smoker = _to_bool(declared.get("smoker"))
        alcohol = (declared.get("alcohol") or "none").lower()
        pre_existing = _to_list(declared.get("pre_existing_diseases") or declared.get("pre_existing_conditions"))
        family_history = _to_list(declared.get("family_history"))
        sum_insured = _to_float(declared.get("sum_insured") or declared.get("coverage_amount"))
        deductible = _to_float(declared.get("deductible"))

        medical_risk_score = _medical_risk_score(pre_existing, family_history)
        lifestyle_risk_score = _lifestyle_risk_score(smoker, alcohol)
        overall_risk_category = _overall_risk_category(age, bmi, medical_risk_score, lifestyle_risk_score)

        return {
            "bmi": bmi,
            "age": age,
            "smoker": smoker,
            "alcohol": alcohol,
            "pre_existing_count": len(pre_existing),
            "family_history_count": len(family_history),
            "medical_risk_score": medical_risk_score,
            "lifestyle_risk_score": lifestyle_risk_score,
            "age_risk_bucket": _age_bucket(age),
            "overall_risk_category": overall_risk_category,
            "sum_insured": sum_insured,
            "deductible": deductible
        }


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ["yes", "true", "1", "y"]
    return False


def _to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _compute_emi(loan_amount: Optional[float], tenure_months: Optional[float], loan_type: str) -> Optional[float]:
    if not loan_amount or not tenure_months or tenure_months <= 0:
        return None

    annual_rate = 0.085 if loan_type == "home" else 0.14
    monthly_rate = annual_rate / 12.0
    n = tenure_months

    if monthly_rate == 0:
        return loan_amount / n

    factor = (1 + monthly_rate) ** n
    emi = loan_amount * monthly_rate * factor / (factor - 1)
    return round(emi, 2)


def _compute_income_stability(total_exp: Optional[float], tenure_years: Optional[float]) -> float:
    score = 0.5
    if total_exp is not None:
        score += min(total_exp / 20.0, 0.3)
    if tenure_years is not None:
        score += min(tenure_years / 10.0, 0.2)
    return round(min(score, 1.0), 2)


def _credit_bucket(score: Optional[float]) -> str:
    if score is None:
        return "unknown"
    if score >= 750:
        return "low"
    if score >= 650:
        return "medium"
    return "high"


def _age_bucket(age: Optional[float]) -> str:
    if age is None:
        return "unknown"
    if age < 30:
        return "low"
    if age <= 45:
        return "medium"
    if age <= 60:
        return "elevated"
    return "high"


def _medical_risk_score(pre_existing: list[str], family_history: list[str]) -> float:
    score = 0.0
    score += min(len(pre_existing) * 0.2, 0.8)
    score += min(len(family_history) * 0.1, 0.2)
    return round(min(score, 1.0), 2)


def _lifestyle_risk_score(smoker: bool, alcohol: str) -> float:
    score = 0.0
    if smoker:
        score += 0.5
    if alcohol == "moderate":
        score += 0.2
    elif alcohol == "high":
        score += 0.4
    return round(min(score, 1.0), 2)


def _overall_risk_category(
    age: Optional[float],
    bmi: Optional[float],
    medical_score: float,
    lifestyle_score: float
) -> str:
    score = medical_score + lifestyle_score
    if age is not None and age > 50:
        score += 0.2
    if bmi is not None and bmi >= 30:
        score += 0.2
    if score < 0.4:
        return "low"
    if score < 0.8:
        return "medium"
    return "high"
