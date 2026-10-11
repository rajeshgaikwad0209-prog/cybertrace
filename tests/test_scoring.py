"""
Unit tests for app.core.scoring

Run with: pytest tests/test_scoring.py -v
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.core.scoring import (
    compute_scores, risk_level, ScoringError, validate_answers_complete
)
from app.core.questions import QUESTIONS, all_question_ids, get_question


def all_answers_with(key: str) -> dict:
    """Helper: build an answers dict with the same answer key for every question."""
    return {q.id: key for q in QUESTIONS}


class TestRiskLevelBoundaries:
    def test_low_boundary_zero(self):
        assert risk_level(0) == "LOW"

    def test_low_upper_boundary(self):
        assert risk_level(24) == "LOW"

    def test_moderate_lower_boundary(self):
        assert risk_level(25) == "MODERATE"

    def test_moderate_upper_boundary(self):
        assert risk_level(49) == "MODERATE"

    def test_high_lower_boundary(self):
        assert risk_level(50) == "HIGH"

    def test_high_upper_boundary(self):
        assert risk_level(74) == "HIGH"

    def test_critical_lower_boundary(self):
        assert risk_level(75) == "CRITICAL"

    def test_critical_upper_boundary(self):
        assert risk_level(100) == "CRITICAL"

    def test_out_of_bounds_raises(self):
        with pytest.raises(ScoringError):
            risk_level(101)
        with pytest.raises(ScoringError):
            risk_level(-1)


class TestComputeScoresEmptyAndEdge:
    def test_no_answers_returns_none_score(self):
        result = compute_scores({})
        assert result.overall_score is None
        assert result.overall_risk_level is None
        assert result.total_applicable == 0

    def test_all_not_applicable_returns_none_score(self):
        answers = all_answers_with("na")
        result = compute_scores(answers)
        assert result.overall_score is None
        assert result.total_applicable == 0

    def test_partial_answers_only_counts_applicable(self):
        # Answer only the identity category
        answers = {"ID-01": "yes", "ID-02": "yes", "ID-03": "yes", "ID-04": "yes"}
        result = compute_scores(answers)
        assert result.overall_score is not None
        # Identity category should be fully applicable (4 questions)
        assert result.category_scores["identity"].applicable_count == 4
        # Other categories should have no applicable answers
        assert result.category_scores["accounts"].score is None


class TestComputeScoresExtremes:
    def test_all_max_risk_answers_yield_100(self):
        # For EXPOSURE_SCALE, "yes" = 1.0 risk (max exposure = bad)
        # For PROTECTIVE_SCALE, "no" = 1.0 risk (not doing protective practice = bad)
        answers = {}
        for q in QUESTIONS:
            if q.reverse_scored:
                answers[q.id] = "no"   # worst protective answer
            else:
                answers[q.id] = "yes"  # worst exposure answer
        result = compute_scores(answers)
        assert result.overall_score == 100.0
        assert result.overall_risk_level == "CRITICAL"
        for cat_score in result.category_scores.values():
            assert cat_score.score == 100.0

    def test_all_min_risk_answers_yield_0(self):
        answers = {}
        for q in QUESTIONS:
            if q.reverse_scored:
                answers[q.id] = "yes"  # best protective answer
            else:
                answers[q.id] = "no"   # best exposure answer (not exposed)
        result = compute_scores(answers)
        assert result.overall_score == 0.0
        assert result.overall_risk_level == "LOW"

    def test_all_partial_answers_yield_50(self):
        answers = all_answers_with("partial")
        result = compute_scores(answers)
        assert result.overall_score == 50.0
        assert result.overall_risk_level == "HIGH"


class TestNotApplicableExclusion:
    def test_na_excluded_from_denominator(self):
        # Two questions, one NA one max risk -> score should be 100,
        # not 50 (NA must not count as "safe").
        q1, q2 = QUESTIONS[0], QUESTIONS[1]
        answers = {q1.id: "na", q2.id: "yes" if not q2.reverse_scored else "no"}
        result = compute_scores(answers)
        assert result.overall_score == 100.0

    def test_na_not_counted_as_concern(self):
        answers = {q.id: "na" for q in QUESTIONS}
        result = compute_scores(answers)
        assert result.total_concerns == 0


class TestWeightedScoringCorrectness:
    def test_manual_weighted_calc_matches(self):
        # Pick two identity questions with known weights and verify
        # the formula by hand.
        q1 = get_question("ID-01")  # weight 1.0, exposure scale
        q2 = get_question("ID-02")  # weight 1.3, exposure scale
        answers = {q1.id: "yes", q2.id: "no"}  # risk 1.0 and 0.0
        result = compute_scores(answers)
        expected = 100.0 * (1.0 * 1.0 + 0.0 * 1.3) / (1.0 + 1.3)
        cat_score = result.category_scores["identity"].score
        assert cat_score == round(expected, 1)

    def test_reverse_scored_question_direction(self):
        # SEC-01 is reverse scored: "yes" (does MFA) = 0.0 risk
        q = get_question("SEC-01")
        assert q.reverse_scored is True
        opt_yes = q.option_by_key("yes")
        opt_no = q.option_by_key("no")
        assert opt_yes.risk_value == 0.0
        assert opt_no.risk_value == 1.0


class TestConcernCounting:
    def test_concern_counted_for_high_risk_answers(self):
        answers = {"ID-01": "yes"}  # risk_value 1.0 >= 0.5 threshold
        result = compute_scores(answers)
        assert result.total_concerns == 1

    def test_no_concern_for_low_risk_answers(self):
        answers = {"ID-01": "no"}  # risk_value 0.0
        result = compute_scores(answers)
        assert result.total_concerns == 0

    def test_partial_counts_as_concern(self):
        # partial = 0.5, which is >= 0.5 threshold
        answers = {"ID-01": "partial"}
        result = compute_scores(answers)
        assert result.total_concerns == 1


class TestValidateAnswersComplete:
    def test_missing_required_detected(self):
        missing = validate_answers_complete({})
        assert len(missing) == len(all_question_ids())

    def test_all_answered_none_missing(self):
        answers = {q.id: "no" for q in QUESTIONS}
        missing = validate_answers_complete(answers)
        assert missing == []


class TestScoreBounds:
    def test_score_never_exceeds_100(self):
        answers = all_answers_with("yes")
        result = compute_scores(answers)
        assert result.overall_score <= 100.0
        for cs in result.category_scores.values():
            if cs.score is not None:
                assert cs.score <= 100.0

    def test_score_never_below_0(self):
        answers = all_answers_with("no")
        result = compute_scores(answers)
        assert result.overall_score >= 0.0
        for cs in result.category_scores.values():
            if cs.score is not None:
                assert cs.score >= 0.0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
