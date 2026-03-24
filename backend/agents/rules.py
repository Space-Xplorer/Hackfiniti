"""
Rules Agent implementing underwriting rule engine.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.schemas.state import ApplicationState
from src.utils.logging import log_agent_execution, log_error
from src.utils.storage import save_validation_report
from src.utils.llm_helpers import parse_json_response

logger = logging.getLogger(__name__)

try:
    from langchain_groq import ChatGroq
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


class RulesAgent:
    """Rule engine for loan and health underwriting pre-screen."""

    def __init__(self, rules_dir: str = "src/rules") -> None:
        rules_root = os.getenv("RULES_DIR", rules_dir)
        self.rules_dir = Path(rules_root)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.llm = None
        if self.groq_api_key and LLM_AVAILABLE:
            try:
                self.llm = ChatGroq(
                    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
                    temperature=float(os.getenv("GROQ_TEMPERATURE", "0.2")),
                    api_key=self.groq_api_key
                )
                logger.info("RulesAgent LLM initialized")
            except Exception as exc:
                logger.warning(f"RulesAgent LLM init failed: {exc}")

    def check_rules(self, state: ApplicationState) -> ApplicationState:
        request_id = state.get("request_id", "unknown")
        log_agent_execution("RulesAgent", request_id, "started")

        try:
            request_type = state.get("request_type")
            declared = state.get("declared_data", {}) or {}
            ocr_data = state.get("ocr_extracted_data", {}) or {}
            derived = state.get("derived_features", {}) or {}
            ocr_documents = state.get("ocr_documents", []) or []

            rules_text = self._load_rules_text()
            extracted_snapshots = self._build_text_snapshots(ocr_documents)
            state["rules_extracted_texts"] = extracted_snapshots

            failed_rules: List[Dict[str, Any]] = []
            evidence: List[Dict[str, Any]] = []

            if request_type in ["loan", "both"]:
                loan_failed, loan_evidence = self._apply_loan_rules(declared, ocr_data, derived)
                failed_rules.extend(loan_failed)
                evidence.extend(loan_evidence)

            if request_type in ["insurance", "health", "both"]:
                health_failed, health_evidence = self._apply_health_rules(declared, ocr_data, derived)
                failed_rules.extend(health_failed)
                evidence.extend(health_evidence)

            llm_violations = []
            if rules_text and extracted_snapshots:
                llm_violations = self._evaluate_with_llm(rules_text, extracted_snapshots)

            failed_rules.extend(llm_violations)

            rules_passed = len(failed_rules) == 0
            state["rules_checked"] = True
            state["rules_passed"] = rules_passed
            state["rules_violations"] = failed_rules

            validation_report = state.get("validation_report", {}) or {}
            validation_report["rule_engine"] = {
                "rule_status": "pass" if rules_passed else "fail",
                "failed_rules": failed_rules,
                "evidence_snippets": evidence,
                "rules_source": str(self.rules_dir)
            }
            state["validation_report"] = validation_report

            if not rules_passed:
                state["rejected"] = True
                state["rejection_reason"] = self._format_rejection_reason(failed_rules)

            if state.get("application_id"):
                save_validation_report(
                    state["application_id"],
                    validation_report,
                    metadata={
                        "request_id": request_id,
                        "request_type": request_type
                    }
                )

            log_agent_execution("RulesAgent", request_id, "completed")
            return state

        except Exception as exc:
            error_msg = f"Rules check failed: {exc}"
            state.setdefault("errors", []).append(error_msg)
            log_error("rules", error_msg, request_id)
            state["rules_checked"] = True
            state["rules_passed"] = True
            state["rules_violations"] = []
            log_agent_execution("RulesAgent", request_id, "failed")
            return state

    def _load_rules_text(self) -> str:
        if not self.rules_dir.exists():
            return ""

        parts: List[str] = []

        for path in sorted(self.rules_dir.iterdir()):
            if path.suffix.lower() == ".txt":
                parts.append(self._read_text_file(path))
            elif path.suffix.lower() == ".pdf":
                parts.append(self._read_pdf_file(path))

        return "\n\n".join([p for p in parts if p])

    def _read_text_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Failed to read {path.name}: {exc}")
            return ""

    def _read_pdf_file(self, path: Path) -> str:
        if not PDF_AVAILABLE:
            logger.warning("PyPDF2 not available for PDF rule parsing")
            return ""

        try:
            text_chunks: List[str] = []
            with open(path, "rb") as handle:
                reader = PyPDF2.PdfReader(handle)
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    if page_text:
                        text_chunks.append(page_text)
            return "\n".join(text_chunks)
        except Exception as exc:
            logger.warning(f"Failed to read PDF {path.name}: {exc}")
            return ""

    def _build_text_snapshots(self, ocr_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        snapshots: List[Dict[str, Any]] = []
        for doc in ocr_documents:
            text = (doc.get("text") or "").strip()
            if not text:
                continue
            snapshots.append({
                "document_type": doc.get("document_type") or doc.get("type"),
                "file_path": doc.get("file_path"),
                "confidence": doc.get("confidence"),
                "text_excerpt": text[:2000]
            })
        return snapshots

    def _evaluate_with_llm(self, rules_text: str, snapshots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.llm:
            return []

        prompt = (
            "You are an underwriting rules auditor.\n\n"
            "Rules (authoritative):\n"
            f"{rules_text}\n\n"
            "Applicant document excerpts (OCR):\n"
            f"{snapshots}\n\n"
            "Task: Identify any violations in the applicant documents against the rules.\n"
            "Return JSON array of violations with fields: rule, reason, severity.\n"
            "If no violations, return [].\n"
        )

        try:
            response = self.llm.invoke(prompt).content
            violations = parse_json_response(response, default=[])
            if isinstance(violations, list):
                return violations
            return []
        except Exception as e:
            logger.warning(f"LLM rule audit failed (rate limit or error): {e}. Proceeding without LLM validation.")
            return []

    def _format_rejection_reason(self, violations: List[Dict[str, Any]]) -> str:
        if not violations:
            return "Rule engine rejection"
        reasons = []
        for violation in violations:
            rule = violation.get("rule", "Rule")
            reason = violation.get("reason", "Violation detected")
            reasons.append(f"- {rule}: {reason}")
        return "Application rejected due to rule violations:\n" + "\n".join(reasons)

    def _apply_loan_rules(
        self,
        declared: Dict[str, Any],
        ocr_data: Dict[str, Any],
        derived: Dict[str, Any]
    ) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
        failed: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []

        loan_type = (declared.get("loan_type") or "home").lower()
        foir_threshold = 0.6 if loan_type == "home" else 0.5
        foir = _get_loan_metric(declared, ocr_data, derived, "foir")
        if foir is None:
            foir = _compute_foir(declared, ocr_data, loan_type)
        if foir is not None:
            evidence.append({"rule": "foir_threshold", "observed": foir, "threshold": foir_threshold})
            if foir >= foir_threshold:
                failed.append({
                    "rule": "FOIR",
                    "reason": f"FOIR {foir:.2f} exceeds threshold {foir_threshold:.2f}",
                    "severity": "HIGH"
                })

        ltv = _get_loan_metric(declared, ocr_data, derived, "ltv")
        if ltv is None:
            ltv = _compute_ltv(declared, ocr_data)
        if ltv is not None:
            evidence.append({"rule": "ltv_threshold", "observed": ltv, "threshold": 0.9})
            if ltv > 0.9:
                failed.append({
                    "rule": "LTV",
                    "reason": f"LTV {ltv:.2f} exceeds 0.90",
                    "severity": "HIGH"
                })

        credit_score = _pick_value(
            declared.get("credit_score"),
            declared.get("cibil_score"),
            ocr_data.get("cibil_score")
        )
        credit_score = _to_float(credit_score)
        if credit_score is not None:
            evidence.append({"rule": "credit_score", "observed": credit_score, "threshold": 500})
            if credit_score < 500:
                failed.append({
                    "rule": "Credit Score",
                    "reason": f"Credit score {credit_score:.0f} below 500",
                    "severity": "HIGH"
                })

        age = _to_float(_pick_value(declared.get("age"), ocr_data.get("age")))
        tenure_months = _to_float(_pick_value(
            declared.get("tenure_months"),
            declared.get("loan_tenure_months"),
            declared.get("tenure")
        ))
        retirement_age = _to_float(declared.get("retirement_age") or 60)

        if age is not None and tenure_months is not None:
            remaining_years = retirement_age - age
            if remaining_years < (tenure_months / 12.0):
                adjusted_months = max(int(remaining_years * 12), 0)
                evidence.append({
                    "rule": "retirement_tenure_adjustment",
                    "observed": tenure_months,
                    "adjusted": adjusted_months,
                    "retirement_age": retirement_age
                })

        return failed, evidence

    def _apply_health_rules(
        self,
        declared: Dict[str, Any],
        ocr_data: Dict[str, Any],
        derived: Dict[str, Any]
    ) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
        failed: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []

        pre_existing = declared.get("pre_existing_diseases") or declared.get("pre_existing_conditions")
        pre_existing_count = len(_to_list(pre_existing))
        if pre_existing_count >= 3:
            evidence.append({
                "rule": "pre_existing_diseases_risk",
                "observed": pre_existing_count,
                "note": "High PED count increases risk"
            })

        return failed, evidence


def _get_loan_metric(
    declared: Dict[str, Any],
    ocr_data: Dict[str, Any],
    derived: Dict[str, Any],
    key: str
) -> Optional[float]:
    if "loan" in derived and isinstance(derived["loan"], dict):
        if key in derived["loan"]:
            return _to_float(derived["loan"].get(key))
    return _to_float(_pick_value(declared.get(key), ocr_data.get(key)))


def _compute_foir(declared: Dict[str, Any], ocr_data: Dict[str, Any], loan_type: str) -> Optional[float]:
    loan_amount = _to_float(_pick_value(
        declared.get("loan_amount_requested"),
        declared.get("loan_amount"),
        ocr_data.get("loan_amount")
    ))
    tenure_months = _to_float(_pick_value(
        declared.get("tenure_months"),
        declared.get("loan_tenure_months"),
        declared.get("tenure")
    ))
    existing_emi = _to_float(_pick_value(
        declared.get("declared_existing_emi"),
        declared.get("existing_emi"),
        ocr_data.get("detected_existing_emi"),
        ocr_data.get("existing_emi")
    )) or 0.0

    avg_salary_6m = _to_float(_pick_value(
        ocr_data.get("avg_salary_6m"),
        declared.get("declared_monthly_income"),
        declared.get("monthly_income")
    ))
    if avg_salary_6m is None:
        income_annum = _to_float(_pick_value(
            declared.get("annual_income"),
            declared.get("income_annum"),
            ocr_data.get("income_annum")
        ))
        avg_salary_6m = (income_annum / 12.0) if income_annum else None

    emi = _compute_emi(loan_amount, tenure_months, loan_type)
    if avg_salary_6m and avg_salary_6m > 0 and emi is not None:
        return (existing_emi + emi) / avg_salary_6m
    return None


def _compute_ltv(declared: Dict[str, Any], ocr_data: Dict[str, Any]) -> Optional[float]:
    loan_amount = _to_float(_pick_value(
        declared.get("loan_amount_requested"),
        declared.get("loan_amount"),
        ocr_data.get("loan_amount")
    ))
    property_value = _to_float(_pick_value(
        declared.get("property_value"),
        ocr_data.get("property_value")
    ))
    if loan_amount is None or not property_value:
        return None
    return loan_amount / property_value


def _compute_emi(loan_amount: Optional[float], tenure_months: Optional[float], loan_type: str) -> Optional[float]:
    if not loan_amount or not tenure_months or tenure_months <= 0:
        return None

    annual_rate = 0.085 if loan_type == "home" else 0.14
    monthly_rate = annual_rate / 12.0
    n = tenure_months

    if monthly_rate == 0:
        return loan_amount / n

    factor = (1 + monthly_rate) ** n
    return loan_amount * monthly_rate * factor / (factor - 1)


def _pick_value(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
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
