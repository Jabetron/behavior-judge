from __future__ import annotations

import csv
import json
from pathlib import Path

from behavior_judge.models import (
    ExistingMetrics,
    Location,
    ScenarioMetadata,
    TelemetryPoint,
)


def load_metadata(scenario_dir: Path) -> ScenarioMetadata:
    data = json.loads((scenario_dir / "metadata.json").read_text())
    data["location"] = Location(**data["location"])
    return ScenarioMetadata(**data)


def load_telemetry(scenario_dir: Path) -> list[TelemetryPoint]:
    path = scenario_dir / "telemetry.csv"
    if not path.exists():
        return []
    with open(path) as f:
        return [TelemetryPoint(**{k: _cast(k, v) for k, v in row.items()}) for row in csv.DictReader(f)]


def _cast(key: str, value: str) -> float | int:
    if key == "timestamp_ms":
        return int(value)
    return float(value)


def load_frames(scenario_dir: Path) -> list[Path]:
    frames_dir = scenario_dir / "frames"
    if not frames_dir.exists():
        return []
    return sorted(frames_dir.glob("*.png")) + sorted(frames_dir.glob("*.jpg"))


def compute_existing_metrics(
    telemetry: list[TelemetryPoint],
    collision: bool = False,
    goal_reached: bool = True,
) -> ExistingMetrics:
    if not telemetry:
        return ExistingMetrics(
            collision=collision,
            max_jerk=0.0,
            max_acceleration=0.0,
            goal_reached=goal_reached,
        )
    return ExistingMetrics(
        collision=collision,
        max_jerk=max(abs(t.jerk_mps3) for t in telemetry),
        max_acceleration=max(abs(t.acceleration_mps2) for t in telemetry),
        goal_reached=goal_reached,
        time_to_complete_s=(telemetry[-1].timestamp_ms - telemetry[0].timestamp_ms) / 1000.0,
    )
