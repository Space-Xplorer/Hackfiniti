"""
Unit tests for the Supervisor Agent decisioning logic.

Tests the weighted confidence calculation and decision routing.
"""

import pytest
from agents.supervisor import SupervisorAgent, supervisor_decision, _compute_confidence


class TestComputeConfidence:
    def test_all_good_gives_high_confidence(self):
        state = {
            "kyc_verified": True,
            "kyc_score": 1.0,
            "compliance_passed": True,
            "fraud_results": {"fraud_risk_score": 0.0},
            "loan_prediction": {"probability": 0.9},
        }
        conf = _compute_confidence(state)
        assert conf >= 0.85

    def test_high_fraud_lowers_confidence(self):
        state = {
            "kyc_verified": True,
            "kyc_score": 1.0,
            "compliance_passed": True,
            "fraud_results": {"fraud_risk_score": 90.0},
            "loan_prediction": {"probability": 0.9},
        }
        conf = _compute_confidence(state)
        # All-good baseline with fraud=0 should be higher than fraud=90
        state_no_fraud = {**state, "fraud_results": {"fraud_risk_score": 0.0}}
        assert _compute_confidence(state_no_fraud) > conf, "High fraud must lower confidence"
        assert conf < 0.83  # fraud=90 should bring it well below the no-fraud score

    def test_empty_state_gives_low_confidence(self):
        # With no KYC, no compliance, and high notional fraud penalty, confidence is low
        conf = _compute_confidence({})
        assert conf < 0.5  # missing data is bad — no false comfort

    def test_compliance_failure_zeroes_compliance_weight(self):
        state_pass = {"compliance_passed": True}
        state_fail = {"compliance_passed": False}
        assert _compute_confidence(state_pass) > _compute_confidence(state_fail)


class TestSupervisorDecisions:
    def _agent(self):
        return SupervisorAgent()

    def test_hard_reject_on_kyc_failure(self):
        state = {
            "request_id": "test",
            "kyc_verified": False,
            "errors": [],
        }
        result = self._agent().make_decision(state)
        assert result["supervisor_action"] == "reject"
        assert result["rejected"] is True

    def test_hard_reject_on_compliance_failure(self):
        state = {
            "request_id": "test",
            "kyc_verified": True,
            "compliance_checked": True,
            "compliance_passed": False,
            "compliance_violations": [
                {"rule": "RBI Rule 1.3", "reason": "Low CIBIL", "severity": "CRITICAL"}
            ],
            "errors": [],
        }
        result = self._agent().make_decision(state)
        assert result["supervisor_action"] == "reject"

    def test_hard_reject_on_high_fraud(self):
        state = {
            "request_id": "test",
            "kyc_verified": True,
            "compliance_passed": True,
            "fraud_results": {"fraud_risk_score": 80.0},
            "errors": [],
        }
        result = self._agent().make_decision(state)
        assert result["supervisor_action"] == "reject"

    def test_escalate_on_medium_fraud(self):
        state = {
            "request_id": "test",
            "kyc_verified": True,
            "compliance_passed": True,
            "fraud_results": {"fraud_risk_score": 50.0},  # in review band
            "errors": [],
        }
        result = self._agent().make_decision(state)
        assert result["supervisor_action"] == "escalate_to_human"
        assert result["requires_human_review"] is True

    def test_escalate_on_too_many_errors(self):
        state = {
            "request_id": "test",
            "kyc_verified": True,
            "compliance_passed": True,
            "fraud_results": {"fraud_risk_score": 5.0},
            "errors": ["err1", "err2", "err3"],  # ≥ 2 triggers review
        }
        result = self._agent().make_decision(state)
        assert result["supervisor_action"] == "escalate_to_human"

    def test_approve_on_clean_state(self):
        state = {
            "request_id": "test",
            "kyc_verified": True,
            "compliance_passed": True,
            "compliance_checked": True,
            "fraud_results": {"fraud_risk_score": 5.0},
            "loan_prediction": {"probability": 0.85},
            "errors": [],
        }
        result = self._agent().make_decision(state)
        assert result["supervisor_action"] == "approve"
        assert result["supervisor_decision"]["confidence"] > 0.7

    def test_supervisor_decision_in_state(self):
        state = {"request_id": "test", "kyc_verified": True, "compliance_passed": True, "errors": []}
        result = self._agent().make_decision(state)
        decision = result.get("supervisor_decision", {})
        assert "action" in decision
        assert "confidence" in decision
        assert "fraud_score" in decision

    def test_convenience_function_wrapper(self):
        state = {"request_id": "test", "kyc_verified": False, "errors": []}
        result = supervisor_decision(state)
        assert result["supervisor_action"] == "reject"

    def test_prior_rejection_kept(self):
        """If a previous agent already set rejected=True, supervisor honours it."""
        state = {
            "request_id": "test",
            "rejected": True,
            "rejection_reason": "Fraud agent hard reject",
            "errors": [],
        }
        result = self._agent().make_decision(state)
        assert result["supervisor_action"] == "reject"
        assert result["rejection_reason"] == "Fraud agent hard reject"

    def test_verification_flag_triggers_review(self):
        state = {
            "request_id": "test",
            "kyc_verified": True,
            "compliance_passed": True,
            "fraud_results": {"fraud_risk_score": 5.0},
            "loan_verification": {"requires_human_review": True, "concerns": ["Income mismatch"]},
            "errors": [],
        }
        result = self._agent().make_decision(state)
        assert result["supervisor_action"] == "escalate_to_human"
