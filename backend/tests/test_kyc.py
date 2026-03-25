"""
Unit tests for the KYC agent — Verhoeff checksum, PAN validation, scoring.

These are pure unit tests (no server required) covering the core validation
logic added during the P0 security fix.
"""

import pytest


# Import the module under test
from agents.kyc import _verhoeff_validate, _validate_pan, _name_similarity, run


# ─── Verhoeff checksum ────────────────────────────────────────────────────────

class TestVerhoeff:
    # UIDAI example: valid Aadhaar numbers have checksum digit such that
    # _verhoeff_validate returns True.
    # We test with a known-bad number and known structural checks.

    def test_all_zeros_length_12_invalid(self):
        """000000000000 fails Verhoeff."""
        assert _verhoeff_validate("000000000000") is False

    def test_sequential_fails(self):
        assert _verhoeff_validate("123456789012") is False

    def test_non_digit_not_tested(self):
        """The function expects digit strings; letters would raise ValueError."""
        with pytest.raises((ValueError, IndexError)):
            _verhoeff_validate("ABCDEF123456")

    def test_11_digit_string_gives_wrong_result(self):
        # Only 12-digit strings are valid Aadhaar
        # A correct implementation should still not crash on different lengths
        result = _verhoeff_validate("12345678901")  # 11 digits
        assert isinstance(result, bool)


# ─── PAN validation ───────────────────────────────────────────────────────────

class TestPanValidation:
    def test_valid_pan_format(self):
        assert _validate_pan("ABCDE1234F") is True

    def test_lowercase_accepted(self):
        assert _validate_pan("abcde1234f") is True  # normalised to upper internally

    def test_pan_too_short_fails(self):
        assert _validate_pan("ABCD1234F") is False

    def test_pan_too_long_fails(self):
        assert _validate_pan("ABCDE12345F") is False

    def test_pan_wrong_pattern_fails(self):
        assert _validate_pan("1BCDE1234F") is False  # first char must be letter

    def test_pan_all_letters_fails(self):
        assert _validate_pan("ABCDEFGHIJ") is False

    def test_pan_with_spaces_surrounding_accepted(self):
        assert _validate_pan("  ABCDE1234F  ") is True


# ─── Name similarity ─────────────────────────────────────────────────────────

class TestNameSimilarity:
    def test_identical_names(self):
        assert _name_similarity("Priya Sharma", "Priya Sharma") == 1.0

    def test_case_insensitive(self):
        assert _name_similarity("Priya Sharma", "priya sharma") > 0.99

    def test_similar_names_above_threshold(self):
        score = _name_similarity("Rajesh Kumar", "Rajesh Kumar Singh")
        assert score > 0.7

    def test_completely_different_below_threshold(self):
        score = _name_similarity("Priya Sharma", "John Doe")
        assert score < 0.5

    def test_empty_strings(self):
        score = _name_similarity("", "")
        assert score == 1.0  # identical empty strings


# ─── KYC run() entry point ────────────────────────────────────────────────────

class TestKYCRun:
    def _base_state(self, aadhaar: str = "499118665246", name: str = "Priya Sharma", pan: str = "ABCDE1234F") -> dict:
        """Build a minimal state dict for KYC run."""
        return {
            "request_id": "test-req-001",
            "submitted_aadhaar": aadhaar,
            "submitted_name": name,
            "declared_data": {
                "pan": pan,
                "name": name,
                "aadhaar": aadhaar,
            },
        }

    def test_invalid_aadhaar_format_rejected(self):
        state = self._base_state(aadhaar="not-a-number")
        result = run(state)
        assert result["kyc_verified"] is False
        assert result.get("rejected") is True

    def test_short_aadhaar_rejected(self):
        state = self._base_state(aadhaar="12345")
        result = run(state)
        assert result["kyc_verified"] is False

    def test_invalid_pan_lowers_score(self):
        state = self._base_state(pan="INVALID-PAN")
        result = run(state)
        # KYC might still pass if Aadhaar checksum is fine, but score should be < 1.0
        assert result.get("kyc_score", 1.0) < 1.0

    def test_missing_name_lowers_score(self):
        state = self._base_state(name="")
        result = run(state)
        assert result.get("kyc_score", 1.0) < 1.0

    def test_kyc_data_populated(self):
        state = self._base_state()
        result = run(state)
        data = result.get("kyc_data", {})
        assert data.get("aadhaar_number") is not None
        assert data.get("name") is not None

    def test_no_crash_on_empty_state(self):
        result = run({})
        assert "kyc_verified" in result
        assert result["kyc_verified"] is False
