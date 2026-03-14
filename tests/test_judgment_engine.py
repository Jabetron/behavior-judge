from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from behavior_judge.models import (
    BehaviorScores,
    ExistingMetrics,
    JudgmentVerdict,
    LegalityResearch,
    RelevantLaw,
)
from behavior_judge.scoring.scorer import compute_metric_agreement


def make_verdict(overall: float = 7.0, blind_spots: list[str] | None = None) -> JudgmentVerdict:
    return JudgmentVerdict(
        scores=BehaviorScores(
            safety_margin=7.0,
            comfort=8.0,
            social_compliance=7.0,
            legality=overall,
            decision_quality=7.0,
            overall=overall,
        ),
        behavior_description="Vehicle merged smoothly.",
        reasoning="Adequate gap maintained.",
        legal_violations=[],
        metric_blind_spots=blind_spots or [],
        recommendations="No changes needed.",
        confidence=0.85,
    )


def make_metrics(collision: bool = False, goal_reached: bool = True) -> ExistingMetrics:
    return ExistingMetrics(
        collision=collision,
        max_jerk=0.8,
        max_acceleration=2.4,
        goal_reached=goal_reached,
        time_to_complete_s=5.0,
    )


class TestMetricAgreement:
    def test_agreement_when_both_pass(self):
        result = compute_metric_agreement(make_verdict(overall=8.0), make_metrics())
        assert result["agreement"] is True
        assert result["divergence_detected"] is False
        assert result["divergence_type"] is None

    def test_false_pass_detected(self):
        """Metrics say PASS but LLM says FAIL — most dangerous divergence."""
        result = compute_metric_agreement(make_verdict(overall=4.0), make_metrics())
        assert result["divergence_detected"] is True
        assert result["divergence_type"] == "FALSE_PASS"
        assert result["metric_verdict"] == "PASS"
        assert result["llm_verdict"] == "FAIL"

    def test_false_fail_detected(self):
        """Metrics say FAIL but LLM says PASS — overly strict metric."""
        result = compute_metric_agreement(make_verdict(overall=8.0), make_metrics(collision=True))
        assert result["divergence_detected"] is True
        assert result["divergence_type"] == "FALSE_FAIL"

    def test_blind_spot_count(self):
        blind_spots = ["Failed to yield at crosswalk", "Exceeded speed limit briefly"]
        result = compute_metric_agreement(make_verdict(blind_spots=blind_spots), make_metrics())
        assert result["blind_spot_count"] == 2
