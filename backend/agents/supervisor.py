"""
Supervisor Agent — final decisioning and routing logic.

Replaces the previous stub which:
  - Always used confidence=0.9 regardless of agent outputs
  - Ignored fraud risk score, compliance violations, and agent error counts
  - Never rejected on agent-level criteria

This version:
  - Computes a weighted confidence score from all agent outputs
  - Hard-rejects on compliance violations, high fraud risk, or KYC failure
  - Routes to human review when verification raised concerns or errors occurred
  - Logs a structured audit trail for every decision
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ─── Decision thresholds ──────────────────────────────────────────────────────
FRAUD_HARD_REJECT_THRESHOLD = 75.0   # fraud_risk_score ≥ this → auto-reject
FRAUD_REVIEW_THRESHOLD = 40.0        # fraud_risk_score ≥ this → human review
MAX_AGENT_ERRORS_BEFORE_REVIEW = 2   # ≥ N errors from any agent → human review


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _compute_confidence(state: dict[str, Any]) -> float:
    """
    Derive a 0-1 confidence score from the combined agent outputs.

    Weights (sum to 1.0):
      KYC score          0.20
      Compliance pass    0.25
      Fraud (inverted)   0.15
      Loan probability   0.20
      Insurance prob     0.20
                              (scaled to available data)
    """
    factors: list[tuple[float, float]] = []  # (value, weight)

    # KYC
    kyc_score = _safe_float(state.get("kyc_score"), 1.0 if state.get("kyc_verified") else 0.0)
    factors.append((kyc_score, 0.20))

    # Compliance
    compliance_pass = 1.0 if state.get("compliance_passed") else 0.0
    factors.append((compliance_pass, 0.25))

    # Fraud (inverted — high fraud = low confidence)
    fraud_score = _safe_float(state.get("fraud_results", {}).get("fraud_risk_score", 0.0))
    factors.append((1.0 - min(fraud_score / 100.0, 1.0), 0.15))

    # Loan underwriting probability
    loan_prob = _safe_float(
        (state.get("loan_prediction") or {}).get("probability"),
        -1.0,  # sentinel for "not present"
    )
    if loan_prob >= 0:
        factors.append((loan_prob, 0.20))

    # Insurance normalised premium confidence (inverted standardised)
    ins_pred = state.get("insurance_prediction") or {}
    if ins_pred:
        ins_conf = _safe_float(ins_pred.get("confidence", ins_pred.get("confidence_score", -1.0)))
        if ins_conf >= 0:
            factors.append((ins_conf, 0.20))

    if not factors:
        return 0.5

    total_weight = sum(w for _, w in factors)
    weighted_sum = sum(v * w for v, w in factors)
    return round(weighted_sum / total_weight, 3)


# ─── Main supervisor class ────────────────────────────────────────────────────

class SupervisorAgent:
    """
    Supervisor that orchestrates workflow routing and makes the final
    approve / reject / escalate decision after all agents have run.
    """

    def make_decision(self, state: dict[str, Any]) -> dict[str, Any]:
        request_id = state.get("request_id", "unknown")
        errors: list[str] = state.get("errors", []) or []

        # ── 1. Hard-reject conditions ─────────────────────────────────────────

        # Explicit rejection already set by a prior agent
        if state.get("rejected"):
            reason = state.get("rejection_reason", "Rejected by upstream agent")
            return self._decide(state, "reject", reason, _compute_confidence(state), request_id)

        # KYC failed
        if not state.get("kyc_verified", True):
            reason = f"KYC failed: {state.get('rejection_reason', 'Identity verification failed')}"
            state["rejected"] = True
            state["rejection_reason"] = reason
            return self._decide(state, "reject", reason, 0.0, request_id)

        # Compliance failed
        if state.get("compliance_checked") and not state.get("compliance_passed", True):
            violations = state.get("compliance_violations", [])
            critical = [v for v in violations if v.get("severity") == "CRITICAL"]
            reason = (
                f"Compliance rejected: {critical[0]['reason']}" if critical
                else "Compliance check failed"
            )
            state["rejected"] = True
            state["rejection_reason"] = reason
            return self._decide(state, "reject", reason, 0.0, request_id)

        # Fraud hard-reject
        fraud_score = _safe_float(
            (state.get("fraud_results") or {}).get("fraud_risk_score", 0.0)
        )
        if fraud_score >= FRAUD_HARD_REJECT_THRESHOLD:
            reason = f"High fraud risk score ({fraud_score:.0f}/100) — auto-rejected"
            state["rejected"] = True
            state["rejection_reason"] = reason
            return self._decide(state, "reject", reason, 0.0, request_id)

        # ── 2. Human-review conditions ────────────────────────────────────────

        needs_review = state.get("requires_human_review", False)

        # Fraud review band
        if fraud_score >= FRAUD_REVIEW_THRESHOLD:
            needs_review = True
            state["human_review_reason"] = (
                state.get("human_review_reason", "")
                + f" Elevated fraud score ({fraud_score:.0f}/100)."
            )

        # Too many agent errors
        if len(errors) >= MAX_AGENT_ERRORS_BEFORE_REVIEW:
            needs_review = True
            state["human_review_reason"] = (
                state.get("human_review_reason", "")
                + f" {len(errors)} agent errors encountered."
            )

        # Verification concern
        loan_ver = state.get("loan_verification") or {}
        ins_ver = state.get("insurance_verification") or {}
        if loan_ver.get("requires_human_review") or ins_ver.get("requires_human_review"):
            needs_review = True
            state["human_review_reason"] = (
                state.get("human_review_reason", "")
                + " Verification agent flagged for human review."
            )

        # Compliance engine error (fail-closed path)
        if state.get("compliance_error"):
            needs_review = True
            state["human_review_reason"] = (
                state.get("human_review_reason", "")
                + f" Compliance engine error: {state['compliance_error']}."
            )

        if needs_review:
            state["requires_human_review"] = True
            reason = (state.get("human_review_reason") or "Manual review required").strip()
            confidence = _compute_confidence(state)
            return self._decide(state, "escalate_to_human", reason, confidence, request_id)

        # ── 3. Loopback condition ─────────────────────────────────────────────
        if state.get("loopback_requested"):
            reason = state.get("loopback_reason", "Additional information needed")
            return self._decide(state, "request_more_info", reason, 0.7, request_id)

        # ── 4. Approve ────────────────────────────────────────────────────────
        confidence = _compute_confidence(state)
        return self._decide(state, "approve", "All checks passed", confidence, request_id)

    # ── Private ───────────────────────────────────────────────────────────────

    def _decide(
        self,
        state: dict[str, Any],
        action: str,
        reason: str,
        confidence: float,
        request_id: str,
    ) -> dict[str, Any]:
        state["supervisor_action"] = action
        state["supervisor_decision"] = {
            "action": action,
            "reason": reason,
            "confidence": confidence,
            "fraud_score": _safe_float(
                (state.get("fraud_results") or {}).get("fraud_risk_score", 0.0)
            ),
            "compliance_passed": state.get("compliance_passed"),
            "kyc_verified": state.get("kyc_verified"),
            "error_count": len(state.get("errors") or []),
        }
        logger.info(
            "request_id=%s supervisor_action=%s confidence=%.3f reason=%s",
            request_id,
            action,
            confidence,
            reason,
        )
        return state

    def check_loopback_needed(self, state: dict[str, Any]) -> bool:
        """Check if loopback to earlier agent is needed based on verification concerns."""
        loan_verification = state.get("loan_verification", {}) or {}
        insurance_verification = state.get("insurance_verification", {}) or {}

        all_concerns = (
            loan_verification.get("concerns", [])
            + insurance_verification.get("concerns", [])
        )
        if len(all_concerns) > 2:
            state["loopback_requested"] = True
            state["loopback_target"] = "onboarding"
            state["loopback_reason"] = f"Multiple concerns: {', '.join(str(c) for c in all_concerns)}"
            return True

        doc_verification = state.get("document_verification") or {}
        stale_docs = [
            doc_type
            for doc_type, status in doc_verification.items()
            if not (status or {}).get("is_fresh", True)
        ]
        if stale_docs:
            state["loopback_requested"] = True
            state["loopback_target"] = "onboarding"
            state["loopback_reason"] = f"Stale documents: {', '.join(stale_docs)}"
            return True

        return False


# ─── Convenience function ─────────────────────────────────────────────────────

def supervisor_decision(state: dict[str, Any]) -> dict[str, Any]:
    """Convenience entry point for LangGraph workflow integration."""
    try:
        return SupervisorAgent().make_decision(state)
    except Exception as exc:
        logger.error("Supervisor processing failed: %s", exc)
        state.setdefault("errors", []).append(f"Supervisor: {exc}")
        state["supervisor_action"] = "escalate_to_human"
        state["requires_human_review"] = True
        return state
