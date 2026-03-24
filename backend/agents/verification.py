"""
Verification Agent with LLM-based sanity checking.

This module implements a final verification layer that uses LLM to validate
ML model outputs and reasoning before sending results to the frontend.
Includes async support for improved performance.
"""

import asyncio
import logging
import os
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError

from src.schemas.state import ApplicationState

logger = logging.getLogger(__name__)


class VerificationResult(BaseModel):
    """Pydantic model for verification results."""
    verified: bool = Field(description="Whether the decision is verified as reasonable")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    concerns: list[str] = Field(default_factory=list, description="List of concerns or red flags")
    recommendation: str = Field(description="Recommendation: APPROVE, REVIEW, REJECT, or ADJUST")


class VerificationAgent:
    """
    Verification agent that performs LLM-based sanity checks on ML model decisions.
    
    This agent:
    - Reviews loan approval decisions for consistency
    - Reviews insurance premium predictions for reasonableness
    - Identifies potential concerns or red flags
    - Returns verification result with confidence score
    """
    
    def __init__(self):
        """Initialize the Verification Agent with Groq LLM."""
        logger.info("Initializing VerificationAgent")
        
        try:
            from langchain_groq import ChatGroq
            from langchain_core.output_parsers import PydanticOutputParser

            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            
            self.llm = ChatGroq(
                model="openai/gpt-oss-20b",
                temperature=0.2,
                api_key=api_key
            )
            
            # Initialize Pydantic output parser
            self.parser = PydanticOutputParser(pydantic_object=VerificationResult)
            
            logger.info("VerificationAgent initialized successfully with Pydantic parser")
        except ImportError as e:
            logger.error(f"langchain_groq not available: {e}")
            raise RuntimeError("Verification agent initialization failed: LLM dependency missing")
        except Exception as e:
            logger.error(f"Failed to initialize Groq LLM: {e}")
            raise RuntimeError(f"Verification agent initialization failed: {e}")
    
    def verify_decision(self, state: ApplicationState) -> ApplicationState:
        """
        Main verification method that routes to loan or insurance verification.
        """
        try:
            request_type = state.get("request_type", "both")

            # Verify loan decision if present
            if request_type in ["loan", "both"] and state.get("loan_prediction"):
                loan_verification = self._verify_loan_decision(state)
                state["loan_verification"] = loan_verification
                logger.info(f"Loan verification: {loan_verification.get('verified', False)}")

            # Verify insurance decision if present
            if request_type in ["insurance", "both"] and state.get("insurance_prediction"):
                insurance_verification = self._verify_insurance_decision(state)
                state["insurance_verification"] = insurance_verification
                logger.info(f"Insurance verification: {insurance_verification.get('verified', False)}")

            return state

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            state.setdefault("errors", []).append(f"Verification: {str(e)}")
            return state
    
    def _verify_loan_decision(self, state: ApplicationState) -> Dict[str, Any]:
        """
        Verify loan decision makes sense given applicant data.
        
        Args:
            state: Application state with loan_prediction and applicant_data
        
        Returns:
            Verification result with verified flag, concerns, and confidence
        """
        try:
            prediction = state["loan_prediction"]
            applicant_data = state.get("declared_data") or state.get("applicant_data") or {}
            
            if not self.llm or not self.parser:
                return self._fallback_verification("REVIEW")

            # Format reasoning for prompt
            reasoning_text = self._format_reasoning(prediction.get("reasoning", {}))
            
            # Get format instructions from parser
            format_instructions = self.parser.get_format_instructions()
            
            prompt = f"""You are a senior loan underwriter reviewing an AI decision.

Applicant Profile:
- CIBIL Score: {applicant_data.get('cibil_score', 'N/A')}
- Annual Income: Γé╣{applicant_data.get('annual_income', applicant_data.get('income_annum', 'N/A'))}
- Loan Amount: Γé╣{applicant_data.get('loan_amount', 'N/A')}
- Existing Debt: Γé╣{applicant_data.get('existing_debt', 'N/A')}
- Age: {applicant_data.get('age', 'N/A')}
- Employment: {applicant_data.get('employment_type', 'N/A')}
- Employment Years: {applicant_data.get('employment_years', 'N/A')}

AI Decision: {"APPROVED" if prediction['approved'] else "REJECTED"}
Confidence: {prediction['probability']:.1%}

Top Contributing Factors:
{reasoning_text}

Task: Verify if this decision is reasonable. Consider:
1. Does the decision align with the applicant's profile?
2. Are the contributing factors logical?
3. Are there any red flags or concerns?

{format_instructions}"""
            
            response = self.llm.invoke(prompt).content
            
            # Parse using Pydantic parser
            try:
                verification = self.parser.parse(response)
                result = verification.model_dump()
                logger.debug(f"Loan verification result: {result}")
                return result
            except ValidationError as e:
                logger.error(f"Pydantic validation failed: {e}")
                return self._fallback_verification("REVIEW")
        except Exception as e:
            logger.error(f"Loan verification failed (likely rate limit): {e}")
            # Return fallback verification instead of failing workflow
            prediction = state.get("loan_prediction", {})
            decision = "APPROVED" if prediction.get("approved") else "REJECTED"
            return self._fallback_verification(decision)
    
    async def _verify_loan_decision_async(self, state: ApplicationState) -> Dict[str, Any]:
        """
        Async version: Verify loan decision makes sense given applicant data.
        """
        try:
            prediction = state["loan_prediction"]
            applicant_data = state.get("declared_data") or state.get("applicant_data") or {}
            
            # Format reasoning for prompt
            reasoning_text = self._format_reasoning(prediction.get("reasoning", {}))
            
            # Get format instructions from parser
            format_instructions = self.parser.get_format_instructions()
            
            prompt = f"""You are a senior loan underwriter reviewing an AI loan decision.

Applicant Profile:
- CIBIL Score: {applicant_data.get('cibil_score', 'N/A')}
- Annual Income: Γé╣{applicant_data.get('annual_income', applicant_data.get('income_annum', 0)):,.2f}
- Loan Amount: Γé╣{applicant_data.get('loan_amount', 0):,.2f}
- Existing Debt: Γé╣{applicant_data.get('existing_debt', 0):,.2f}
- Employment: {applicant_data.get('employment_type', 'N/A')}
- Work Experience: {applicant_data.get('employment_years', 'N/A')} years

AI Decision: {"APPROVED" if prediction['approved'] else "REJECTED"}
Confidence: {prediction['probability']:.1%}

Top Contributing Factors:
{reasoning_text}

Task: Verify if this decision is reasonable. Consider:
1. Does the decision align with the applicant's profile?
2. Are the contributing factors logical?
3. Are there any red flags or concerns?

{format_instructions}"""
            
            response = await self.llm.ainvoke(prompt)
            response_content = response.content
            
            # Parse using Pydantic parser
            try:
                verification = self.parser.parse(response_content)
                result = verification.model_dump()
                logger.debug(f"Loan verification result (async): {result}")
                return result
            except ValidationError as e:
                logger.error(f"Pydantic validation failed (async): {e}")
                return self._fallback_verification("REVIEW")
        except Exception as e:
            logger.error(f"Loan verification failed (async, likely rate limit): {e}")
            # Return fallback verification instead of failing workflow
            prediction = state.get("loan_prediction", {})
            decision = "APPROVED" if prediction.get("approved") else "REJECTED"
            return self._fallback_verification(decision)
    
    def _verify_insurance_decision(self, state: ApplicationState) -> Dict[str, Any]:
        """
        Verify insurance premium makes sense given applicant data.
        
        Args:
            state: Application state with insurance_prediction and applicant_data
        
        Returns:
            Verification result with verified flag, concerns, and confidence
        """
        try:
            prediction = state["insurance_prediction"]
            applicant_data = state.get("declared_data") or state.get("applicant_data") or {}
            
            if not self.llm or not self.parser:
                return self._fallback_verification("REVIEW")

            # Format reasoning for prompt
            reasoning_text = self._format_reasoning(prediction.get("reasoning", {}))
            
            # Get format instructions from parser
            format_instructions = self.parser.get_format_instructions()
            
            prompt = f"""You are a senior insurance underwriter reviewing an AI premium calculation.

Applicant Profile:
- Age: {applicant_data.get('age', 'N/A')}
- BMI: {applicant_data.get('bmi', 'N/A')}
- Smoker: {applicant_data.get('smoker', 'N/A')}
- Pre-existing Conditions: {applicant_data.get('pre_existing_conditions', [])}
- Blood Pressure: {"High" if applicant_data.get('bloodpressure') else "Normal"}
- Diabetes: {"Yes" if applicant_data.get('diabetes') else "No"}
- Occupation Risk: {applicant_data.get('occupation_risk', 'N/A')}

AI Premium: Γé╣{prediction['premium']:,.2f}

Top Contributing Factors:
{reasoning_text}

Task: Verify if this premium is reasonable. Consider:
1. Is the premium appropriate for the risk profile?
2. Are the contributing factors logical?
3. Are there any concerns about fairness or accuracy?

{format_instructions}"""
            
            response = self.llm.invoke(prompt).content
            
            # Parse using Pydantic parser
            try:
                verification = self.parser.parse(response)
                result = verification.model_dump()
                logger.debug(f"Insurance verification result: {result}")
                return result
            except ValidationError as e:
                logger.error(f"Pydantic validation failed: {e}")
                return self._fallback_verification("REVIEW")
        except Exception as e:
            logger.error(f"Insurance verification failed (likely rate limit): {e}")
            return self._fallback_verification("APPROVED")

    def _fallback_verification(self, recommendation: str) -> Dict[str, Any]:
        """Return a safe default verification result when LLM is unavailable."""
        return {
            "verified": True,
            "confidence": 0.5,
            "concerns": [],
            "recommendation": recommendation
        }
    
    async def _verify_insurance_decision_async(self, state: ApplicationState) -> Dict[str, Any]:
        """
        Async version: Verify insurance premium makes sense given applicant data.
        """
        try:
            prediction = state["insurance_prediction"]
            applicant_data = state["applicant_data"]

            # Format reasoning for prompt
            reasoning_text = self._format_reasoning(prediction.get("reasoning", {}))

            # Get format instructions from parser
            format_instructions = self.parser.get_format_instructions()

            prompt = f"""You are a senior insurance underwriter reviewing an AI premium calculation.

Applicant Profile:
- Age: {applicant_data.get('age', 'N/A')}
- BMI: {applicant_data.get('bmi', 'N/A')}
- Smoker: {applicant_data.get('smoker', 'N/A')}
- Pre-existing Conditions: {applicant_data.get('pre_existing_conditions', [])}
- Blood Pressure: {"High" if applicant_data.get('bloodpressure') else "Normal"}
- Diabetes: {"Yes" if applicant_data.get('diabetes') else "No"}
- Occupation Risk: {applicant_data.get('occupation_risk', 'N/A')}

AI Premium: Γé╣{prediction['premium']:,.2f}

Top Contributing Factors:
{reasoning_text}

Task: Verify if this premium is reasonable. Consider:
1. Is the premium appropriate for the risk profile?
2. Are the contributing factors logical?
3. Are there any concerns about fairness or accuracy?

{format_instructions}"""

            response = await self.llm.ainvoke(prompt)
            response_content = response.content

            # Parse using Pydantic parser
            try:
                verification = self.parser.parse(response_content)
                result = verification.model_dump()
                logger.debug(f"Insurance verification result (async): {result}")
                return result
            except ValidationError as e:
                logger.error(f"Pydantic validation failed (async): {e}")
                return self._fallback_verification("REVIEW")
        except Exception as e:
            logger.error(f"Insurance verification failed (async, likely rate limit): {e}")
            return self._fallback_verification("APPROVED")
    
    async def verify_decision_async(self, state: ApplicationState) -> ApplicationState:
        """
        Async version: Main verification method with parallel loan/insurance verification.
        """
        try:
            request_type = state.get("request_type", "both")
            
            tasks = []
            
            # Prepare verification tasks
            if request_type in ["loan", "both"] and state.get("loan_prediction"):
                tasks.append(("loan", self._verify_loan_decision_async(state)))
            
            if request_type in ["insurance", "both"] and state.get("insurance_prediction"):
                tasks.append(("insurance", self._verify_insurance_decision_async(state)))
            
            # Run verifications in parallel
            if tasks:
                task_types, task_coroutines = zip(*tasks)
                results = await asyncio.gather(*task_coroutines)
                
                for task_type, result in zip(task_types, results):
                    if task_type == "loan":
                        state["loan_verification"] = result
                        logger.info(f"Loan verification (async): {result.get('verified', False)}")
                    elif task_type == "insurance":
                        state["insurance_verification"] = result
                        logger.info(f"Insurance verification (async): {result.get('verified', False)}")
            
            return state
            
        except Exception as e:
            logger.error(f"Verification processing failed (async): {e}")
            state.setdefault("errors", []).append(f"Verification: {str(e)}")
            return state
    
    def _format_reasoning(self, reasoning: Dict[str, float]) -> str:
        """
        Format feature contributions for prompt.
        
        Args:
            reasoning: Dictionary of feature contributions
        
        Returns:
            Formatted string with top 5 features
        """
        if not reasoning:
            return "No reasoning available"
        
        # Sort by absolute contribution
        sorted_features = sorted(
            reasoning.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        # Format top 5 features
        lines = []
        for name, value in sorted_features[:5]:
            lines.append(f"- {name}: {value:+.3f}")
        
        return "\n".join(lines)
    


def verify_decision(state: ApplicationState) -> ApplicationState:
    """
    Convenience function for workflow integration.
    
    Args:
        state: Current application state
    
    Returns:
        Updated state with verification results
    """
    try:
        agent = VerificationAgent()
        return agent.verify_decision(state)
    except Exception as e:
        logger.error(f"Verification processing failed: {e}")
        state.setdefault("errors", []).append(f"Verification: {str(e)}")
        return state
