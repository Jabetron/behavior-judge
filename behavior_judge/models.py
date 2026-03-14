from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Location(BaseModel):
    lat: float
    lon: float
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class ScenarioMetadata(BaseModel):
    scenario_id: str
    location: Location
    scenario_type: str  # e.g. "highway_merge", "intersection", "lane_change"
    description: str
    timestamp: Optional[datetime] = None


class TelemetryPoint(BaseModel):
    timestamp_ms: int
    speed_mps: float
    acceleration_mps2: float
    jerk_mps3: float
    heading_deg: float
    lat: float
    lon: float


class ExistingMetrics(BaseModel):
    collision: bool
    max_jerk: float
    max_acceleration: float
    goal_reached: bool
    time_to_complete_s: Optional[float] = None


class RelevantLaw(BaseModel):
    description: str
    source: str
    applies_to: str


class LegalityResearch(BaseModel):
    jurisdiction: str
    relevant_laws: list[RelevantLaw]
    research_summary: str


class BehaviorScores(BaseModel):
    safety_margin: float = Field(..., ge=0, le=10)
    comfort: float = Field(..., ge=0, le=10)
    social_compliance: float = Field(..., ge=0, le=10)
    legality: float = Field(..., ge=0, le=10)
    decision_quality: float = Field(..., ge=0, le=10)
    overall: float = Field(..., ge=0, le=10)


class JudgmentVerdict(BaseModel):
    scores: BehaviorScores
    behavior_description: str
    reasoning: str
    legal_violations: list[str]
    metric_blind_spots: list[str]
    recommendations: str
    confidence: float = Field(..., ge=0, le=1)


class ScenarioReport(BaseModel):
    scenario_id: str
    metadata: ScenarioMetadata
    legality_research: LegalityResearch
    existing_metrics: ExistingMetrics
    verdict: JudgmentVerdict
    generated_at: datetime
