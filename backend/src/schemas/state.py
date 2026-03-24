from typing import Any, TypedDict


class ApplicationState(TypedDict, total=False):
    application_id: str
    request_id: str
    request_type: str
    loan_type: str
    applicant_data: dict[str, Any]
    declared_data: dict[str, Any]
    uploaded_documents: list[dict[str, Any]]
    ocr_extracted_data: dict[str, Any]
    ocr_documents: list[dict[str, Any]]
    ocr_confidence_scores: dict[str, float]
    document_verification: dict[str, Any]
    derived_features: dict[str, Any]
    model_output: dict[str, Any]
    loan_prediction: dict[str, Any]
    insurance_prediction: dict[str, Any]
    loan_explanation: str
    insurance_explanation: str
    loan_verification: dict[str, Any]
    insurance_verification: dict[str, Any]
    compliance_passed: bool
    compliance_violations: list[dict[str, Any]]
    fraud_results: dict[str, Any]
    kyc_verified: bool
    rejected: bool
    rejection_reason: str
    errors: list[str]
    completed: bool
