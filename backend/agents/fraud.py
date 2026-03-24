"""
Fraud Agent for OCR document fraud checks.
"""

import logging
from typing import Any, Dict, List, Optional

from src.schemas.state import ApplicationState
from src.utils.fraud_detector import FraudDetector
from src.utils.logging import log_agent_execution, log_error
from src.utils.storage import save_validation_report

logger = logging.getLogger(__name__)


class FraudAgent:
    """Runs OCR fraud checks and records flags without blocking the flow."""

    def __init__(self) -> None:
        self.detector = FraudDetector()

    def check_fraud(self, state: ApplicationState) -> ApplicationState:
        request_id = state.get("request_id", "unknown")
        log_agent_execution("FraudAgent", request_id, "started")

        try:
            ocr_documents = state.get("ocr_documents", []) or []
            declared = state.get("declared_data", {}) or {}
            ocr_data = state.get("ocr_extracted_data", {}) or {}
            doc_results: List[Dict[str, Any]] = []

            for doc in ocr_documents:
                file_path = doc.get("file_path")
                text = doc.get("text", "")
                doc_type = doc.get("document_type") or doc.get("type") or "unknown"

                if not file_path:
                    continue

                analysis = self.detector.analyze_document(
                    file_path=file_path,
                    extracted_text=text,
                    document_type=doc_type
                )
                analysis["document_type"] = doc_type
                analysis["file_path"] = file_path
                doc_results.append(analysis)

            anomaly_flags = self._compare_declared_vs_ocr(declared, ocr_data)
            fraud_score = self._aggregate_fraud_score(doc_results, anomaly_flags)
            confidence_level = self._confidence_level(anomaly_flags)

            fraud_summary = {
                "fraud_risk_score": fraud_score,
                "anomaly_flags": anomaly_flags,
                "confidence_level": confidence_level,
                "document_checks": doc_results
            }

            state["fraud_results"] = fraud_summary

            validation_report = state.get("validation_report", {}) or {}
            validation_report["fraud_analysis"] = fraud_summary
            state["validation_report"] = validation_report

            if state.get("application_id"):
                save_validation_report(
                    state["application_id"],
                    validation_report,
                    metadata={
                        "request_id": request_id,
                        "request_type": state.get("request_type")
                    }
                )

            log_agent_execution("FraudAgent", request_id, "completed")
            return state

        except Exception as exc:
            error_msg = f"Fraud check failed: {exc}"
            state.setdefault("errors", []).append(error_msg)
            log_error("fraud", error_msg, request_id)
            log_agent_execution("FraudAgent", request_id, "failed")
            return state

    def _compare_declared_vs_ocr(self, declared: Dict[str, Any], ocr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        checks = [
            ("declared_monthly_income", "avg_salary_6m"),
            ("declared_existing_emi", "detected_existing_emi"),
            ("age", "age"),
            ("salary_slip_net", "bank_salary_credits")
        ]

        health_checks = [
            ("pre_existing_diseases", "diagnosed_conditions"),
            ("age", "age")
        ]

        anomalies: List[Dict[str, Any]] = []

        for declared_key, ocr_key in checks:
            anomaly = _compare_numeric(declared, ocr_data, declared_key, ocr_key)
            if anomaly:
                anomalies.append(anomaly)

        for declared_key, ocr_key in health_checks:
            if declared_key in ["pre_existing_diseases"]:
                mismatch = _compare_list(declared, ocr_data, declared_key, ocr_key)
                if mismatch:
                    anomalies.append(mismatch)
            else:
                anomaly = _compare_numeric(declared, ocr_data, declared_key, ocr_key)
                if anomaly:
                    anomalies.append(anomaly)

        return anomalies

    def _aggregate_fraud_score(self, doc_results: List[Dict[str, Any]], anomalies: List[Dict[str, Any]]) -> float:
        score = 0.0
        if doc_results:
            doc_scores = [float(result.get("fraud_score", 0.0)) for result in doc_results]
            score += sum(doc_scores) / max(len(doc_scores), 1)

        score += min(len(anomalies) * 15.0, 60.0)
        return round(min(score, 100.0), 2)

    def _confidence_level(self, anomalies: List[Dict[str, Any]]) -> str:
        if len(anomalies) >= 3:
            return "high"
        if len(anomalies) >= 1:
            return "medium"
        return "low"


def _compare_numeric(
    declared: Dict[str, Any],
    ocr_data: Dict[str, Any],
    declared_key: str,
    ocr_key: str
) -> Optional[Dict[str, Any]]:
    declared_val = _to_float(declared.get(declared_key))
    ocr_val = _to_float(ocr_data.get(ocr_key))
    if declared_val is None or ocr_val is None:
        return None
    if declared_val == 0:
        return None

    diff_pct = abs(declared_val - ocr_val) / abs(declared_val)
    if diff_pct > 0.10:
        return {
            "field": declared_key,
            "declared": declared_val,
            "ocr": ocr_val,
            "diff_pct": round(diff_pct, 3)
        }
    return None


def _compare_list(
    declared: Dict[str, Any],
    ocr_data: Dict[str, Any],
    declared_key: str,
    ocr_key: str
) -> Optional[Dict[str, Any]]:
    declared_vals = _to_list(declared.get(declared_key))
    ocr_vals = _to_list(ocr_data.get(ocr_key))
    if not declared_vals or not ocr_vals:
        return None

    declared_set = {item.lower() for item in declared_vals}
    ocr_set = {item.lower() for item in ocr_vals}
    missing = sorted(list(ocr_set - declared_set))
    if missing:
        return {
            "field": declared_key,
            "declared": declared_vals,
            "ocr": ocr_vals,
            "missing_declared": missing
        }
    return None


def _to_float(value: Any) -> Optional[float]:
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
