"""
Supervisor Agent for workflow orchestration and decision-making.

This module implements the supervisor that coordinates all other agents,
makes routing decisions, and handles loopback scenarios.
"""

import logging
from typing import Literal, Dict, Any

from src.schemas.state import ApplicationState

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor agent that orchestrates workflow and makes routing decisions.
    
    The supervisor can:
    - Decide which agent to invoke next
    - Request more information (loopback to earlier agents)
    - Escalate to human review
    - Make final approval/rejection decisions
    """
    
    def __init__(self):
        """Initialize the Supervisor Agent."""
        logger.info("Initializing SupervisorAgent")
        self.agents = {
            "kyc": "KYC Agent",
            "onboarding": "Onboarding Agent",
            "compliance": "Compliance Agent",
            "router": "Router Agent",
            "underwriting_loan": "Underwriting Loan Agent",
            "underwriting_insurance": "Underwriting Insurance Agent",
            "verification_loan": "Verification Loan Agent",
            "verification_insurance": "Verification Insurance Agent",
            "transparency_loan": "Transparency Loan Agent",
            "transparency_insurance": "Transparency Insurance Agent"
        }
        logger.info("SupervisorAgent initialized successfully")
    
    def make_decision(self, state: ApplicationState) -> ApplicationState:
        """
        Make supervisor decision based on current state.
        
        Args:
            state: Current application state
        
        Returns:
            Updated state with supervisor decision
        """
        try:
            # Check if loopback is requested
            if state.get("loopback_requested"):
                action = "request_more_info"
                reason = state.get("loopback_reason", "Additional information needed")
            
            # Check if escalation is needed
            elif state.get("escalate_to_human"):
                action = "finalize"
                reason = state.get("escalation_reason", "Manual review required")
            
            # Check if there are critical errors
            elif state.get("error_category") == "compliance":
                action = "reject"
                reason = "Compliance violations detected"
                state["rejected"] = True
            
            # Check if workflow is complete
            elif state.get("completed"):
                action = "finalize"
                reason = "All processing complete"
            
            # Otherwise, proceed
            else:
                action = "proceed"
                reason = "Continue workflow"
            
            # Update state with decision
            state["supervisor_action"] = action
            state["supervisor_decision"] = {
                "action": action,
                "reason": reason,
                "confidence": 0.9
            }
            
            logger.info(f"Supervisor decision: {action} - {reason}")
            return state
            
        except Exception as e:
            logger.error(f"Supervisor decision failed: {e}")
            state.setdefault("errors", []).append(f"Supervisor: {str(e)}")
            state["supervisor_action"] = "finalize"
            return state
    
    def check_loopback_needed(self, state: ApplicationState) -> bool:
        """
        Check if loopback to earlier agent is needed.
        
        Args:
            state: Current application state
        
        Returns:
            True if loopback is needed
        """
        # Check verification concerns
        loan_verification = state.get("loan_verification", {})
        insurance_verification = state.get("insurance_verification", {})
        
        loan_concerns = loan_verification.get("concerns", [])
        insurance_concerns = insurance_verification.get("concerns", [])
        
        # If there are multiple concerns, request more info
        if len(loan_concerns) + len(insurance_concerns) > 2:
            state["loopback_requested"] = True
            state["loopback_target"] = "onboarding"
            state["loopback_reason"] = f"Multiple concerns raised: {', '.join(loan_concerns + insurance_concerns)}"
            return True
        
        # Check if data quality is low
        if state.get("document_verification"):
            stale_docs = [
                doc_type for doc_type, status in state["document_verification"].items()
                if not status.get("is_fresh", True)
            ]
            if len(stale_docs) > 0:
                state["loopback_requested"] = True
                state["loopback_target"] = "onboarding"
                state["loopback_reason"] = f"Stale documents detected: {', '.join(stale_docs)}"
                return True
        
        return False


def supervisor_decision(state: ApplicationState) -> ApplicationState:
    """
    Convenience function for workflow integration.
    
    Args:
        state: Current application state
    
    Returns:
        Updated state with supervisor decision
    """
    try:
        agent = SupervisorAgent()
        return agent.make_decision(state)
    except Exception as e:
        logger.error(f"Supervisor processing failed: {e}")
        state.setdefault("errors", []).append(f"Supervisor: {str(e)}")
        state["supervisor_action"] = "finalize"
        return state
