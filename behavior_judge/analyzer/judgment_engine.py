from __future__ import annotations

import json
import os

import ollama

from behavior_judge.models import (
    BehaviorScores,
    ExistingMetrics,
    JudgmentVerdict,
    LegalityResearch,
)

JUDGE_MODEL = os.getenv("BJ_JUDGE_MODEL", "llama3.1")

_VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "object",
            "properties": {
                "safety_margin":      {"type": "number"},
                "comfort":            {"type": "number"},
                "social_compliance":  {"type": "number"},
                "legality":           {"type": "number"},
                "decision_quality":   {"type": "number"},
                "overall":            {"type": "number"},
            },
            "required": ["safety_margin", "comfort", "social_compliance", "legality", "decision_quality", "overall"],
        },
        "behavior_description": {"type": "string"},
        "reasoning":            {"type": "string"},
        "legal_violations":     {"type": "array", "items": {"type": "string"}},
        "metric_blind_spots":   {"type": "array", "items": {"type": "string"}},
        "recommendations":      {"type": "string"},
        "confidence":           {"type": "number"},
    },
    "required": [
        "scores", "behavior_description", "reasoning",
        "legal_violations", "metric_blind_spots", "recommendations", "confidence",
    ],
}


def judge_behavior(
    behavior_description: str,
    legality_research: LegalityResearch,
    existing_metrics: ExistingMetrics,
    scenario_type: str,
) -> JudgmentVerdict:
    laws_text = "\n".join(
        f"  - [{law.applies_to}] {law.description}  (Source: {law.source})"
        for law in legality_research.relevant_laws
    ) or "  No specific laws found for this jurisdiction/scenario."

    traditional_verdict = "FAIL" if existing_metrics.collision or not existing_metrics.goal_reached else "PASS"

    prompt = f"""You are a senior autonomous vehicle safety evaluator with deep expertise in traffic law, human factors, and AV evaluation.

## Scenario
Type: {scenario_type}
Jurisdiction: {legality_research.jurisdiction}

## Observed Behavior
{behavior_description}

## Applicable Traffic Laws
{laws_text}

Legal summary: {legality_research.research_summary}

## Existing Metric Verdicts
- Collision detected: {existing_metrics.collision}
- Max jerk: {existing_metrics.max_jerk:.3f} m/s³
- Max acceleration: {existing_metrics.max_acceleration:.3f} m/s²
- Goal reached: {existing_metrics.goal_reached}
- Time to complete: {existing_metrics.time_to_complete_s}s
- Traditional verdict: {traditional_verdict}

## Instructions
Score behavior on each dimension from 0 to 10 (10 = perfect).
Find metric blind spots — cases where traditional metrics disagree with your judgment. This is the most important output:
  - PASS metrics but poor behavior = dangerous gap
  - FAIL metrics but behavior was actually correct = overly strict metric
List any specific traffic law violations with statute references.
Give concrete recommendations.

Respond with valid JSON matching the required schema."""

    response = ollama.chat(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        format=_VERDICT_SCHEMA,
    )

    data = json.loads(response["message"]["content"])

    # Clamp all scores to [0, 10] and confidence to [0, 1]
    scores = data["scores"]
    for key in scores:
        scores[key] = max(0.0, min(10.0, float(scores[key])))
    data["confidence"] = max(0.0, min(1.0, float(data.get("confidence", 0.8))))

    return JudgmentVerdict(
        scores=BehaviorScores(**scores),
        behavior_description=data["behavior_description"],
        reasoning=data["reasoning"],
        legal_violations=data.get("legal_violations", []),
        metric_blind_spots=data.get("metric_blind_spots", []),
        recommendations=data["recommendations"],
        confidence=data["confidence"],
    )
