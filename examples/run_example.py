"""
Run the full behavior judgment pipeline on a scenario directory.

Usage:
    python examples/run_example.py scenarios/sample --output reports/
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from behavior_judge.analyzer.behavior_analyzer import analyze_behavior
from behavior_judge.analyzer.judgment_engine import judge_behavior
from behavior_judge.ingestion.replay_loader import (
    compute_existing_metrics,
    load_frames,
    load_metadata,
    load_telemetry,
)
from behavior_judge.law_researcher.researcher import research_traffic_laws
from behavior_judge.models import ScenarioReport
from behavior_judge.reporting.report_generator import generate_html_report, generate_json_report
from behavior_judge.scoring.scorer import compute_metric_agreement


def run(scenario_dir: Path, output_dir: Path) -> ScenarioReport:
    print(f"\n{'='*60}")
    print(f"  behavior-judge")
    print(f"  Scenario: {scenario_dir}")
    print(f"{'='*60}\n")

    print("[1/5] Loading scenario...")
    metadata = load_metadata(scenario_dir)
    telemetry = load_telemetry(scenario_dir)
    frames = load_frames(scenario_dir)
    existing_metrics = compute_existing_metrics(telemetry)
    print(f"      {len(frames)} frames | {len(telemetry)} telemetry points")

    print("[2/5] Researching traffic laws...")
    legality_research = research_traffic_laws(metadata.location, metadata.scenario_type)
    print(f"      Found {len(legality_research.relevant_laws)} applicable laws in {legality_research.jurisdiction}")

    print("[3/5] Analyzing behavior (VLM)...")
    if frames:
        behavior_description = analyze_behavior(frames, telemetry, metadata.scenario_type, metadata.description)
    else:
        behavior_description = f"No frames available. Scenario: {metadata.description}"
        print("      Warning: no frames found, using description only")

    print("[4/5] Running judgment engine...")
    verdict = judge_behavior(behavior_description, legality_research, existing_metrics, metadata.scenario_type)

    report = ScenarioReport(
        scenario_id=metadata.scenario_id,
        metadata=metadata,
        legality_research=legality_research,
        existing_metrics=existing_metrics,
        verdict=verdict,
        generated_at=datetime.now(timezone.utc),
    )

    print("[5/5] Generating reports...")
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{metadata.scenario_id}.json"
    html_path = output_dir / f"{metadata.scenario_id}.html"
    generate_json_report(report, json_path)
    generate_html_report(report, html_path)

    agreement = compute_metric_agreement(verdict, existing_metrics)

    print(f"\n{'='*60}")
    print(f"  Results — {metadata.scenario_id}")
    print(f"{'='*60}")
    print(f"  Overall score:       {verdict.scores.overall:.1f}/10")
    print(f"  Legality score:      {verdict.scores.legality:.1f}/10  ({legality_research.jurisdiction})")
    print(f"  Traditional verdict: {agreement['metric_verdict']}")
    print(f"  LLM verdict:         {agreement['llm_verdict']}")

    if agreement["divergence_detected"]:
        print(f"\n  ⚠  DIVERGENCE: {agreement['divergence_type']}")

    if verdict.metric_blind_spots:
        print(f"\n  Metric blind spots ({len(verdict.metric_blind_spots)}):")
        for bs in verdict.metric_blind_spots:
            print(f"    - {bs}")

    if verdict.legal_violations:
        print(f"\n  Legal violations ({len(verdict.legal_violations)}):")
        for v in verdict.legal_violations:
            print(f"    - {v}")

    print(f"\n  Reports saved to:")
    print(f"    {html_path}")
    print(f"    {json_path}\n")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run behavior judgment on a simulation scenario.")
    parser.add_argument("scenario_dir", type=Path, help="Path to scenario directory")
    parser.add_argument("--output", type=Path, default=Path("reports"), help="Output directory for reports")
    args = parser.parse_args()
    run(args.scenario_dir, args.output)
