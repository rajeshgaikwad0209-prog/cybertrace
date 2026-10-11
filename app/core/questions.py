"""
CyberTrace Question Bank
=========================
Defines the structured question set used for the digital footprint
assessment. Every question maps its possible answers to a normalized
risk value between 0.0 (no risk) and 1.0 (maximum risk).

This module is pure data + light validation. It has no Streamlit or
database dependencies so it can be unit tested in isolation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class AnswerOption:
    """A single selectable answer for a question."""
    key: str                 # stable key stored in the database
    label: str                # text shown to the user
    risk_value: Optional[float]  # 0.0-1.0, or None for "Not applicable"
    is_not_applicable: bool = False


@dataclass(frozen=True)
class Question:
    id: str                   # unique identifier, e.g. "ID-01"
    category: str              # category key, e.g. "identity"
    text: str                  # the question itself
    explanation: str           # why this matters
    options: List[AnswerOption]
    weight: float              # relative importance within its category
    recommended_action: str    # default recommendation text
    required: bool = True
    reverse_scored: bool = False  # True for protective-practice questions

    def option_by_key(self, key: str) -> Optional[AnswerOption]:
        for opt in self.options:
            if opt.key == key:
                return opt
        return None


# ---------------------------------------------------------------------------
# Standard answer scales
# ---------------------------------------------------------------------------

# Standard exposure scale: higher exposure = higher risk
EXPOSURE_SCALE = [
    AnswerOption("no", "No / Not exposed", 0.0),
    AnswerOption("partial", "Partially / Unsure", 0.5),
    AnswerOption("yes", "Yes / Exposed", 1.0),
    AnswerOption("na", "Not applicable", None, is_not_applicable=True),
]

# Protective practice scale: "Yes, I do this" is GOOD (low risk).
# We still store risk_value directly (already reversed) so the scoring
# engine never needs to branch on reverse_scored for the math itself;
# reverse_scored is kept as metadata for transparency/reporting.
PROTECTIVE_SCALE = [
    AnswerOption("yes", "Yes, consistently", 0.0),
    AnswerOption("partial", "Partially / Sometimes", 0.5),
    AnswerOption("no", "No / Not done", 1.0),
    AnswerOption("na", "Not applicable", None, is_not_applicable=True),
]

CATEGORIES: Dict[str, str] = {
    "identity": "Identity Exposure",
    "accounts": "Account Exposure",
    "social": "Social Media Exposure",
    "contact": "Contact Information",
    "public": "Public Information Exposure",
    "security": "Security & Privacy Practices",
}

CATEGORY_ORDER = ["identity", "accounts", "social", "contact", "public", "security"]

CATEGORY_DESCRIPTIONS = {
    "identity": "How visible your core identifying details are to the public.",
    "accounts": "Whether your accounts can be linked together or to your real identity.",
    "social": "What your social media activity reveals about your life and routines.",
    "contact": "How exposed your personal contact details are.",
    "public": "Personal details that may appear in public-facing pages or documents.",
    "security": "The protective habits you use to reduce risk across all accounts.",
}


# ---------------------------------------------------------------------------
# Question Bank
# ---------------------------------------------------------------------------

QUESTIONS: List[Question] = [

    # ---------------- CATEGORY 1: IDENTITY EXPOSURE ----------------
    Question(
        id="ID-01", category="identity",
        text="Is your full legal name publicly visible on any social media profile or website you control?",
        explanation="A publicly visible full name makes it easier to connect your other online activity to your real identity.",
        options=EXPOSURE_SCALE, weight=1.0,
        recommended_action="Consider using a display name that isn't your full legal name on public-facing profiles.",
    ),
    Question(
        id="ID-02", category="identity",
        text="Is your date of birth publicly visible on any profile or public page?",
        explanation="Date of birth is commonly used in identity verification and account recovery, making its exposure higher risk.",
        options=EXPOSURE_SCALE, weight=1.3,
        recommended_action="Remove or restrict visibility of your date of birth on public profiles.",
    ),
    Question(
        id="ID-03", category="identity",
        text="Have you posted identifying details (e.g. school, employer, hometown) that together could help someone impersonate you?",
        explanation="Individually harmless details can combine to enable impersonation or targeted social engineering.",
        options=EXPOSURE_SCALE, weight=1.1,
        recommended_action="Review your combined public profile information as a whole, not just field by field.",
    ),
    Question(
        id="ID-04", category="identity",
        text="Is identifying information about immediate family members (names, schools, workplaces) publicly visible on your profiles?",
        explanation="Family details are frequently used in security questions and social engineering attempts.",
        options=EXPOSURE_SCALE, weight=0.9,
        recommended_action="Avoid tagging or naming family members in publicly visible posts where possible.",
    ),

    # ---------------- CATEGORY 2: ACCOUNT EXPOSURE ----------------
    Question(
        id="AC-01", category="accounts",
        text="Do you reuse the same recognizable username across multiple online services?",
        explanation="A reused, recognizable username lets others link your accounts together across platforms.",
        options=EXPOSURE_SCALE, weight=1.1,
        recommended_action="Use distinct usernames for sensitive accounts versus public or professional ones.",
    ),
    Question(
        id="AC-02", category="accounts",
        text="Are your personal and professional accounts easily connected (e.g. same photo, bio, or linked profiles)?",
        explanation="Linking personal and professional identities expands what someone can learn from either account alone.",
        options=EXPOSURE_SCALE, weight=1.0,
        recommended_action="Separate personal and professional presences, or review what is cross-linked.",
    ),
    Question(
        id="AC-03", category="accounts",
        text="Does your public profile include details that would let someone find your other accounts (e.g. 'find me on...' links)?",
        explanation="Cross-referencing links make it trivial to build a complete profile of your online presence.",
        options=EXPOSURE_SCALE, weight=0.8,
        recommended_action="Limit cross-platform links on profiles that are publicly visible.",
    ),
    Question(
        id="AC-04", category="accounts",
        text="Have you reviewed which of your accounts are set to public versus private visibility?",
        explanation="Many accounts default to public visibility, which users are often unaware of.",
        options=PROTECTIVE_SCALE, weight=1.0, reverse_scored=True,
        recommended_action="Audit each account's visibility settings and restrict ones that don't need to be public.",
    ),

    # ---------------- CATEGORY 3: SOCIAL MEDIA EXPOSURE ----------------
    Question(
        id="SM-01", category="social",
        text="Are your personal posts (not just a business or public page) visible to anyone, not just approved followers?",
        explanation="Public personal posts can be viewed, collected, and cross-referenced by anyone, not just people you know.",
        options=EXPOSURE_SCALE, weight=1.1,
        recommended_action="Set personal accounts to private/followers-only where the platform supports it.",
    ),
    Question(
        id="SM-02", category="social",
        text="Do your posts reveal predictable daily routines (e.g. regular gym times, commute patterns, school pickup)?",
        explanation="Predictable routines posted publicly can enable physical-world risks like stalking or burglary while away.",
        options=EXPOSURE_SCALE, weight=1.2,
        recommended_action="Avoid posting routine activities in real time; consider posting after the fact instead.",
    ),
    Question(
        id="SM-03", category="social",
        text="Do your photos or captions reveal your home location, workplace, or frequently visited places?",
        explanation="Location details embedded in photos or captions can reveal where you live or work.",
        options=EXPOSURE_SCALE, weight=1.2,
        recommended_action="Review photo metadata and captions for location clues before posting publicly.",
    ),
    Question(
        id="SM-04", category="social",
        text="Do you share detailed personal information (relationship status, health updates, travel plans) publicly?",
        explanation="Oversharing personal context increases the amount of exploitable detail available to strangers.",
        options=EXPOSURE_SCALE, weight=0.9,
        recommended_action="Consider sharing sensitive personal updates with a limited audience instead of publicly.",
    ),

    # ---------------- CATEGORY 4: CONTACT INFORMATION ----------------
    Question(
        id="CI-01", category="contact",
        text="Is a personal email address publicly displayed on any profile, website, or forum post?",
        explanation="Publicly listed email addresses are frequently harvested for spam, phishing, and social engineering.",
        options=EXPOSURE_SCALE, weight=1.0,
        recommended_action="Use a separate email address for public-facing contact rather than your primary personal email.",
    ),
    Question(
        id="CI-02", category="contact",
        text="Is a personal phone number publicly displayed anywhere online?",
        explanation="A public phone number can be used for spam, SIM-swap attempts, or unwanted contact.",
        options=EXPOSURE_SCALE, weight=1.2,
        recommended_action="Remove your personal phone number from public listings; use a secondary number if needed publicly.",
    ),
    Question(
        id="CI-03", category="contact",
        text="Do any of your public profiles include contact information that isn't actually necessary to display?",
        explanation="Unnecessary contact details increase exposure without providing any real benefit.",
        options=EXPOSURE_SCALE, weight=0.8,
        recommended_action="Remove contact fields from profiles unless they serve a clear, necessary purpose.",
    ),
    Question(
        id="CI-04", category="contact",
        text="Do you maintain a clear separation between personal contact methods and public-facing ones?",
        explanation="Separating personal from public contact channels limits the damage if one is exposed or abused.",
        options=PROTECTIVE_SCALE, weight=0.9, reverse_scored=True,
        recommended_action="Create a dedicated public-facing email or number separate from personal channels.",
    ),

    # ---------------- CATEGORY 5: PUBLIC INFORMATION EXPOSURE ----------------
    Question(
        id="PI-01", category="public",
        text="Do you know of personal details about you appearing on public pages you do not control (e.g. old forum posts, directories)?",
        explanation="Information on pages you don't control is harder to remove and often forgotten about.",
        options=EXPOSURE_SCALE, weight=1.0,
        recommended_action="Search for your own name periodically and request removal from directories where possible.",
    ),
    Question(
        id="PI-02", category="public",
        text="Have you included unnecessary personal information in public documents (resumes, PDFs, event listings)?",
        explanation="Public documents often persist online long after their original purpose and can leak details like addresses.",
        options=EXPOSURE_SCALE, weight=0.9,
        recommended_action="Review publicly posted documents and remove unnecessary personal details like full address or birth date.",
    ),
    Question(
        id="PI-03", category="public",
        text="Are there public profiles (old or current) that link unrelated personal details about you together?",
        explanation="Old or abandoned profiles can aggregate details that you would not want connected today.",
        options=EXPOSURE_SCALE, weight=0.9,
        recommended_action="Locate and deactivate or update old profiles that combine outdated personal details.",
    ),
    Question(
        id="PI-04", category="public",
        text="Have you reviewed what information about you is publicly available and identified anything you'd like removed?",
        explanation="A periodic self-review is one of the most effective ways to catch unwanted public exposure early.",
        options=PROTECTIVE_SCALE, weight=0.8, reverse_scored=True,
        recommended_action="Schedule a periodic self-review of your publicly available information.",
    ),

    # ---------------- CATEGORY 6: SECURITY & PRIVACY PRACTICES ----------------
    Question(
        id="SEC-01", category="security",
        text="Do you use multi-factor authentication (MFA) on your important accounts (email, banking, social media)?",
        explanation="MFA significantly reduces the risk of account takeover even if a password is compromised.",
        options=PROTECTIVE_SCALE, weight=1.3, reverse_scored=True,
        recommended_action="Enable multi-factor authentication on email, banking, and social media accounts where available.",
    ),
    Question(
        id="SEC-02", category="security",
        text="Do you use unique passwords for each important account rather than reusing the same password?",
        explanation="Password reuse means a single breach can compromise many of your accounts at once.",
        options=PROTECTIVE_SCALE, weight=1.2, reverse_scored=True,
        recommended_action="Use a password manager to maintain unique passwords for each account.",
    ),
    Question(
        id="SEC-03", category="security",
        text="Have you reviewed your privacy settings on your main social media accounts in the last 12 months?",
        explanation="Platforms frequently change default privacy settings, which can silently increase exposure.",
        options=PROTECTIVE_SCALE, weight=1.0, reverse_scored=True,
        recommended_action="Review privacy settings on your main accounts at least once or twice a year.",
    ),
    Question(
        id="SEC-04", category="security",
        text="Have you reviewed which third-party apps have permission to access your accounts?",
        explanation="Forgotten third-party app permissions are a common, overlooked source of data exposure.",
        options=PROTECTIVE_SCALE, weight=0.9, reverse_scored=True,
        recommended_action="Review and revoke unnecessary third-party app permissions on your key accounts.",
    ),
]


def get_questions_by_category(category: str) -> List[Question]:
    return [q for q in QUESTIONS if q.category == category]


def get_question(question_id: str) -> Optional[Question]:
    for q in QUESTIONS:
        if q.id == question_id:
            return q
    return None


def all_question_ids() -> List[str]:
    return [q.id for q in QUESTIONS]
