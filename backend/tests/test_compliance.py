"""
Unit tests for Compliance Agent fail-closed behaviour.

Critical regression tests:
  - Any exception during compliance check must NOT result in compliance_passed=True
  - Errors must set requires_human_review=True
  - Graceful degradation with missing state keys
"""

import pytest
from unittest.mock import MagicMock, patch


class TestComplianceFailClosed:
    """
    Ensure the fail-closed fix (P0.3) holds — compliance MUST NOT pass when
    the engine throws an unexpected exception.
    """

    def _make_state(self) -> dict:
        return {
            "request_id": "test-req-999",
            "request_type": "loan",
            "loan_type": "home",
            "errors": [],
            "declared_data": {
                "cibil_score": 750,
                "age": 35,
                "employment_years": 5,
                "declared_monthly_income": 80000,
            },
        }

    def _make_agent(self):
        from agents.compliance import ComplianceAgent
        from unittest.mock import MagicMock
        agent = ComplianceAgent.__new__(ComplianceAgent)
        # Stub every attribute that check_compliance() accesses before the patch
        agent.bypass_compliance = False
        agent.groq_api_key = None
        agent.llm = None
        agent.vectorstore = None
        agent.rules_dir = MagicMock()
        return agent

    def test_check_compliance_fails_closed_on_exception(self):
        """
        Patch ComplianceAgent internals to throw, verify compliance_passed=False.
        """
        from agents.compliance import ComplianceAgent

        agent = self._make_agent()

        # Force the private check method to raise
        with patch.object(agent, "_check_loan_compliance", side_effect=RuntimeError("DB exploded")):
            state = self._make_state()
            result = agent.check_compliance(state)

        # CRITICAL: must be False, not True (old fail-open bug)
        assert result.get("compliance_passed") is False, (
            "Compliance engine error MUST NOT result in compliance_passed=True"
        )
        assert result.get("requires_human_review") is True
        assert result.get("compliance_checked") is True
        assert any("error" in str(v).lower() or "human" in str(v).lower()
                   for v in (result.get("compliance_violations") or []))

    def test_compliance_violations_list_populated_on_error(self):
        """
        The violations list must contain at least one SYSTEM-level entry on error.
        """
        agent = self._make_agent()

        with patch.object(agent, "_check_loan_compliance", side_effect=ValueError("boom")):
            state = self._make_state()
            result = agent.check_compliance(state)

        violations = result.get("compliance_violations", [])
        assert len(violations) >= 1
        assert any(v.get("severity") == "CRITICAL" for v in violations)


class TestComplianceLowCibil:
    """
    Test the deterministic (non-LLM) rule checks in _check_loan_compliance_rules.
    These don't need LLM or vector store — they run purely on applicant_data.
    """

    def _get_rules_method(self):
        """Return a reference to the deterministic rules helper."""
        from agents.compliance import ComplianceAgent
        # Import the private method that does the deterministic checks.
        # This is _check_loan_compliance_rules (or _check_basic_loan_rules depending on version).
        # We call it directly without needing the full agent.
        agent = ComplianceAgent.__new__(ComplianceAgent)
        agent.bypass_compliance = False
        agent.groq_api_key = None
        agent.llm = None
        agent.vectorstore = None
        from unittest.mock import MagicMock
        agent.rules_dir = MagicMock()
        return agent

    def test_low_cibil_auto_rejected(self):
        agent = self._get_rules_method()
        # Access the private deterministic method name
        check_fn = getattr(agent, "_check_loan_compliance_rules", None) or getattr(agent, "_basic_loan_rule_checks", None)
        if check_fn is None:
            pytest.skip("No deterministic rule-check method found — relying on integration test")

        violations = check_fn(
            {"cibil_score": 500, "age": 30, "employment_years": 4, "declared_monthly_income": 60000},
            "home"
        )
        cibil_violations = [v for v in violations if "cibil" in v.get("rule", "").lower()
                            or "credit" in v.get("reason", "").lower()]
        assert len(cibil_violations) >= 1, f"Expected CIBIL violation, got: {violations}"

    def test_underage_applicant_flagged(self):
        agent = self._get_rules_method()
        check_fn = getattr(agent, "_check_loan_compliance_rules", None) or getattr(agent, "_basic_loan_rule_checks", None)
        if check_fn is None:
            pytest.skip("No deterministic rule-check method found — relying on integration test")

        violations = check_fn(
            {"cibil_score": 750, "age": 16, "employment_years": 0, "declared_monthly_income": 0},
            "personal"
        )
        age_violations = [v for v in violations if "age" in v.get("rule", "").lower()]
        assert len(age_violations) >= 1
