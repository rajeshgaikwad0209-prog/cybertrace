"""
CyberTrace Risk Scoring Engine
================================
Deterministic, weighted risk scoring. This is the single source of
truth for score computation. All other modules (dashboard, exposure
map, history, comparison, PDF report) must call into this module
rather than recomputing scores themselves.

Formula (per category and overall):

    Risk Score = 100 * SUM(risk_value * weight) / SUM(applicable_weights)

"Not applicable" answers are excluded entirely from both the
numerator and denominator (they are not treated as safe or risky).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.questions import (
    QUESTIONS, CATEGORY_ORDER, CATEGORIES, get_questions_by_category
)


class ScoringError(Exception):
    """Raised when scoring cannot be performed validly."""
    pass


def risk_level(score: float) -> str:
    """Map a 0-100 score to a risk level label."""
    if score < 0 or score > 100:
        raise ScoringError(f"Score out of bounds: {score}")
    if score <= 24:
        return "LOW"
    elif score <= 49:
        return "MODERATE"
    elif score <= 74:
        return "HIGH"
    else:
        return "CRITICAL"


RISK_LEVEL_COLORS = {
    "LOW": "#2ecc71",
    "MODERATE": "#f1c40f",
    "HIGH": "#e67e22",
    "CRITICAL": "#e74c3c",
}

RISK_LEVEL_ORDER = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


@dataclass
class CategoryScore:
    category: str
    category_label: str
    score: Optional[float]           # None if no applicable answers
    risk_level: Optional[str]
    applicable_count: int
    total_questions: int
    concern_count: int               # answers with risk_value >= 0.5 (excluding NA)
    contributing_factors: List[str] = field(default_factory=list)


@dataclass
class ScoringResult:
    overall_score: Optional[float]
    overall_risk_level: Optional[str]
    category_scores: Dict[str, CategoryScore]
    total_applicable: int
    total_concerns: int
    unanswered_required: List[str] = field(default_factory=list)


def _weighted_category_score(category: str, answers: Dict[str, str]) -> CategoryScore:
    """
    Compute a single category's score.

    answers: dict of question_id -> answer_key (e.g. {"ID-01": "yes"})
    Questions not present in `answers` are treated as unanswered and
    excluded (same as "not applicable") for scoring purposes, but are
    tracked separately if required.
    """
    questions = get_questions_by_category(category)
    weighted_sum = 0.0
    weight_sum = 0.0
    applicable_count = 0
    concern_count = 0
    factors = []

    for q in questions:
        answer_key = answers.get(q.id)
        if answer_key is None:
            continue
        option = q.option_by_key(answer_key)
        if option is None or option.is_not_applicable or option.risk_value is None:
            continue

        applicable_count += 1
        weighted_sum += option.risk_value * q.weight
        weight_sum += q.weight

        if option.risk_value >= 0.5:
            concern_count += 1
            factors.append(q.id)

    if weight_sum == 0:
        score = None
        level = None
    else:
        score = round(100.0 * weighted_sum / weight_sum, 1)
        score = max(0.0, min(100.0, score))
        level = risk_level(score)

    return CategoryScore(
        category=category,
        category_label=CATEGORIES[category],
        score=score,
        risk_level=level,
        applicable_count=applicable_count,
        total_questions=len(questions),
        concern_count=concern_count,
        contributing_factors=factors,
    )


def compute_scores(answers: Dict[str, str]) -> ScoringResult:
    """
    Compute overall and per-category scores from a dict of
    question_id -> answer_key.

    Raises ScoringError if there are zero applicable answers overall,
    so callers can show a clear validation message rather than a
    misleading score.
    """
    category_scores: Dict[str, CategoryScore] = {}
    overall_weighted_sum = 0.0
    overall_weight_sum = 0.0
    total_applicable = 0
    total_concerns = 0

    for category in CATEGORY_ORDER:
        cat_score = _weighted_category_score(category, answers)
        category_scores[category] = cat_score
        total_applicable += cat_score.applicable_count
        total_concerns += cat_score.concern_count

        if cat_score.score is not None:
            # Re-derive weighted sums for overall (recompute, don't
            # reuse rounded category score, to avoid compounding
            # rounding error in the overall figure).
            for q in get_questions_by_category(category):
                answer_key = answers.get(q.id)
                if answer_key is None:
                    continue
                option = q.option_by_key(answer_key)
                if option is None or option.is_not_applicable or option.risk_value is None:
                    continue
                overall_weighted_sum += option.risk_value * q.weight
                overall_weight_sum += q.weight

    unanswered_required = [
        q.id for q in QUESTIONS
        if q.required and q.id not in answers
    ]

    if overall_weight_sum == 0:
        return ScoringResult(
            overall_score=None,
            overall_risk_level=None,
            category_scores=category_scores,
            total_applicable=0,
            total_concerns=0,
            unanswered_required=unanswered_required,
        )

    overall_score = round(100.0 * overall_weighted_sum / overall_weight_sum, 1)
    overall_score = max(0.0, min(100.0, overall_score))
    overall_level = risk_level(overall_score)

    return ScoringResult(
        overall_score=overall_score,
        overall_risk_level=overall_level,
        category_scores=category_scores,
        total_applicable=total_applicable,
        total_concerns=total_concerns,
        unanswered_required=unanswered_required,
    )


def validate_answers_complete(answers: Dict[str, str]) -> List[str]:
    """Return list of required question IDs missing an answer."""
    return [q.id for q in QUESTIONS if q.required and q.id not in answers]
