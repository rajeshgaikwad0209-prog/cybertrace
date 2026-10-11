"""
Unit tests for app.core.profile_audit

Run with: pytest tests/test_profile_audit.py -v
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.core.profile_audit import (
    score_profile_audit, validate_profile_url, URLValidationError
)


class TestURLValidation:
    def test_empty_url_is_allowed(self):
        assert validate_profile_url("") == ""

    def test_whitespace_only_url_is_allowed(self):
        assert validate_profile_url("   ") == ""

    def test_valid_https_url(self):
        url = "https://example.com/profile"
        assert validate_profile_url(url) == url

    def test_valid_http_url(self):
        url = "http://example.com/profile"
        assert validate_profile_url(url) == url

    def test_javascript_scheme_rejected(self):
        with pytest.raises(URLValidationError):
            validate_profile_url("javascript:alert(1)")

    def test_ftp_scheme_rejected(self):
        with pytest.raises(URLValidationError):
            validate_profile_url("ftp://example.com/file")

    def test_missing_domain_rejected(self):
        with pytest.raises(URLValidationError):
            validate_profile_url("https://")

    def test_no_scheme_rejected(self):
        with pytest.raises(URLValidationError):
            validate_profile_url("example.com/profile")


class TestProfileAuditScoring:
    def test_no_answers_returns_none(self):
        result = score_profile_audit({})
        assert result.score is None
        assert result.risk_level is None

    def test_all_na_returns_none(self):
        answers = {k: "na" for k in [
            "is_public", "contact_visible", "identity_exposed",
            "routine_revealed", "links_other_accounts"
        ]}
        result = score_profile_audit(answers)
        assert result.score is None

    def test_all_yes_yields_max_risk(self):
        answers = {k: "yes" for k in [
            "is_public", "contact_visible", "identity_exposed",
            "routine_revealed", "links_other_accounts"
        ]}
        result = score_profile_audit(answers)
        assert result.score == 100.0
        assert result.risk_level == "CRITICAL"
        assert len(result.concerns) == 5

    def test_all_no_yields_min_risk(self):
        answers = {k: "no" for k in [
            "is_public", "contact_visible", "identity_exposed",
            "routine_revealed", "links_other_accounts"
        ]}
        result = score_profile_audit(answers)
        assert result.score == 0.0
        assert result.risk_level == "LOW"
        assert result.concerns == []

    def test_partial_answer_counted_as_concern(self):
        answers = {"is_public": "partial"}
        result = score_profile_audit(answers)
        assert result.score == 50.0
        assert len(result.concerns) == 1

    def test_na_excluded_from_score(self):
        # One NA + one max-risk should score 100, not averaged down.
        answers = {"is_public": "na", "contact_visible": "yes"}
        result = score_profile_audit(answers)
        assert result.score == 100.0

    def test_mixed_answers_weighted_correctly(self):
        answers = {"is_public": "yes", "contact_visible": "no"}
        result = score_profile_audit(answers)
        # weights: is_public=1.0, contact_visible=1.2
        expected = 100.0 * (1.0 * 1.0 + 0.0 * 1.2) / (1.0 + 1.2)
        assert result.score == round(expected, 1)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
