"""
CyberTrace Recommendation Engine
===================================
Generates personalized, rule-based recommendations from a user's
assessment answers. No external AI service is required.

Each recommendation is derived directly from one or more specific
answers, so the "reason" field always traces back to something the
user actually reported.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.questions import get_question, QUESTIONS

PRIORITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


@dataclass
class Recommendation:
    rec_id: str                # stable id, e.g. "REC-ID-01"
    title: str
    explanation: str
    priority: str               # Critical / High / Medium / Low
    category: str
    action_steps: List[str]
    reason: str                 # why this was generated (plain language)
    source_question_ids: List[str] = field(default_factory=list)
    completed: bool = False


def _priority_for_risk(risk_value: float, weight: float) -> str:
    """Derive a priority from how risky the answer was and how heavily
    weighted the underlying question is."""
    severity = risk_value * weight
    if severity >= 1.1:
        return "Critical"
    elif severity >= 0.8:
        return "High"
    elif severity >= 0.4:
        return "Medium"
    else:
        return "Low"


# Extra, more specific action steps layered on top of each question's
# single default recommended_action, keyed by question id.
ACTION_STEPS: Dict[str, List[str]] = {
    "ID-01": [
        "Replace your full legal name with a display name on public profiles.",
        "Check search engines for your name and note where it appears publicly.",
    ],
    "ID-02": [
        "Remove or hide your birth date field on social platforms.",
        "Update account recovery questions that rely on your birth date.",
    ],
    "ID-03": [
        "List out identifying details across all your public profiles together.",
        "Remove or generalize details that aren't necessary to share.",
    ],
    "ID-04": [
        "Avoid tagging family members by name in public posts.",
        "Ask family members to review their own visibility settings too.",
    ],
    "AC-01": [
        "Create distinct usernames for sensitive vs. public-facing accounts.",
        "Avoid including birth years or real names in usernames.",
    ],
    "AC-02": [
        "Use different profile photos and bios for personal vs. professional accounts.",
        "Remove cross-links between personal and professional profiles.",
    ],
    "AC-03": [
        "Remove 'find me elsewhere' links from public profiles.",
        "Limit cross-platform discoverability settings where available.",
    ],
    "AC-04": [
        "Go through each major account's privacy/visibility settings this week.",
        "Set a recurring reminder to review account visibility every 6 months.",
    ],
    "SM-01": [
        "Switch personal social accounts to private/followers-only.",
        "Review your follower list and remove unfamiliar accounts.",
    ],
    "SM-02": [
        "Post about routine activities after they happen, not in real time.",
        "Avoid consistent timestamps that reveal a predictable schedule.",
    ],
    "SM-03": [
        "Disable location tagging/geotags on photo posts.",
        "Review older posts for visible location clues and edit or remove them.",
    ],
    "SM-04": [
        "Limit audience for sensitive personal updates to close contacts.",
        "Consider a delay before posting travel plans publicly.",
    ],
    "CI-01": [
        "Create a separate email address for public-facing use.",
        "Remove your primary personal email from public profiles.",
    ],
    "CI-02": [
        "Remove your personal phone number from public listings.",
        "Use a secondary or virtual number for any public contact needs.",
    ],
    "CI-03": [
        "Audit each profile's contact fields and remove unnecessary ones.",
    ],
    "CI-04": [
        "Set up a dedicated public-facing email or number if you haven't already.",
    ],
    "PI-01": [
        "Search your name periodically and note where it appears.",
        "Contact site owners or use opt-out tools to request removal where available.",
    ],
    "PI-02": [
        "Review PDFs and documents you've posted publicly for unnecessary personal details.",
        "Replace full addresses or birth dates in public documents with general info.",
    ],
    "PI-03": [
        "Locate old or abandoned profiles and deactivate them if no longer needed.",
        "Update outdated profile information that no longer reflects your preferences.",
    ],
    "PI-04": [
        "Schedule a recurring self-review of your public information.",
    ],
    "SEC-01": [
        "Enable MFA on your email account first, since it protects password resets for other accounts.",
        "Use an authenticator app rather than SMS-based MFA where possible.",
    ],
    "SEC-02": [
        "Adopt a password manager to generate and store unique passwords.",
        "Prioritize changing reused passwords on your most sensitive accounts first.",
    ],
    "SEC-03": [
        "Review privacy settings on your top 3 most-used platforms this month.",
        "Set a recurring calendar reminder to repeat this review.",
    ],
    "SEC-04": [
        "Open your account's connected-apps page and revoke unused permissions.",
        "Repeat this review periodically, since new apps get authorized over time.",
    ],
}


def generate_recommendations(answers: Dict[str, str]) -> List[Recommendation]:
    """
    Generate recommendations from a dict of question_id -> answer_key.
    Only answers indicating meaningful risk (risk_value >= 0.5) produce
    a recommendation.
    """
    recommendations: List[Recommendation] = []

    for q in QUESTIONS:
        answer_key = answers.get(q.id)
        if answer_key is None:
            continue
        option = q.option_by_key(answer_key)
        if option is None or option.is_not_applicable or option.risk_value is None:
            continue
        if option.risk_value < 0.5:
            continue  # no concern, no recommendation needed

        priority = _priority_for_risk(option.risk_value, q.weight)
        steps = ACTION_STEPS.get(q.id, [q.recommended_action])

        reason = (
            f"You answered \"{option.label}\" to: \"{q.text}\""
        )

        recommendations.append(Recommendation(
            rec_id=f"REC-{q.id}",
            title=q.recommended_action.rstrip("."),
            explanation=q.explanation,
            priority=priority,
            category=q.category,
            action_steps=steps,
            reason=reason,
            source_question_ids=[q.id],
        ))

    # Sort by priority (Critical first), then by category order
    recommendations.sort(key=lambda r: (PRIORITY_ORDER.get(r.priority, 99), r.category))
    return recommendations


def recommendation_summary(recs: List[Recommendation]) -> Dict[str, int]:
    """Count recommendations by priority."""
    summary = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for r in recs:
        summary[r.priority] = summary.get(r.priority, 0) + 1
    return summary
