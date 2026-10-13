"""Regression tests for API input validation and in-memory HMAC audit integrity."""
import pytest
from pydantic import ValidationError
from agents.base import AuditTrail
from agents.api import MASCCRequest, api_score

VALID = {
    "burden": "none_mild", "no_hypotension": True, "no_copd": True,
    "favorable_malignancy": True, "no_dehydration": True,
    "outpatient_onset": True, "age_under_60": True,
}


def test_api_returns_validated_index():
    assert api_score(MASCCRequest(**VALID))["score"] == 26
    assert api_score(MASCCRequest(**{**VALID, "no_hypotension": False}))["score"] == 21


def test_api_rejects_missing_or_coerced_inputs():
    with pytest.raises(ValidationError):
        MASCCRequest(**{**VALID, "no_hypotension": "maybe"})
    with pytest.raises(ValidationError):
        MASCCRequest(**{key: v for key, v in VALID.items() if key != "no_copd"})


def test_hmac_verification_detects_tampering():
    trail = AuditTrail(secret_key="testing-only-fixed-secret")
    trail.log("worker", "system", "CHECK", {"status": "ok"})
    trail.log("worker", "system", "CHECK", {"status": "ok"})
    assert trail.verify_integrity()
    snapshot = trail.get_trail()
    snapshot[0]["actor"] = "someone-else"
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "someone-else"
    assert not trail.verify_integrity()


def test_modified_last_signature_is_rejected():
    trail = AuditTrail(secret_key="testing-only-fixed-secret")
    trail.log("system", "system", "CHECK", {"status": "ok"})
    trail.logs[0]["current_hash"] = "f" * 64
    assert not trail.verify_integrity()
