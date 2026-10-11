"""
Unit tests for app.core.recommendations

Run with: pytest tests/test_recommendations.py -v
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.core.recommendations import generate_recommendations, recommendation_summary
from app.core.questions import QUESTIONS, get_question


class TestRecommendationGeneration:
    def test_no_answers_no_recommendations(self):
        assert generate_recommendations({}) == []

    def test_low_risk_answers_produce_no_recommendations(self):
        answers = {}
        for q in QUESTIONS:
            answers[q.id] = "yes" if q.reverse_scored else "no"
        recs = generate_recommendations(answers)
        assert recs == []

    def test_high_risk_answer_produces_recommendation(self):
        answers = {"ID-02": "yes"}  # DOB publicly visible, weight 1.3
        recs = generate_recommendations(answers)
        assert len(recs) == 1
        assert recs[0].source_question_ids == ["ID-02"]
        assert "ID-02" in recs[0].reason or "date of birth" in recs[0].reason.lower()

    def test_na_answer_produces_no_recommendation(self):
        answers = {"ID-02": "na"}
        recs = generate_recommendations(answers)
        assert recs == []

    def test_partial_answer_produces_recommendation(self):
        answers = {"ID-01": "partial"}  # risk_value 0.5, meets threshold
        recs = generate_recommendations(answers)
        assert len(recs) == 1

    def test_reverse_scored_question_direction(self):
        # SEC-01: answering "no" (not using MFA) should trigger a recommendation
        answers_no_mfa = {"SEC-01": "no"}
        recs = generate_recommendations(answers_no_mfa)
        assert len(recs) == 1

        # answering "yes" (uses MFA) should NOT trigger a recommendation
        answers_has_mfa = {"SEC-01": "yes"}
        recs2 = generate_recommendations(answers_has_mfa)
        assert len(recs2) == 0

    def test_recommendations_sorted_by_priority(self):
        answers = {q.id: ("no" if q.reverse_scored else "yes") for q in QUESTIONS}
        recs = generate_recommendations(answers)
        priorities = [r.priority for r in recs]
        order_map = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        values = [order_map[p] for p in priorities]
        assert values == sorted(values)

    def test_each_recommendation_has_action_steps(self):
        answers = {q.id: ("no" if q.reverse_scored else "yes") for q in QUESTIONS}
        recs = generate_recommendations(answers)
        for rec in recs:
            assert len(rec.action_steps) >= 1
            assert all(isinstance(s, str) and s for s in rec.action_steps)

    def test_every_question_can_generate_a_traceable_recommendation(self):
        # Each high-risk answer, in isolation, should trace back to its own question.
        for q in QUESTIONS:
            bad_key = "no" if q.reverse_scored else "yes"
            answers = {q.id: bad_key}
            recs = generate_recommendations(answers)
            assert len(recs) == 1, f"Expected 1 recommendation for {q.id}, got {len(recs)}"
            assert recs[0].source_question_ids == [q.id]
            assert recs[0].category == q.category


class TestRecommendationSummary:
    def test_summary_counts_match_total(self):
        answers = {q.id: ("no" if q.reverse_scored else "yes") for q in QUESTIONS}
        recs = generate_recommendations(answers)
        summary = recommendation_summary(recs)
        assert sum(summary.values()) == len(recs)

    def test_summary_has_all_priority_keys(self):
        recs = generate_recommendations({})
        summary = recommendation_summary(recs)
        assert set(summary.keys()) == {"Critical", "High", "Medium", "Low"}


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
