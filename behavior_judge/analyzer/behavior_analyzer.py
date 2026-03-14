from __future__ import annotations

import os
from pathlib import Path

import ollama

from behavior_judge.models import TelemetryPoint

VISION_MODEL = os.getenv("BJ_VISION_MODEL", "llama3.2-vision")


def _sample_frames(frames: list[Path], max_frames: int = 8) -> list[Path]:
    if len(frames) <= max_frames:
        return frames
    step = len(frames) // max_frames
    return frames[::step][:max_frames]


def _telemetry_summary(telemetry: list[TelemetryPoint]) -> str:
    if not telemetry:
        return "No telemetry available."
    avg_speed = sum(t.speed_mps for t in telemetry) / len(telemetry)
    max_jerk = max(abs(t.jerk_mps3) for t in telemetry)
    max_accel = max(abs(t.acceleration_mps2) for t in telemetry)
    duration = (telemetry[-1].timestamp_ms - telemetry[0].timestamp_ms) / 1000.0
    return (
        f"Duration: {duration:.1f}s | "
        f"Avg speed: {avg_speed:.1f} m/s | "
        f"Max jerk: {max_jerk:.3f} m/s³ | "
        f"Max acceleration: {max_accel:.3f} m/s²"
    )


def analyze_behavior(
    frames: list[Path],
    telemetry: list[TelemetryPoint],
    scenario_type: str,
    scenario_description: str,
) -> str:
    sampled = _sample_frames(frames)

    prompt = (
        f"You are an expert autonomous vehicle behavior analyst.\n\n"
        f"Scenario type: {scenario_type}\n"
        f"Description: {scenario_description}\n"
        f"Telemetry: {_telemetry_summary(telemetry)}\n\n"
        f"Analyze the provided simulation frames. Describe:\n"
        f"1. The driving maneuver being performed\n"
        f"2. How the vehicle responds to other road users and conditions\n"
        f"3. Any behaviors that seem unsafe, uncomfortable, or socially inappropriate\n"
        f"4. What a cautious, experienced human driver would have done differently\n\n"
        f"Be specific and technical."
    )

    if sampled:
        response = ollama.chat(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [str(f) for f in sampled],
                }
            ],
        )
    else:
        # No frames — analyze from telemetry + description alone
        response = ollama.chat(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nNote: No visual frames available. Base analysis on telemetry and description only.",
                }
            ],
        )

    return response["message"]["content"]
