from __future__ import annotations

import json
from pathlib import Path

from behavior_judge.models import ScenarioReport
from behavior_judge.scoring.scorer import compute_metric_agreement


def generate_json_report(report: ScenarioReport, output_path: Path) -> None:
    output_path.write_text(report.model_dump_json(indent=2))


def generate_html_report(report: ScenarioReport, output_path: Path) -> None:
    agreement = compute_metric_agreement(report.verdict, report.existing_metrics)
    s = report.verdict.scores

    def score_color(v: float) -> str:
        if v >= 8:
            return "#2a9d8f"
        if v >= 6:
            return "#e9c46a"
        return "#e63946"

    def li_items(items: list[str], css_class: str = "") -> str:
        if not items:
            return "<li>None detected</li>"
        return "".join(f'<li class="{css_class}">{item}</li>' for item in items)

    divergence_badge = (
        f'<span class="badge badge-{agreement["divergence_type"].lower().replace("_", "-")}">'
        f'{agreement["divergence_type"].replace("_", " ")}</span>'
        if agreement["divergence_detected"]
        else '<span class="badge badge-ok">METRICS AGREE</span>'
    )

    laws_html = "".join(
        f"<li><strong>{law.applies_to}:</strong> {law.description} "
        f"<em class='source'>({law.source})</em></li>"
        for law in report.legality_research.relevant_laws
    ) or "<li>No specific laws researched.</li>"

    score_cards = "".join(
        f"""<div class="score-card">
          <div class="value" style="color:{score_color(val)}">{val:.1f}</div>
          <div class="label">{label}</div>
        </div>"""
        for label, val in [
            ("Safety Margin", s.safety_margin),
            ("Comfort", s.comfort),
            ("Social Compliance", s.social_compliance),
            ("Legality", s.legality),
            ("Decision Quality", s.decision_quality),
            ("Overall", s.overall),
        ]
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Behavior Judgment — {report.scenario_id}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 24px; color: #1a1a2e; background: #f8f9fa; }}
    h1 {{ border-bottom: 3px solid #e63946; padding-bottom: 12px; margin-bottom: 8px; }}
    h2 {{ color: #457b9d; margin: 32px 0 12px; }}
    h3 {{ color: #333; margin: 20px 0 8px; }}
    .meta {{ background: #edf2f4; padding: 14px 18px; border-radius: 8px; margin-bottom: 24px; font-size: 0.9em; }}
    .section {{ background: #fff; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px 24px; margin: 12px 0; }}
    .scores {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 16px 0; }}
    .score-card {{ background: #fff; border: 1px solid #dee2e6; border-radius: 8px; padding: 16px; text-align: center; }}
    .score-card .value {{ font-size: 2.2em; font-weight: 700; }}
    .score-card .label {{ font-size: 0.78em; color: #666; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }}
    .badge {{ display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.8em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }}
    .badge-ok {{ background: #2a9d8f; color: #fff; }}
    .badge-false-pass {{ background: #e63946; color: #fff; }}
    .badge-false-fail {{ background: #ffb703; color: #000; }}
    .blind-spot {{ color: #c1121f; margin: 8px 0; padding-left: 4px; border-left: 3px solid #e63946; }}
    .violation {{ color: #c1121f; margin: 6px 0; }}
    .reasoning {{ background: #f1faee; padding: 16px 20px; border-left: 4px solid #457b9d; border-radius: 4px; line-height: 1.7; white-space: pre-wrap; }}
    .source {{ color: #888; font-size: 0.85em; }}
    .stat-row {{ display: flex; gap: 32px; flex-wrap: wrap; font-size: 0.9em; }}
    .stat {{ display: flex; flex-direction: column; }}
    .stat .key {{ color: #888; font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.05em; }}
    .stat .val {{ font-weight: 600; font-size: 1.05em; margin-top: 2px; }}
    footer {{ text-align: center; color: #aaa; margin: 40px 0 20px; font-size: 0.8em; }}
  </style>
</head>
<body>
  <h1>Behavior Judgment Report</h1>

  <div class="meta">
    <strong>{report.scenario_id}</strong> &nbsp;·&nbsp;
    {report.metadata.scenario_type} &nbsp;·&nbsp;
    {report.legality_research.jurisdiction} &nbsp;·&nbsp;
    {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}
  </div>

  <h2>Metric Agreement &nbsp; {divergence_badge}</h2>
  <div class="section">
    <div class="stat-row">
      <div class="stat"><span class="key">Traditional Verdict</span><span class="val">{agreement['metric_verdict']}</span></div>
      <div class="stat"><span class="key">LLM Verdict</span><span class="val">{agreement['llm_verdict']}</span></div>
      <div class="stat"><span class="key">Blind Spots</span><span class="val">{agreement['blind_spot_count']}</span></div>
      <div class="stat"><span class="key">Legal Violations</span><span class="val">{agreement['legal_violation_count']}</span></div>
      <div class="stat"><span class="key">Confidence</span><span class="val">{report.verdict.confidence:.0%}</span></div>
    </div>
  </div>

  <h2>Behavior Scores</h2>
  <div class="scores">{score_cards}</div>

  <h2>Metric Blind Spots</h2>
  <div class="section">
    <p style="color:#666;font-size:0.9em;margin-top:0">
      Cases where metric verdicts diverge from judgment — the most actionable output.
    </p>
    <ul>{li_items(report.verdict.metric_blind_spots, "blind-spot")}</ul>
  </div>

  <h2>Legal Violations</h2>
  <div class="section">
    <ul>{li_items(report.verdict.legal_violations, "violation")}</ul>
    <h3>Researched Laws — {report.legality_research.jurisdiction}</h3>
    <p style="color:#666;font-size:0.9em">{report.legality_research.research_summary}</p>
    <ul>{laws_html}</ul>
  </div>

  <h2>Reasoning</h2>
  <div class="section">
    <div class="reasoning">{report.verdict.reasoning}</div>
  </div>

  <h2>Recommendations</h2>
  <div class="section">
    <p style="line-height:1.7">{report.verdict.recommendations}</p>
  </div>

  <h2>Traditional Metrics</h2>
  <div class="section">
    <div class="stat-row">
      <div class="stat"><span class="key">Collision</span><span class="val">{report.existing_metrics.collision}</span></div>
      <div class="stat"><span class="key">Goal Reached</span><span class="val">{report.existing_metrics.goal_reached}</span></div>
      <div class="stat"><span class="key">Max Jerk</span><span class="val">{report.existing_metrics.max_jerk:.3f} m/s³</span></div>
      <div class="stat"><span class="key">Max Accel</span><span class="val">{report.existing_metrics.max_acceleration:.3f} m/s²</span></div>
      <div class="stat"><span class="key">Duration</span><span class="val">{report.existing_metrics.time_to_complete_s}s</span></div>
    </div>
  </div>

  <footer>behavior-judge &nbsp;·&nbsp; powered by Claude &nbsp;·&nbsp; {report.generated_at.strftime('%Y-%m-%d')}</footer>
</body>
</html>"""

    output_path.write_text(html)
