"""
Onboarding Agent with OCR document processing.

This module implements document processing and field extraction using OCR.
"""

import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

from src.schemas.state import ApplicationState
from src.utils.ocr_service_factory import get_ocr_service
from src.utils.ocr_service_mock import OCRService as MockOCRService
from src.utils.logging import log_agent_execution, log_error
from src.utils.error_handling import safe_agent_wrapper
from src.utils.storage import save_ocr_data


class OnboardingAgent:
    """
    Onboarding Agent for document processing and field extraction.
    
    This agent:
    1. Processes uploaded documents using OCR
    2. Classifies document types
    3. Extracts relevant fields for loan/insurance applications
    4. Verifies document freshness
    5. Generates pre-filled form data
    """
    
    def __init__(self, groq_api_key: str = None):
        """
        Initialize Onboarding Agent.
        
        Args:
            groq_api_key: Optional Groq API key for LLM-based classification
        """
        self.ocr_service = get_ocr_service(groq_api_key=groq_api_key)
        self.mock_ocr_service = MockOCRService()
    
    def process_documents(self, state: ApplicationState) -> ApplicationState:
        """
        Main document processing pipeline.
        
        Args:
            state: Current application state
            
        Returns:
            Updated application state with extracted data
        """
        import base64
        
        request_id = state.get("request_id", "unknown")
        start_time = time.time()
        
        log_agent_execution("OnboardingAgent", request_id, "started")
        
        try:
            uploaded_docs = state.get("uploaded_documents", [])
            request_type = state["request_type"]
            
            if not uploaded_docs:
                # No documents uploaded, mark as completed (manual entry mode)
                state["onboarding_completed"] = True
                state["ocr_extracted_data"] = {}
                state["document_verification"] = {}
                
                duration_ms = (time.time() - start_time) * 1000
                log_agent_execution("OnboardingAgent", request_id, "completed", duration_ms)
                return state
            
            extracted_data = {}
            verification_status = {}
            ocr_confidence_scores = {}  # Track OCR confidence per document
            ocr_documents = []
            
            # Process each document
            for doc in uploaded_docs:
                doc_path = doc.get("file_path")
                
                # If no file_path, check for base64 content
                if not doc_path and doc.get("content_base64"):
                    try:
                        # Decode base64 and save to temporary file
                        content = base64.b64decode(doc["content_base64"])
                        
                        # Determine file extension from mime_type or name
                        mime_type = doc.get("mime_type", "")
                        name = doc.get("name", "document")
                        
                        if mime_type == "application/pdf" or name.lower().endswith(".pdf"):
                            ext = ".pdf"
                        elif mime_type.startswith("image/") or any(name.lower().endswith(e) for e in [".jpg", ".jpeg", ".png"]):
                            ext = ".jpg" if "jpeg" in mime_type or name.lower().endswith((".jpg", ".jpeg")) else ".png"
                        else:
                            ext = ".pdf"  # Default to PDF
                        
                        app_id = state.get("application_id") or "unknown"
                        output_dir = Path("temp") / "uploads" / app_id
                        output_dir.mkdir(parents=True, exist_ok=True)
                        safe_name = f"{doc.get('type', 'document')}{ext}"
                        target_path = output_dir / safe_name
                        target_path.write_bytes(content)
                        doc_path = str(target_path)
                        
                    except Exception as e:
                        log_error("onboarding", f"Failed to decode document {doc.get('name')}: {str(e)}", request_id)
                        continue
                
                if not doc_path:
                    continue
                
                ocr_service = self.ocr_service
                if not Path(doc_path).exists():
                    ocr_service = self.mock_ocr_service

                # Extract text and classify
                result = ocr_service.process_document(
                    doc_path,
                    preprocess=True,
                    classify=True
                )
                
                doc_type = result.get("document_type", doc.get("type", "unknown"))
                text = result.get("text", "")
                
                confidence = result.get("confidence", 95.0)
                
                # Log confidence scores
                ocr_confidence_scores[doc_type] = confidence
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"OCR confidence for {doc_type}: {confidence:.1f}%")
                
                # Track OCR artifacts for downstream rules/fraud checks
                ocr_documents.append({
                    "document_type": doc_type,
                    "file_path": doc_path,
                    "text": text,
                    "confidence": confidence,
                    "text_length": len(text)
                })

                # Extract fields based on request type
                if request_type in ["loan", "both"]:
                    loan_data = self._extract_loan_fields(doc_type, text, ocr_service)
                    extracted_data.update(loan_data)
                
                if request_type in ["insurance", "health", "both"]:
                    health_data = self._extract_health_fields(doc_type, text, ocr_service)
                    extracted_data.update(health_data)
                
                # Verify document freshness
                verification_status[doc_type] = self._verify_document_freshness(
                    doc_type, text
                )
            
            # Update state with extracted data and confidence scores
            state["ocr_extracted_data"] = extracted_data
            state["document_verification"] = verification_status
            state["ocr_confidence_scores"] = ocr_confidence_scores  # Add confidence tracking
            state["ocr_documents"] = ocr_documents
            
            state["onboarding_completed"] = True

            if state.get("application_id"):
                save_ocr_data(
                    state["application_id"],
                    extracted_data,
                    ocr_documents=ocr_documents,
                    metadata={
                        "request_id": request_id,
                        "request_type": request_type
                    }
                )
            
            duration_ms = (time.time() - start_time) * 1000
            log_agent_execution("OnboardingAgent", request_id, "completed", duration_ms)
        
        except Exception as e:
            error_msg = f"Onboarding processing error: {str(e)}"
            state["errors"].append(error_msg)
            log_error("onboarding", error_msg, request_id)
            
            duration_ms = (time.time() - start_time) * 1000
            log_agent_execution("OnboardingAgent", request_id, "failed", duration_ms)
        
        return state
    
    def _extract_loan_fields(self, doc_type: str, text: str, ocr_service=None) -> Dict[str, Any]:
        """
        Extract loan-specific fields from document text.
        
        Args:
            doc_type: Type of document
            text: Extracted text
            
        Returns:
            Dictionary of extracted loan fields
        """
        fields = {}
        
        ocr_service = ocr_service or self.ocr_service

        if doc_type == "cibil_report":
            # Extract CIBIL score
            cibil = ocr_service.extract_field(text, "cibil_score")
            if cibil:
                try:
                    fields["cibil_score"] = int(cibil)
                except (ValueError, TypeError):
                    pass
        
        elif doc_type == "salary_slip":
            # Extract monthly income and calculate annual
            monthly = ocr_service.extract_field(text, "monthly_income")
            if monthly:
                try:
                    monthly_val = float(str(monthly).replace(",", ""))
                    fields["income_annum"] = monthly_val * 12
                except (ValueError, TypeError):
                    pass
        
        elif doc_type in ["itr_form16", "itr", "form_16", "tds_certificate"]:
            # Extract annual income directly
            annual = ocr_service.extract_field(text, "annual_income")
            if annual:
                try:
                    fields["income_annum"] = float(str(annual).replace(",", ""))
                except (ValueError, TypeError):
                    pass
        
        elif doc_type == "bank_statement":
            # Extract bank balance
            balance = ocr_service.extract_field(text, "bank_balance")
            if balance:
                try:
                    fields["bank_asset_value"] = float(str(balance).replace(",", ""))
                except (ValueError, TypeError):
                    pass
        
        elif doc_type == "property_document":
            # Extract property value
            value = ocr_service.extract_field(text, "property_value")
            if value:
                try:
                    fields["residential_assets_value"] = float(str(value).replace(",", ""))
                except (ValueError, TypeError):
                    pass
        
        elif doc_type in ["aadhaar_card", "pan_card", "passport", "voter_id", "birth_certificate", "tenth_marksheet"]:
            # Extract age and gender
            age = ocr_service.extract_field(text, "age")
            if age:
                try:
                    fields["age"] = int(age)
                except (ValueError, TypeError):
                    pass
            
            gender = ocr_service.extract_field(text, "gender")
            if gender:
                fields["gender"] = gender

            name = ocr_service.extract_field(text, "name")
            if name:
                fields["name"] = name.strip()

            aadhaar_number = ocr_service.extract_field(text, "aadhaar_number")
            if aadhaar_number:
                fields["aadhaar_number"] = aadhaar_number.replace(" ", "")

            pan_number = ocr_service.extract_field(text, "pan_number")
            if pan_number:
                fields["pan_number"] = pan_number

            passport_number = self.ocr_service.extract_field(text, "passport_number")
            if passport_number:
                fields["passport_number"] = passport_number

            voter_id_number = self.ocr_service.extract_field(text, "voter_id_number")
            if voter_id_number:
                fields["voter_id_number"] = voter_id_number

        elif doc_type == "utility_bill":
            fields["address_proof_type"] = "utility_bill"

        elif doc_type in ["gst_certificate", "trade_license"]:
            fields["business_proof_type"] = doc_type
        
        return fields
    
    def _extract_health_fields(self, doc_type: str, text: str, ocr_service=None) -> Dict[str, Any]:
        """
        Extract health-specific fields from document text.
        
        Args:
            doc_type: Type of document
            text: Extracted text
            
        Returns:
            Dictionary of extracted health fields
        """
        fields = {}
        ocr_service = ocr_service or self.ocr_service
        
        if doc_type == "diagnostic_report":
            # Extract HbA1c for diabetes detection
            hba1c = ocr_service.extract_field(text, "hba1c")
            if hba1c:
                try:
                    hba1c_val = float(hba1c)
                    fields["hba1c"] = hba1c_val
                    fields["diabetes"] = 1 if hba1c_val >= 6.5 else 0
                except (ValueError, TypeError):
                    pass
            
            # Extract cholesterol
            cholesterol = ocr_service.extract_field(text, "cholesterol")
            if cholesterol:
                try:
                    fields["cholesterol"] = float(cholesterol)
                except (ValueError, TypeError):
                    pass
            
            # Extract blood sugar
            blood_sugar = ocr_service.extract_field(text, "blood_sugar")
            if blood_sugar:
                try:
                    fields["blood_sugar"] = float(blood_sugar)
                except (ValueError, TypeError):
                    pass
        
        elif doc_type == "physical_exam":
            # Extract height and weight for BMI calculation
            height = ocr_service.extract_field(text, "height")
            weight = ocr_service.extract_field(text, "weight")
            
            if height and weight:
                try:
                    height_cm = float(height)
                    weight_kg = float(weight)
                    bmi = weight_kg / ((height_cm / 100) ** 2)
                    fields["bmi"] = round(bmi, 2)
                    fields["height_cm"] = height_cm
                    fields["weight_kg"] = weight_kg
                except (ValueError, TypeError, ZeroDivisionError):
                    pass
            
            # Extract blood pressure
            bp = ocr_service.extract_field(text, "blood_pressure")
            if bp and isinstance(bp, tuple) and len(bp) == 2:
                try:
                    systolic, diastolic = bp
                    fields["systolic_bp"] = int(systolic)
                    fields["diastolic_bp"] = int(diastolic)
                    # Flag high blood pressure
                    fields["bloodpressure"] = 1 if int(systolic) >= 140 or int(diastolic) >= 90 else 0
                except (ValueError, TypeError):
                    pass
            
            # Extract heart rate
            hr = ocr_service.extract_field(text, "heart_rate")
            if hr:
                try:
                    fields["heart_rate"] = int(hr)
                except (ValueError, TypeError):
                    pass
        
        elif doc_type == "medical_declaration":
            # Extract smoker status and exercise habits
            # This would typically use LLM for complex extraction
            # For now, use simple keyword matching
            text_lower = text.lower()
            
            # Smoker status
            if "smoker: yes" in text_lower or "smoking: yes" in text_lower:
                fields["smoker"] = True
            elif "smoker: no" in text_lower or "smoking: no" in text_lower or "non-smoker" in text_lower:
                fields["smoker"] = False
            
            # Exercise habits
            if "regular exercise: yes" in text_lower or "exercise: yes" in text_lower:
                fields["regular_ex"] = True
            elif "regular exercise: no" in text_lower or "exercise: no" in text_lower:
                fields["regular_ex"] = False
            
            # Pre-existing conditions
            if "pre-existing conditions: none" in text_lower or "pre-existing: none" in text_lower:
                fields["pre_existing_conditions"] = []
            elif "diabetes" in text_lower:
                fields["pre_existing_conditions"] = ["diabetes"]
        
        elif doc_type == "family_medical_records":
            # Extract hereditary diseases
            text_lower = text.lower()
            hereditary_keywords = ["diabetes", "heart disease", "cancer", "hypertension", "stroke"]
            found_conditions = [kw for kw in hereditary_keywords if kw in text_lower]
            
            if found_conditions:
                fields["family_history"] = found_conditions
                fields["hereditary_diseases"] = True
            else:
                fields["hereditary_diseases"] = False
        
        elif doc_type in ["aadhaar_card", "pan_card", "passport", "voter_id", "birth_certificate", "tenth_marksheet"]:
            # Extract age and gender
            age = ocr_service.extract_field(text, "age")
            if age:
                try:
                    fields["age"] = int(age)
                except (ValueError, TypeError):
                    pass
            
            gender = ocr_service.extract_field(text, "gender")
            if gender:
                fields["gender"] = gender

            name = ocr_service.extract_field(text, "name")
            if name:
                fields["name"] = name.strip()

            aadhaar_number = self.ocr_service.extract_field(text, "aadhaar_number")
            if aadhaar_number:
                fields["aadhaar_number"] = aadhaar_number.replace(" ", "")

            pan_number = self.ocr_service.extract_field(text, "pan_number")
            if pan_number:
                fields["pan_number"] = pan_number

            passport_number = self.ocr_service.extract_field(text, "passport_number")
            if passport_number:
                fields["passport_number"] = passport_number

            voter_id_number = self.ocr_service.extract_field(text, "voter_id_number")
            if voter_id_number:
                fields["voter_id_number"] = voter_id_number

        elif doc_type == "utility_bill":
            fields["address_proof_type"] = "utility_bill"
        
        return fields
    
    def _verify_document_freshness(self, doc_type: str, text: str) -> Dict[str, Any]:
        """
        Verify document is recent and valid.
        
        Args:
            doc_type: Type of document
            text: Extracted text
            
        Returns:
            Dictionary with verification status
        """
        # Extract date from document
        date_str = self.ocr_service.extract_field(text, "date")
        
        if not date_str:
            return {
                "verified": False,
                "reason": "No date found in document",
                "is_fresh": False
            }
        
        try:
            # Parse date (try multiple formats)
            doc_date = self._parse_date(date_str)
            
            if not doc_date:
                return {
                    "verified": False,
                    "reason": "Could not parse document date",
                    "is_fresh": False
                }
            
            # Calculate age in days
            age_days = (datetime.now() - doc_date).days
            
            # Determine freshness threshold based on document type
            if doc_type in ["diagnostic_report", "physical_exam", "medical_declaration", 
                           "family_medical_records", "ecg_report"]:
                # Medical documents: 6 months (180 days)
                threshold_days = 180
            elif doc_type in ["salary_slip", "bank_statement"]:
                # Financial documents: 6 months (180 days)
                threshold_days = 180
            elif doc_type in ["itr_form16", "itr", "form_16", "tds_certificate"]:
                # Tax documents: 2 years (730 days)
                threshold_days = 730
            elif doc_type in ["cibil_report"]:
                # Credit reports: 1 month (30 days)
                threshold_days = 30
            elif doc_type in ["utility_bill"]:
                # Address proof: 2 months (60 days)
                threshold_days = 60
            elif doc_type in ["discharge_summary", "prescription_history", "medical_history"]:
                # Medical history and discharge summaries: 5 years (1825 days)
                threshold_days = 1825
            elif doc_type in ["gst_certificate", "trade_license"]:
                # Business proof: 1 year (365 days)
                threshold_days = 365
            else:
                # Other documents: 1 year (365 days)
                threshold_days = 365
            
            is_fresh = age_days <= threshold_days
            
            return {
                "verified": True,
                "document_date": doc_date.isoformat(),
                "age_days": age_days,
                "threshold_days": threshold_days,
                "is_fresh": is_fresh,
                "reason": "Document is fresh" if is_fresh else f"Document is {age_days} days old (threshold: {threshold_days} days)"
            }
        
        except Exception as e:
            return {
                "verified": False,
                "reason": f"Date verification error: {str(e)}",
                "is_fresh": False
            }
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string in various formats.
        
        Args:
            date_str: Date string
            
        Returns:
            datetime object or None
        """
        # Try multiple date formats
        formats = [
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%y",
            "%d/%m/%y",
            "%d %B %Y",
            "%d %b %Y",
            "%B %d, %Y",
            "%b %d, %Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
