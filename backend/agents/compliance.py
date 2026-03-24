"""
Compliance Agent with RAG for regulatory rules.

This module implements regulatory compliance checking using RAG over USDA/IRDAI PDFs.
"""

import asyncio
import os
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from src.schemas.state import ApplicationState
from src.utils.llm_helpers import parse_json_response
from src.utils.logging import log_agent_execution, log_error

# Try to import RAG dependencies lazily
try:
    from langchain_groq import ChatGroq
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning("RAG dependencies not available. Compliance agent will use rule-based checking.")


class ComplianceAgent:
    """
    Compliance Agent for regulatory rules validation.
    
    This agent validates applications against regulatory rules from USDA/IRDAI
    using RAG (Retrieval-Augmented Generation) for intelligent rule checking.
    """
    
    def __init__(self, groq_api_key: Optional[str] = None, rules_dir: str = "src/rules"):
        """
        Initialize Compliance Agent.
        
        Args:
            groq_api_key: Groq API key for LLM
            rules_dir: Directory containing regulatory rules files
        """
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.rules_dir = Path(rules_dir)
        self.bypass_compliance = os.getenv("BYPASS_COMPLIANCE", "false").lower() == "true"
        
        # Initialize LLM if available
        self.llm = None
        if self.groq_api_key and RAG_AVAILABLE:
            try:
                self.llm = ChatGroq(
                    model="openai/gpt-oss-20b",
                    temperature=0.1,  # Very low for strict rule interpretation
                    api_key=self.groq_api_key
                )
                logging.info("Compliance LLM initialized")
            except Exception as e:
                logging.warning(f"Failed to initialize LLM: {e}")
        
        # Load rules and create vector store
        self.rules_db = None
        if RAG_AVAILABLE:
            self.rules_db = self._load_rules()
    
    def _load_rules(self) -> Optional[Any]:
        """
        Load regulatory rules from files and create FAISS vector store.
        
        Returns:
            FAISS vector store or None
        """
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain.docstore.document import Document
            
            documents = []
            
            # Load USDA loan rules
            usda_path = self.rules_dir / "usda_loan_rules.txt"
            if usda_path.exists():
                with open(usda_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    doc = Document(page_content=content, metadata={"source": "USDA", "type": "loan"})
                    documents.append(doc)
                    logging.info(f"Loaded USDA rules: {len(content)} characters")
            
            # Load IRDAI insurance rules
            irdai_path = self.rules_dir / "irdai_insurance_rules.txt"
            if irdai_path.exists():
                with open(irdai_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    doc = Document(page_content=content, metadata={"source": "IRDAI", "type": "insurance"})
                    documents.append(doc)
                    logging.info(f"Loaded IRDAI rules: {len(content)} characters")
            
            if not documents:
                logging.warning("No regulatory rules files found")
                return None

            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n## ", "\n### ", "\n\n", "\n", " "]
            )
            splits = text_splitter.split_documents(documents)
            logging.info(f"Split rules into {len(splits)} chunks")
            
            # Create embeddings and vector store
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            vectorstore = FAISS.from_documents(splits, embeddings)
            logging.info("FAISS vector store created")
            
            return vectorstore
        
        except Exception as e:
            logging.error(f"Failed to load rules: {e}")
            return None
    
    def check_compliance(self, state: ApplicationState) -> ApplicationState:
        """
        Check application compliance against regulatory rules.
        
        Args:
            state: Current application state
            
        Returns:
            Updated application state with compliance results
        """
        request_id = state.get("request_id", "unknown")
        start_time = time.time()
        
        log_agent_execution("ComplianceAgent", request_id, "started")
        
        try:
            # Check if compliance is bypassed
            if self.bypass_compliance:
                logging.info(f"Compliance check bypassed for {request_id}")
                state["compliance_checked"] = True
                state["compliance_passed"] = True
                state["compliance_violations"] = []
                
                duration_ms = (time.time() - start_time) * 1000
                log_agent_execution("ComplianceAgent", request_id, "completed", duration_ms)
                return state
            
            request_type = state["request_type"]
            applicant_data = state.get("declared_data") or state.get("applicant_data") or {}
            loan_type = state.get("loan_type")
            
            violations = []
            
            # Check loan compliance
            if request_type in ["loan", "both"]:
                loan_violations = self._check_loan_compliance(applicant_data, loan_type)
                violations.extend(loan_violations)
            
            # Check insurance compliance
            if request_type in ["insurance", "both"]:
                insurance_violations = self._check_insurance_compliance(applicant_data)
                violations.extend(insurance_violations)
            
            # Update state
            state["compliance_checked"] = True
            state["compliance_violations"] = violations
            
            # Determine if compliance passed (only CRITICAL violations cause rejection)
            critical_violations = [v for v in violations if v.get("severity") == "CRITICAL"]
            
            if critical_violations:
                state["compliance_passed"] = False
                state["rejected"] = True
                state["rejection_reason"] = self._format_rejection_reason(critical_violations)
            else:
                state["compliance_passed"] = True
            
            duration_ms = (time.time() - start_time) * 1000
            log_agent_execution("ComplianceAgent", request_id, "completed", duration_ms)
        
        except Exception as e:
            error_msg = f"Compliance check error: {str(e)}"
            state["errors"].append(error_msg)
            log_error("compliance", error_msg, request_id)
            
            # Default to passing on error (fail-open for availability)
            state["compliance_checked"] = True
            state["compliance_passed"] = True
            state["compliance_violations"] = []
            
            duration_ms = (time.time() - start_time) * 1000
            log_agent_execution("ComplianceAgent", request_id, "failed", duration_ms)
        
        return state
    
    async def check_compliance_async(self, state: ApplicationState) -> ApplicationState:
        """
        Check application compliance against regulatory rules asynchronously.
        
        Args:
            state: Current application state
            
        Returns:
            Updated application state with compliance results
        """
        request_id = state.get("request_id", "unknown")
        start_time = time.time()
        
        log_agent_execution("ComplianceAgent", request_id, "started (async)")
        
        try:
            # Check if compliance is bypassed
            if self.bypass_compliance:
                logging.info(f"Compliance check bypassed for {request_id}")
                state["compliance_checked"] = True
                state["compliance_passed"] = True
                state["compliance_violations"] = []
                
                duration_ms = (time.time() - start_time) * 1000
                log_agent_execution("ComplianceAgent", request_id, "completed (async)", duration_ms)
                return state
            
            request_type = state["request_type"]
            applicant_data = state.get("declared_data") or state.get("applicant_data") or {}
            loan_type = state.get("loan_type")
            
            violations = []
            
            # Check if we can use RAG for async checks
            if self.llm and self.rules_db:
                # For "both" request type, run checks in parallel
                if request_type == "both":
                    loan_task = self._check_loan_compliance_rag_async(applicant_data, loan_type)
                    insurance_task = self._check_insurance_compliance_rag_async(applicant_data)
                    
                    loan_violations, insurance_violations = await asyncio.gather(loan_task, insurance_task)
                    violations.extend(loan_violations)
                    violations.extend(insurance_violations)
                elif request_type == "loan":
                    loan_violations = await self._check_loan_compliance_rag_async(applicant_data, loan_type)
                    violations.extend(loan_violations)
                elif request_type == "insurance":
                    insurance_violations = await self._check_insurance_compliance_rag_async(applicant_data)
                    violations.extend(insurance_violations)
            else:
                # Fall back to sync rule-based checking
                if request_type in ["loan", "both"]:
                    loan_violations = self._check_loan_compliance_rules(applicant_data, loan_type)
                    violations.extend(loan_violations)
                
                if request_type in ["insurance", "both"]:
                    insurance_violations = self._check_insurance_compliance_rules(applicant_data)
                    violations.extend(insurance_violations)
            
            # Update state
            state["compliance_checked"] = True
            state["compliance_violations"] = violations
            
            # Determine if compliance passed (only CRITICAL violations cause rejection)
            critical_violations = [v for v in violations if v.get("severity") == "CRITICAL"]
            
            if critical_violations:
                state["compliance_passed"] = False
                state["rejected"] = True
                state["rejection_reason"] = self._format_rejection_reason(critical_violations)
            else:
                state["compliance_passed"] = True
            
            duration_ms = (time.time() - start_time) * 1000
            log_agent_execution("ComplianceAgent", request_id, "completed (async)", duration_ms)
        
        except Exception as e:
            error_msg = f"Async compliance check error: {str(e)}"
            state["errors"].append(error_msg)
            log_error("compliance", error_msg, request_id)
            
            # Default to passing on error (fail-open for availability)
            state["compliance_checked"] = True
            state["compliance_passed"] = True
            state["compliance_violations"] = []
            
            duration_ms = (time.time() - start_time) * 1000
            log_agent_execution("ComplianceAgent", request_id, "failed (async)", duration_ms)
        
        return state
    
    def _check_loan_compliance(self, data: Dict[str, Any], loan_type: str) -> List[Dict[str, str]]:
        """
        Check loan application against USDA/banking rules.
        
        Args:
            data: Applicant data
            loan_type: Type of loan
            
        Returns:
            List of violations
        """
        violations = []

        # Always apply rule-based checks
        violations.extend(self._check_loan_compliance_rules(data, loan_type))

        # Add RAG violations if available
        if self.llm and self.rules_db:
            violations.extend(self._check_loan_compliance_rag(data, loan_type))

        return violations
    
    def _check_loan_compliance_rag(self, data: Dict[str, Any], loan_type: str) -> List[Dict[str, str]]:
        """
        Check loan compliance using RAG.
        
        Args:
            data: Applicant data
            loan_type: Type of loan
            
        Returns:
            List of violations
        """
        try:
            # Retrieve relevant rules
            query = f"What are the eligibility requirements for {loan_type} loan approval? Include credit score, income, debt, age requirements."
            relevant_docs = self.rules_db.similarity_search(query, k=5)
            
            # Format rules for prompt
            rules_text = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Create prompt for LLM
            prompt = f"""You are a regulatory compliance officer checking a loan application against USDA rules.

Loan Type: {loan_type}

Applicant Data:
- CIBIL Score: {data.get('cibil_score', 'Not provided')}
- Annual Income: ₹{data.get('annual_income', data.get('income_annum', 'Not provided'))}
- Loan Amount: ₹{data.get('loan_amount', 'Not provided')}
- Existing Debt: ₹{data.get('existing_debt', 'Not provided')}
- Age: {data.get('age', 'Not provided')}
- Employment Type: {data.get('employment_type', 'Not provided')}
- Employment Years: {data.get('employment_years', 'Not provided')}

Relevant Regulatory Rules:
{rules_text}

Task: Identify any CRITICAL or HIGH severity violations. For each violation, provide:
1. Rule violated (exact rule number if available)
2. Reason for violation (be specific)
3. Severity (CRITICAL or HIGH only)

Return as JSON array: [{{"rule": "...", "reason": "...", "severity": "CRITICAL|HIGH"}}]
If no CRITICAL or HIGH violations, return empty array: []

IMPORTANT: Only flag actual violations. If data is "Not provided", do not flag as violation unless the rule explicitly requires it.
"""
            
            response = self.llm.invoke(prompt).content
            
            violations_data = parse_json_response(response, default=[])
            if isinstance(violations_data, list):
                return violations_data
            logging.warning(f"Could not parse LLM response: {response[:100]}")
            return []
        
        except Exception as e:
            logging.error(f"RAG compliance check failed: {e}")
            return []
    
    async def _check_loan_compliance_rag_async(self, data: Dict[str, Any], loan_type: str) -> List[Dict[str, str]]:
        """
        Check loan compliance using RAG asynchronously.
        
        Args:
            data: Applicant data
            loan_type: Type of loan
            
        Returns:
            List of violations
        """
        try:
            # Retrieve relevant rules
            query = f"What are the eligibility requirements for {loan_type} loan approval? Include credit score, income, debt, age requirements."
            relevant_docs = self.rules_db.similarity_search(query, k=5)
            
            # Format rules for prompt
            rules_text = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Create prompt for LLM
            prompt = f"""You are a regulatory compliance officer checking a loan application against USDA rules.

Loan Type: {loan_type}

Applicant Data:
- CIBIL Score: {data.get('cibil_score', 'Not provided')}
- Annual Income: ₹{data.get('annual_income', data.get('income_annum', 'Not provided'))}
- Loan Amount: ₹{data.get('loan_amount', 'Not provided')}
- Existing Debt: ₹{data.get('existing_debt', 'Not provided')}
- Age: {data.get('age', 'Not provided')}
- Employment Type: {data.get('employment_type', 'Not provided')}
- Employment Years: {data.get('employment_years', 'Not provided')}

Relevant Regulatory Rules:
{rules_text}

Task: Identify any CRITICAL or HIGH severity violations. For each violation, provide:
1. Rule violated (exact rule number if available)
2. Reason for violation (be specific)
3. Severity (CRITICAL or HIGH only)

Return as JSON array: [{{"rule": "...", "reason": "...", "severity": "CRITICAL|HIGH"}}]
If no CRITICAL or HIGH violations, return empty array: []

IMPORTANT: Only flag actual violations. If data is "Not provided", do not flag as violation unless the rule explicitly requires it.
"""
            
            response = await self.llm.ainvoke(prompt)
            response_content = response.content
            
            violations_data = parse_json_response(response_content, default=[])
            if isinstance(violations_data, list):
                return violations_data
            logging.warning(f"Could not parse LLM response: {response_content[:100]}")
            return []
        
        except Exception as e:
            logging.error(f"Async RAG compliance check failed: {e}")
            return []
    
    def _check_loan_compliance_rules(self, data: Dict[str, Any], loan_type: str) -> List[Dict[str, str]]:
        """
        Check loan compliance using rule-based approach (fallback).
        
        Args:
            data: Applicant data
            loan_type: Type of loan
            
        Returns:
            List of violations
        """
        violations = []
        
        # Rule 1.1: Minimum Credit Score (CRITICAL)
        cibil_score = data.get('cibil_score')
        if cibil_score and cibil_score < 640:
            violations.append({
                "rule": "USDA Rule 1.1: Minimum Credit Score",
                "reason": f"CIBIL score {cibil_score} is below minimum requirement of 640",
                "severity": "CRITICAL"
            })
        
        # Rule 2.1: Debt-to-Income Ratio (CRITICAL)
        annual_income = data.get('annual_income') or data.get('income_annum')
        loan_amount = data.get('loan_amount')
        existing_debt = data.get('existing_debt', 0)
        
        if annual_income and loan_amount:
            monthly_income = annual_income / 12
            # Estimate monthly payment (simplified: 1% of loan amount)
            estimated_payment = loan_amount * 0.01
            monthly_debt = existing_debt / 12 if existing_debt else 0
            total_monthly_debt = estimated_payment + monthly_debt
            dti_ratio = (total_monthly_debt / monthly_income) * 100
            
            if dti_ratio > 41:
                violations.append({
                    "rule": "USDA Rule 2.1: Debt-to-Income Ratio",
                    "reason": f"DTI ratio {dti_ratio:.1f}% exceeds maximum of 41%",
                    "severity": "CRITICAL"
                })
        
        # Rule 8.1: Minimum Age (CRITICAL)
        age = data.get('age')
        if age and age < 18:
            violations.append({
                "rule": "USDA Rule 8.1: Minimum Age",
                "reason": f"Applicant age {age} is below minimum of 18 years",
                "severity": "CRITICAL"
            })
        
        # Rule 3.1: Employment History (MEDIUM)
        employment_years = data.get('employment_years')
        if employment_years is not None and employment_years < 2:
            violations.append({
                "rule": "USDA Rule 3.1: Employment History",
                "reason": f"Employment history of {employment_years} years is below recommended 2 years",
                "severity": "MEDIUM"
            })
        
        return violations
    
    def _check_insurance_compliance(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Check insurance application against IRDAI rules.
        
        Args:
            data: Applicant data
            
        Returns:
            List of violations
        """
        violations = []

        # Always apply rule-based checks
        violations.extend(self._check_insurance_compliance_rules(data))

        # Add RAG violations if available
        if self.llm and self.rules_db:
            violations.extend(self._check_insurance_compliance_rag(data))

        return violations
    
    def _check_insurance_compliance_rag(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Check insurance compliance using RAG.
        
        Args:
            data: Applicant data
            
        Returns:
            List of violations
        """
        try:
            # Retrieve relevant rules
            query = "What are the eligibility requirements for health insurance? Include age, BMI, pre-existing conditions, smoking status."
            relevant_docs = self.rules_db.similarity_search(query, k=5)
            
            # Format rules for prompt
            rules_text = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Create prompt for LLM
            prompt = f"""You are an IRDAI compliance officer checking a health insurance application.

Applicant Data:
- Age: {data.get('age', 'Not provided')}
- BMI: {data.get('bmi', 'Not provided')}
- Smoker: {data.get('smoker', 'Not provided')}
- Pre-existing Conditions: {data.get('pre_existing_conditions', 'Not provided')}
- Blood Pressure: {'High' if data.get('bloodpressure') == 1 else 'Normal' if data.get('bloodpressure') == 0 else 'Not provided'}
- Diabetes: {'Yes' if data.get('diabetes') == 1 else 'No' if data.get('diabetes') == 0 else 'Not provided'}
- HbA1c: {data.get('hba1c', 'Not provided')}%
- Coverage Amount: ₹{data.get('coverage_amount', 'Not provided')}

Relevant IRDAI Rules:
{rules_text}

Task: Identify any CRITICAL or HIGH severity violations. For each violation, provide:
1. Rule violated (exact rule number if available)
2. Reason for violation (be specific)
3. Severity (CRITICAL or HIGH only)

Return as JSON array: [{{"rule": "...", "reason": "...", "severity": "CRITICAL|HIGH"}}]
If no CRITICAL or HIGH violations, return empty array: []

IMPORTANT: Only flag actual violations. If data is "Not provided", do not flag as violation unless the rule explicitly requires it.
"""
            
            response = self.llm.invoke(prompt).content
            
            violations_data = parse_json_response(response, default=[])
            if isinstance(violations_data, list):
                return violations_data
            logging.warning(f"Could not parse LLM response: {response[:100]}")
            return []
        
        except Exception as e:
            logging.error(f"RAG compliance check failed: {e}")
            return []
    
    async def _check_insurance_compliance_rag_async(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Check insurance compliance using RAG asynchronously.
        
        Args:
            data: Applicant data
            
        Returns:
            List of violations
        """
        try:
            # Retrieve relevant rules
            query = "What are the eligibility requirements for health insurance? Include age, BMI, pre-existing conditions, smoking status."
            relevant_docs = self.rules_db.similarity_search(query, k=5)
            
            # Format rules for prompt
            rules_text = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Create prompt for LLM
            prompt = f"""You are an IRDAI compliance officer checking a health insurance application.

Applicant Data:
- Age: {data.get('age', 'Not provided')}
- BMI: {data.get('bmi', 'Not provided')}
- Smoker: {data.get('smoker', 'Not provided')}
- Pre-existing Conditions: {data.get('pre_existing_conditions', 'Not provided')}
- Blood Pressure: {'High' if data.get('bloodpressure') == 1 else 'Normal' if data.get('bloodpressure') == 0 else 'Not provided'}
- Diabetes: {'Yes' if data.get('diabetes') == 1 else 'No' if data.get('diabetes') == 0 else 'Not provided'}
- HbA1c: {data.get('hba1c', 'Not provided')}%
- Coverage Amount: ₹{data.get('coverage_amount', 'Not provided')}

Relevant IRDAI Rules:
{rules_text}

Task: Identify any CRITICAL or HIGH severity violations. For each violation, provide:
1. Rule violated (exact rule number if available)
2. Reason for violation (be specific)
3. Severity (CRITICAL or HIGH only)

Return as JSON array: [{{"rule": "...", "reason": "...", "severity": "CRITICAL|HIGH"}}]
If no CRITICAL or HIGH violations, return empty array: []

IMPORTANT: Only flag actual violations. If data is "Not provided", do not flag as violation unless the rule explicitly requires it.
"""
            
            response = await self.llm.ainvoke(prompt)
            response_content = response.content
            
            violations_data = parse_json_response(response_content, default=[])
            if isinstance(violations_data, list):
                return violations_data
            logging.warning(f"Could not parse LLM response: {response_content[:100]}")
            return []
        
        except Exception as e:
            logging.error(f"Async RAG compliance check failed: {e}")
            return []
    
    def _check_insurance_compliance_rules(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Check insurance compliance using rule-based approach (fallback).
        
        Args:
            data: Applicant data
            
        Returns:
            List of violations
        """
        violations = []
        
        # Rule 1.1: Minimum Entry Age (CRITICAL)
        age = data.get('age')
        if age and age < 18:
            violations.append({
                "rule": "IRDAI Rule 1.1: Minimum Entry Age",
                "reason": f"Applicant age {age} is below minimum of 18 years",
                "severity": "CRITICAL"
            })
        
        # Rule 1.2: Maximum Entry Age (HIGH)
        if age and age > 65:
            violations.append({
                "rule": "IRDAI Rule 1.2: Maximum Entry Age",
                "reason": f"Applicant age {age} exceeds standard maximum of 65 years",
                "severity": "HIGH"
            })
        
        # Rule 3.1: BMI Limits (HIGH)
        bmi = data.get('bmi')
        if bmi:
            if bmi < 18:
                violations.append({
                    "rule": "IRDAI Rule 3.1: BMI Limits",
                    "reason": f"BMI {bmi:.1f} is below minimum of 18 (underweight)",
                    "severity": "HIGH"
                })
            elif bmi > 35:
                violations.append({
                    "rule": "IRDAI Rule 3.1: BMI Limits",
                    "reason": f"BMI {bmi:.1f} exceeds 35 (requires significant premium loading)",
                    "severity": "HIGH"
                })
        
        # Rule 5.1: Diabetes with High HbA1c (HIGH)
        hba1c = data.get('hba1c')
        if hba1c and hba1c > 9.0:
            violations.append({
                "rule": "IRDAI Rule 5.1: Diabetes Control",
                "reason": f"HbA1c {hba1c:.1f}% exceeds 9% (poorly controlled diabetes)",
                "severity": "HIGH"
            })
        
        # Rule 5.2: Severe Hypertension (HIGH)
        systolic_bp = data.get('systolic_bp')
        diastolic_bp = data.get('diastolic_bp')
        if systolic_bp and diastolic_bp:
            if systolic_bp > 160 or diastolic_bp > 100:
                violations.append({
                    "rule": "IRDAI Rule 5.2: Hypertension",
                    "reason": f"Blood pressure {systolic_bp}/{diastolic_bp} exceeds 160/100 (severe hypertension)",
                    "severity": "HIGH"
                })
        
        return violations
    
    def _format_rejection_reason(self, violations: List[Dict[str, str]]) -> str:
        """
        Format violations into user-friendly rejection message.
        
        Args:
            violations: List of violations
            
        Returns:
            Formatted rejection message
        """
        reasons = []
        for v in violations:
            reasons.append(f"- {v['rule']}: {v['reason']}")
        
        return "Application rejected due to regulatory violations:\n" + "\n".join(reasons)
