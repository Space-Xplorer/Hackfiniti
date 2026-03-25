"""
KYC Agent — identity document validation.

Implements:
  1. Aadhaar checksum via Verhoeff algorithm (12-digit, luhn-equivalent for Aadhaar)
  2. PAN format validation via regex
  3. Basic name consistency check between submitted data and declared data
  4. Structured KYCResult with verified flag, score, and mismatch list

In production, wire _digilocker_verify() to the UIDAI / DigiLocker API.
"""

import re
import logging
from difflib import SequenceMatcher
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Verhoeff tables for Aadhaar checksum
# ─────────────────────────────────────────────────────────────────────────────

_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def _verhoeff_validate(number: str) -> bool:
    """Return True if *number* passes the Verhoeff checksum (used by UIDAI for Aadhaar)."""
    c = 0
    for i, digit in enumerate(reversed(number)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][int(digit)]]
    return c == 0


# ─────────────────────────────────────────────────────────────────────────────
# PAN format
# ─────────────────────────────────────────────────────────────────────────────

_PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def _validate_pan(pan: str) -> bool:
    """Return True if *pan* matches the standard PAN format: ABCDE1234F."""
    return bool(_PAN_PATTERN.match(pan.strip().upper()))


# ─────────────────────────────────────────────────────────────────────────────
# Name similarity
# ─────────────────────────────────────────────────────────────────────────────

def _name_similarity(a: str, b: str) -> float:
    """Return 0-1 similarity between two name strings (case-insensitive)."""
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()


# ─────────────────────────────────────────────────────────────────────────────
# KYC Agent entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(state: dict[str, Any]) -> dict[str, Any]:
    """
    KYC validation entry point for LangGraph / workflow.

    Reads from state:
      - submitted_aadhaar: 12-digit Aadhaar number
      - submitted_name: Applicant's declared name
      - submitted_dob: Date of birth (optional)
      - declared_data.pan: PAN (optional, validated if present)

    Writes to state:
      - kyc_verified: bool
      - kyc_score: float 0-1
      - kyc_data: dict with verification details
      - kyc_mismatches: list of mismatch descriptions
      - rejected + rejection_reason if KYC fails hard
    """
    declared = state.get("declared_data", {}) or {}
    aadhaar = str(
        state.get("submitted_aadhaar")
        or declared.get("aadhaar")
        or declared.get("aadhaar_number")
        or ""
    ).strip().replace(" ", "")
    name = str(state.get("submitted_name") or declared.get("name") or "").strip()
    pan = str(declared.get("pan") or declared.get("pan_number") or "").strip().upper()

    mismatches: list[str] = []
    score = 1.0

    # ── 1. Aadhaar format check ───────────────────────────────────────────────
    if not aadhaar or not aadhaar.isdigit() or len(aadhaar) != 12:
        state["kyc_verified"] = False
        state["kyc_score"] = 0.0
        state["kyc_mismatches"] = ["Aadhaar must be exactly 12 digits"]
        state["rejected"] = True
        state["rejection_reason"] = "KYC failed: invalid Aadhaar format"
        state.setdefault("errors", []).append("KYC: invalid Aadhaar format")
        logger.warning("request_id=%s agent=kyc status=failed reason=invalid_aadhaar_format",
                       state.get("request_id", "unknown"))
        return state

    # ── 2. Aadhaar Verhoeff checksum ─────────────────────────────────────────
    if not _verhoeff_validate(aadhaar):
        mismatches.append(f"Aadhaar checksum failed — number {aadhaar} is likely invalid")
        score -= 0.5
        logger.warning("request_id=%s agent=kyc aadhaar_checksum=failed",
                       state.get("request_id", "unknown"))

    # ── 3. Name presence check ───────────────────────────────────────────────
    if not name:
        mismatches.append("Applicant name is missing")
        score -= 0.2

    # ── 4. PAN validation (if provided) ──────────────────────────────────────
    pan_verified = None
    if pan:
        if _validate_pan(pan):
            pan_verified = True
            logger.info("request_id=%s agent=kyc pan_format=valid",
                        state.get("request_id", "unknown"))
        else:
            pan_verified = False
            mismatches.append(f"PAN '{pan}' does not match required format ABCDE1234F")
            score -= 0.2

    # ── 5. Name consistency with OCR-extracted name (if available) ───────────
    ocr_name = (state.get("ocr_extracted_data") or {}).get("name", "")
    if name and ocr_name:
        similarity = _name_similarity(name, ocr_name)
        if similarity < 0.7:
            mismatches.append(
                f"Name mismatch: declared '{name}' vs document '{ocr_name}' "
                f"(similarity {similarity:.0%})"
            )
            score -= 0.2

    score = round(max(0.0, score), 2)
    kyc_verified = score >= 0.5 and len([m for m in mismatches if "checksum" in m or "format" in m]) == 0

    state["kyc_verified"] = kyc_verified
    state["kyc_score"] = score
    state["kyc_mismatches"] = mismatches
    state["kyc_data"] = {
        "name": name,
        "aadhaar_number": aadhaar,
        "dob": state.get("submitted_dob") or declared.get("dob") or "",
        "pan": pan or None,
        "pan_verified": pan_verified,
        "verification_score": score,
    }

    if not kyc_verified:
        state["rejected"] = True
        state["rejection_reason"] = (
            "KYC verification failed: " + "; ".join(mismatches or ["Unknown reason"])
        )
        state.setdefault("errors", []).append("KYC verification failed")
        logger.warning("request_id=%s agent=kyc status=failed mismatches=%s",
                       state.get("request_id", "unknown"), mismatches)
    else:
        logger.info("request_id=%s agent=kyc status=complete score=%.2f mismatches=%d",
                    state.get("request_id", "unknown"), score, len(mismatches))

    return state


# ─────────────────────────────────────────────────────────────────────────────
# Placeholder for production DigiLocker integration
# ─────────────────────────────────────────────────────────────────────────────

async def _digilocker_verify(aadhaar: str, name: str) -> dict[str, Any]:
    """
    Stub for production UIDAI / DigiLocker API call.

    In production replace with:
      - POST https://api.digitallocker.gov.in/v1/verify/aadhaar
      - Requires OAuth2 client credentials from DigiLocker developer portal
    """
    raise NotImplementedError("DigiLocker integration not yet implemented")
