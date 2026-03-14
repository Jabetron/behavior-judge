from __future__ import annotations

from behavior_judge.models import ExistingMetrics, JudgmentVerdict


def compute_metric_agreement(verdict: JudgmentVerdict, metrics: ExistingMetrics) -> dict:
    """
    Quantify where LLM judgment diverges from traditional metric verdicts.
    Divergence is the signal — it reveals what your metrics are missing.
    """
    metric_passed = not metrics.collision and metrics.goal_reached
    llm_passed = verdict.scores.overall >= 6.0

    divergence_type = None
    if metric_passed and not llm_passed:
        divergence_type = "FALSE_PASS"  # metrics say OK, LLM says bad — dangerous gap
    elif not metric_passed and llm_passed:
        divergence_type = "FALSE_FAIL"  # metrics say bad, LLM says OK — overly strict metric

    return {
        "metric_verdict": "PASS" if metric_passed else "FAIL",
        "llm_verdict": "PASS" if llm_passed else "FAIL",
        "agreement": metric_passed == llm_passed,
        "divergence_detected": divergence_type is not None,
        "divergence_type": divergence_type,
        "blind_spot_count": len(verdict.metric_blind_spots),
        "legal_violation_count": len(verdict.legal_violations),
        "legality_score": verdict.scores.legality,
        "overall_score": verdict.scores.overall,
    }
