"""
LangGraph workflow definition.

This module defines the main LangGraph workflow for the Daksha system.
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from src.schemas.state import ApplicationState
from src.services.kyc import KYCAgent
from src.agents.onboarding import OnboardingAgent
from src.agents.rules import RulesAgent
from src.agents.fraud import FraudAgent
from src.agents.feature_engineering import FeatureEngineeringAgent
from src.agents.compliance import ComplianceAgent
from src.agents.underwriting import UnderwritingAgent
from src.agents.verification import VerificationAgent
from src.agents.transparency import TransparencyAgent
from src.services.router import RouterAgent
from src.agents.supervisor import SupervisorAgent
from src.utils.error_handling import safe_agent_wrapper
from src.utils.logging import log_request, log_agent_execution


# Initialize agents
kyc_agent = KYCAgent()
onboarding_agent = OnboardingAgent()
rules_agent = RulesAgent()
fraud_agent = FraudAgent()
feature_engineering_agent = FeatureEngineeringAgent()
compliance_agent = ComplianceAgent()
underwriting_agent = UnderwritingAgent()
verification_agent = VerificationAgent()
transparency_agent = TransparencyAgent()
router_agent = RouterAgent()
supervisor_agent = SupervisorAgent()


# Wrap agents with error handling
@safe_agent_wrapper
def kyc_node(state: ApplicationState) -> ApplicationState:
    """KYC verification node."""
    return kyc_agent.verify_identity(state)


@safe_agent_wrapper
def onboarding_node(state: ApplicationState) -> ApplicationState:
    """Onboarding and document processing node."""
    return onboarding_agent.process_documents(state)


@safe_agent_wrapper
def rules_node(state: ApplicationState) -> ApplicationState:
    """Rules validation node."""
    return rules_agent.check_rules(state)


@safe_agent_wrapper
def fraud_node(state: ApplicationState) -> ApplicationState:
    """OCR fraud detection node."""
    return fraud_agent.check_fraud(state)

@safe_agent_wrapper
def feature_engineering_node(state: ApplicationState) -> ApplicationState:
    """Derived feature engineering node."""
    return feature_engineering_agent.process(state)


@safe_agent_wrapper
def compliance_node(state: ApplicationState) -> ApplicationState:
    """Compliance checking node."""
    return compliance_agent.check_compliance(state)


@safe_agent_wrapper
def router_node(state: ApplicationState) -> ApplicationState:
    """Router node to determine next processing path."""
    return router_agent.route_request(state)


@safe_agent_wrapper
def underwriting_loan_node(state: ApplicationState) -> ApplicationState:
    """Loan underwriting node."""
    state = underwriting_agent.process_loan(state)
    state["current_agent"] = "underwriting_loan"
    return state


@safe_agent_wrapper
def underwriting_insurance_node(state: ApplicationState) -> ApplicationState:
    """Insurance underwriting node."""
    state = underwriting_agent.process_insurance(state)
    state["current_agent"] = "underwriting_insurance"
    return state


@safe_agent_wrapper
def verification_loan_node(state: ApplicationState) -> ApplicationState:
    """Loan verification node."""
    state = verification_agent.verify_decision(state)
    state["loan_verified"] = True
    return state


@safe_agent_wrapper
def verification_insurance_node(state: ApplicationState) -> ApplicationState:
    """Insurance verification node."""
    state = verification_agent.verify_decision(state)
    state["insurance_verified"] = True
    return state


@safe_agent_wrapper
def transparency_loan_node(state: ApplicationState) -> ApplicationState:
    """Loan explanation generation node."""
    state = transparency_agent.explain_loan_decision(state)
    return state


@safe_agent_wrapper
def transparency_insurance_node(state: ApplicationState) -> ApplicationState:
    """Insurance explanation generation node."""
    state = transparency_agent.explain_insurance_premium(state)
    return state


@safe_agent_wrapper
def hitl_checkpoint_node(state: ApplicationState) -> ApplicationState:
    """
    HITL (Human-in-the-Loop) checkpoint node.
    
    This node pauses the workflow for human review of extracted data.
    In a real implementation, this would wait for user input.
    For now, it just marks the checkpoint and continues.
    """
    state["hitl_checkpoint"] = True
    
    # Apply any corrections if provided
    if state.get("hitl_corrections"):
        state["applicant_data"].update(state["hitl_corrections"])
        state["hitl_data_corrected"] = True
    
    return state


@safe_agent_wrapper
def supervisor_node(state: ApplicationState) -> ApplicationState:
    """Supervisor decision node."""
    return supervisor_agent.make_decision(state)


def should_continue_after_kyc(state: ApplicationState) -> Literal["onboarding", "end"]:
    """
    Conditional edge after KYC: continue to onboarding or end if KYC failed.
    
    Args:
        state: Current application state
        
    Returns:
        Next node name or "end"
    """
    if state.get("kyc_verified", False):
        return "onboarding"
    else:
        return "end"


def should_continue_after_onboarding(state: ApplicationState) -> Literal["rules", "hitl_checkpoint"]:
    """
    Conditional edge after onboarding: go to HITL checkpoint or directly to compliance.
    
    Args:
        state: Current application state
        
    Returns:
        Next node name
    """
    # Go directly to rules validation after OCR processing
    return "rules"


def should_continue_after_rules(state: ApplicationState) -> Literal["fraud", "end"]:
    """
    Conditional edge after rules: continue to fraud checks or end if rejected.
    """
    if state.get("rejected") or not state.get("rules_passed", True):
        return "end"
    return "fraud"


def should_continue_after_fraud(state: ApplicationState) -> Literal["feature_engineering"]:
    """Continue to feature engineering after fraud checks."""
    return "feature_engineering"


def should_continue_after_feature_engineering(state: ApplicationState) -> Literal["compliance"]:
    """Continue to compliance after feature engineering."""
    return "compliance"


def should_continue_after_hitl(state: ApplicationState) -> Literal["compliance", "onboarding"]:
    """
    Conditional edge after HITL: continue to compliance or loop back to onboarding.
    
    Args:
        state: Current application state
        
    Returns:
        Next node name
    """
    # Check if loopback to onboarding is requested
    if state.get("loopback_requested") and state.get("loopback_target") == "onboarding":
        state["loopback_requested"] = False  # Reset flag
        return "onboarding"
    
    return "compliance"


def should_continue_after_compliance(state: ApplicationState) -> Literal["router", "supervisor", "end"]:
    """
    Conditional edge after compliance: continue to router, go to supervisor, or end if compliance failed.
    
    Args:
        state: Current application state
        
    Returns:
        Next node name or "end"
    """
    if state.get("compliance_passed", False):
        return "router"
    else:
        # Compliance failed, go to supervisor for final decision
        return "supervisor"


def route_after_router(state: ApplicationState) -> Literal["underwriting_loan", "underwriting_insurance", "end"]:
    """
    Conditional edge after router: determine which underwriting path to take.
    
    Args:
        state: Current application state
        
    Returns:
        Next node name
    """
    request_type = state.get("request_type")
    
    if request_type == "loan":
        return "underwriting_loan"
    elif request_type == "insurance":
        return "underwriting_insurance"
    elif request_type == "both":
        return "underwriting_loan"  # Process loan first
    else:
        return "end"


def route_after_loan_explanation(state: ApplicationState) -> Literal["underwriting_insurance", "supervisor", "end"]:
    """
    Conditional edge after loan explanation: process insurance if "both", go to supervisor, or end.
    
    Args:
        state: Current application state
        
    Returns:
        Next node name or "end"
    """
    request_type = state.get("request_type")
    
    if request_type == "both" and not state.get("insurance_prediction"):
        return "underwriting_insurance"
    else:
        # Go to supervisor for final decision
        return "supervisor"


def route_after_insurance_explanation(state: ApplicationState) -> Literal["supervisor"]:
    """
    Conditional edge after insurance explanation: always go to supervisor.
    
    Args:
        state: Current application state
        
    Returns:
        Next node name
    """
    return "supervisor"


def route_supervisor_decision(state: ApplicationState) -> Literal["onboarding", "finalize", "end"]:
    """
    Conditional edge after supervisor decision: handle loopback, finalize, or end.
    
    Args:
        state: Current application state
        
    Returns:
        Next node name
    """
    supervisor_action = state.get("supervisor_action", "finalize")
    
    if supervisor_action == "request_more_info":
        # Loopback to onboarding for more information
        loopback_target = state.get("loopback_target", "onboarding")
        return loopback_target
    elif supervisor_action == "reject":
        state["rejected"] = True
        state["completed"] = True
        return "finalize"
    elif supervisor_action == "finalize":
        state["completed"] = True
        return "finalize"
    else:
        # proceed - should not reach here in normal flow
        return "finalize"


def finalize_state(state: ApplicationState) -> ApplicationState:
    """
    Finalize state before ending workflow.
    
    Args:
        state: Current application state
        
    Returns:
        Finalized state
    """
    if state.get("rejected") or state.get("kyc_verified") is False:
        state.pop("loan_prediction", None)
        state.pop("insurance_prediction", None)
        state.pop("loan_explanation", None)
        state.pop("insurance_explanation", None)

    if state.get("compliance_checked") and state.get("compliance_passed") is False:
        state.pop("loan_prediction", None)
        state.pop("insurance_prediction", None)
        state.pop("loan_explanation", None)
        state.pop("insurance_explanation", None)

    if state.get("kyc_verified") is False:
        state["kyc_rejection_reason"] = (
            state.get("kyc_rejection_reason")
            or state.get("rejection_reason")
            or "KYC Failed"
        )

    if state.get("loan_prediction") is None:
        state.pop("loan_prediction", None)
    if state.get("insurance_prediction") is None:
        state.pop("insurance_prediction", None)

    state["completed"] = True
    return state


def create_daksha_workflow() -> StateGraph:
    """
    Create the main LangGraph workflow for the Daksha system.
    
    The workflow follows this path:
    1. KYC verification (can reject)
    2. Onboarding (document OCR)
    3. Rules validation (can reject)
    4. Fraud checks (non-blocking)
    5. Compliance checking (can reject)
    6. Router (determines loan/insurance/both)
    7. Underwriting (loan and/or insurance)
    8. Verification (LLM sanity check)
    9. Transparency (explanation generation)
    10. Supervisor (final decision, can loop back)
    
    Returns:
        Compiled StateGraph workflow
    """
    # Create workflow
    workflow = StateGraph(ApplicationState)
    
    # Add nodes
    workflow.add_node("kyc", kyc_node)
    workflow.add_node("onboarding", onboarding_node)
    workflow.add_node("rules", rules_node)
    workflow.add_node("fraud", fraud_node)
    workflow.add_node("feature_engineering", feature_engineering_node)
    workflow.add_node("hitl_checkpoint", hitl_checkpoint_node)
    workflow.add_node("compliance", compliance_node)
    workflow.add_node("router", router_node)
    workflow.add_node("underwriting_loan", underwriting_loan_node)
    workflow.add_node("underwriting_insurance", underwriting_insurance_node)
    workflow.add_node("verification_loan", verification_loan_node)
    workflow.add_node("verification_insurance", verification_insurance_node)
    workflow.add_node("transparency_loan", transparency_loan_node)
    workflow.add_node("transparency_insurance", transparency_insurance_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("finalize", finalize_state)
    
    # Set entry point
    workflow.set_entry_point("kyc")
    
    # Define edges
    # KYC → Onboarding (or END if KYC fails)
    workflow.add_conditional_edges(
        "kyc",
        should_continue_after_kyc,
        {
            "onboarding": "onboarding",
            "end": "finalize"
        }
    )
    
    # Onboarding → Rules
    workflow.add_conditional_edges(
        "onboarding",
        should_continue_after_onboarding,
        {
            "rules": "rules",
            "hitl_checkpoint": "hitl_checkpoint"
        }
    )

    # Rules → Fraud (or end if rejected)
    workflow.add_conditional_edges(
        "rules",
        should_continue_after_rules,
        {
            "fraud": "fraud",
            "end": "finalize"
        }
    )

    # Fraud → Feature Engineering
    workflow.add_conditional_edges(
        "fraud",
        should_continue_after_fraud,
        {
            "feature_engineering": "feature_engineering"
        }
    )

    # Feature Engineering → Compliance
    workflow.add_conditional_edges(
        "feature_engineering",
        should_continue_after_feature_engineering,
        {
            "compliance": "compliance"
        }
    )
    
    # HITL Checkpoint → Compliance (or loop back to Onboarding)
    workflow.add_conditional_edges(
        "hitl_checkpoint",
        should_continue_after_hitl,
        {
            "compliance": "compliance",
            "onboarding": "onboarding"
        }
    )
    
    # Compliance → Router or Supervisor (or END if compliance fails)
    workflow.add_conditional_edges(
        "compliance",
        should_continue_after_compliance,
        {
            "router": "router",
            "supervisor": "supervisor",
            "end": "finalize"
        }
    )
    
    # Router → Underwriting (loan or insurance)
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "underwriting_loan": "underwriting_loan",
            "underwriting_insurance": "underwriting_insurance",
            "end": "finalize"
        }
    )
    
    # Loan flow: Underwriting → Verification → Explanation
    workflow.add_edge("underwriting_loan", "verification_loan")
    workflow.add_edge("verification_loan", "transparency_loan")
    
    # After loan explanation: continue to insurance if "both", or go to supervisor
    workflow.add_conditional_edges(
        "transparency_loan",
        route_after_loan_explanation,
        {
            "underwriting_insurance": "underwriting_insurance",
            "supervisor": "supervisor",
            "end": "finalize"
        }
    )
    
    # Insurance flow: Underwriting → Verification → Explanation → Supervisor
    workflow.add_edge("underwriting_insurance", "verification_insurance")
    workflow.add_edge("verification_insurance", "transparency_insurance")
    workflow.add_conditional_edges(
        "transparency_insurance",
        route_after_insurance_explanation,
        {
            "supervisor": "supervisor"
        }
    )
    
    # Supervisor → Finalize or Loopback
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor_decision,
        {
            "onboarding": "onboarding",
            "finalize": "finalize",
            "end": "finalize"
        }
    )
    
    # Finalize → END
    workflow.add_edge("finalize", END)
    
    # Compile and return
    return workflow.compile()


def run_workflow(state: ApplicationState) -> ApplicationState:
    """
    Run the Daksha workflow with logging.
    
    Args:
        state: Initial application state
        
    Returns:
        Final application state after workflow execution
    """
    request_id = state.get("request_id", "unknown")
    request_type = state.get("request_type", "unknown")
    
    # Log request
    log_request(request_id, request_type)
    
    # Create and run workflow
    workflow = create_daksha_workflow()
    
    try:
        final_state = workflow.invoke(state)
        return final_state
    except Exception as e:
        # Handle workflow-level errors
        from src.utils.logging import log_error
        log_error("workflow", f"Workflow execution failed: {str(e)}", request_id)
        
        state["errors"].append(f"Workflow execution failed: {str(e)}")
        state["completed"] = False
        return state

