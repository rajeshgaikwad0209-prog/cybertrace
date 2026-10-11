"""
CyberTrace Profile Privacy Audit
====================================
Manual, user-entered assessment of a single public profile. This does
NOT fetch, scrape, or verify the URL — it only validates its format
and scores the user's own answers about that profile.
"""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from app.core.scoring import risk_level

ANSWER_RISK = {"yes": 1.0, "partial": 0.5, "no": 0.0}

FIELD_WEIGHTS = {
    "is_public": 1.0,
    "contact_visible": 1.2,
    "identity_exposed": 1.1,
    "routine_revealed": 1.0,
    "links_other_accounts": 0.9,
}


class URLValidationError(Exception):
    pass


def validate_profile_url(url: str) -> str:
    """Validate that a URL uses http/https only. Does not fetch it."""
    url = url.strip()
    if not url:
        return ""  # URL is optional
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise URLValidationError("URL must start with http:// or https://")
    if not parsed.netloc:
        raise URLValidationError("That doesn't look like a valid URL (missing domain).")
    return url


@dataclass
class ProfileAuditResult:
    score: Optional[float]
    risk_level: Optional[str]
    concerns: list


def score_profile_audit(answers: dict) -> ProfileAuditResult:
    """
    answers: dict with keys matching FIELD_WEIGHTS, values in
    {"yes", "partial", "no", "na"}.
    """
    weighted_sum = 0.0
    weight_sum = 0.0
    concerns = []

    field_labels = {
        "is_public": "Profile is publicly visible",
        "contact_visible": "Contact details are visible",
        "identity_exposed": "Identifying details are exposed",
        "routine_revealed": "Posts reveal daily routines",
        "links_other_accounts": "Profile links to other accounts",
    }

    for field, weight in FIELD_WEIGHTS.items():
        value = answers.get(field)
        if value is None or value == "na":
            continue
        risk_value = ANSWER_RISK.get(value)
        if risk_value is None:
            continue
        weighted_sum += risk_value * weight
        weight_sum += weight
        if risk_value >= 0.5:
            concerns.append(field_labels[field])

    if weight_sum == 0:
        return ProfileAuditResult(score=None, risk_level=None, concerns=[])

    score = round(100.0 * weighted_sum / weight_sum, 1)
    score = max(0.0, min(100.0, score))
    return ProfileAuditResult(score=score, risk_level=risk_level(score), concerns=concerns)
