# behavior-judge

> *"We measure AV safety with metrics designed to be measurable, not metrics designed to be meaningful. This tool asks: what would a domain expert say about this behavior — and where does that diverge from what our metrics say?"*

**behavior-judge** is an LLM-as-Oracle evaluation framework for autonomous vehicle simulation. It replaces hard-coded pass/fail metric thresholds with reasoned judgment from a multimodal LLM — and crucially, surfaces the cases where the two disagree.

---

## The Problem

Current AV evaluation pipelines rely on threshold-based metrics:

| Metric | Threshold |
|--------|-----------|
| Collision detected | `False` |
| Max jerk | `< 5 m/s³` |
| Goal reached | `True` |

These metrics are **necessary but insufficient**. A vehicle can pass every threshold while:
- Failing to yield at a crosswalk
- Taking a lane that's prohibited by local ordinance
- Making a decision that would terrify any human passenger

Conversely, a vehicle can *fail* a metric while making the correct judgment call in an ambiguous, adversarial situation.

This gap — the **metric blind spot** — is what behavior-judge is designed to find.

---

## Architecture

```
Scenario Directory
    ├── metadata.json      # location, scenario_type, description
    ├── telemetry.csv      # speed, acceleration, jerk, heading per timestep
    └── frames/            # PNG/JPG simulation frames
          └── *.png

           │
           ▼
┌─────────────────────┐
│   Replay Loader     │  Parses metadata, telemetry, frames
└────────┬────────────┘
         │
         ├──────────────────────────────────────┐
         ▼                                      ▼
┌─────────────────────┐              ┌──────────────────────────┐
│  Law Researcher     │              │   Behavior Analyzer      │
│                     │              │                          │
│  1. Geo → Juris.    │              │  Samples frames evenly   │
│  2. Web search laws │              │  Sends to Claude Vision  │
│  3. Cache result    │              │  Returns behavior desc.  │
└────────┬────────────┘              └──────────────┬───────────┘
         │                                          │
         └──────────────┬───────────────────────────┘
                        ▼
           ┌────────────────────────┐
           │   Judgment Engine      │
           │                        │
           │  Combines:             │
           │  - Behavior desc.      │
           │  - Jurisdiction laws   │
           │  - Existing metrics    │
           │                        │
           │  Outputs:              │
           │  - 6 behavior scores   │
           │  - Legal violations    │
           │  - Metric blind spots  │ ← most valuable
           │  - Recommendations     │
           └───────────┬────────────┘
                       ▼
           ┌───────────────────────┐
           │   Report Generator    │
           │   HTML + JSON         │
           └───────────────────────┘
```

---

## Legality Scoring

The **legality score** is what makes this tool unique among AV evaluation systems.

For each scenario, the system:
1. Resolves the simulation location to a jurisdiction (city/state/country)
2. Uses Claude with web search to research the specific traffic laws governing that scenario type in that jurisdiction
3. Caches results by jurisdiction to avoid redundant lookups
4. Passes the full legal context to the judgment engine
5. Outputs a 0–10 legality score with specific statute citations for any violations

This means a vehicle running a scenario in **San Jose, CA** is evaluated against California Vehicle Code, while the same scenario in **Austin, TX** is evaluated against Texas Transportation Code — automatically.

---

## Metric Blind Spots

The most actionable output of behavior-judge is the **metric blind spot report**.

```
Metric blind spots (2):
  - Metrics PASSED but vehicle failed to yield to pedestrian in crosswalk
    (CA VC 21950 — Pedestrian right-of-way). Traditional eval had no
    pedestrian-yield metric.
  - Metrics FAILED (collision=True) but contact was unavoidable given
    sudden lane intrusion by adjacent vehicle. Blaming AV is incorrect.
```

These divergences reveal:
- **FALSE_PASS**: Metrics say OK, LLM says bad — dangerous coverage gap
- **FALSE_FAIL**: Metrics say bad, LLM says OK — overly strict, masking real failures

---

## Quickstart

**No API key required.** behavior-judge runs entirely on local models via [Ollama](https://ollama.com).

```bash
# 1. Install Ollama (https://ollama.com/download)

# 2. Pull the required models
ollama pull llama3.2-vision   # VLM for frame analysis
ollama pull llama3.1          # LLM for judgment engine

# 3. Install behavior-judge
pip install -e ".[dev]"

# 4. Run on the sample scenario
python examples/run_example.py scenarios/sample --output reports/

# 5. Open the report
open reports/highway-merge-001.html   # macOS
# start reports/highway-merge-001.html  # Windows
```

### Optional: swap models via environment variables

```bash
# Use a lighter model if you're low on VRAM
BJ_VISION_MODEL=llava BJ_JUDGE_MODEL=mistral python examples/run_example.py scenarios/sample
```

| Variable | Default | Purpose |
|----------|---------|---------|
| `BJ_VISION_MODEL` | `llama3.2-vision` | Frame analysis (must support images) |
| `BJ_JUDGE_MODEL` | `llama3.1` | Judgment engine |

---

## Scenario Format

```
scenarios/my_scenario/
├── metadata.json
├── telemetry.csv
└── frames/
    ├── 0001.png
    ├── 0002.png
    └── ...
```

**metadata.json**
```json
{
  "scenario_id": "highway-merge-001",
  "location": {
    "lat": 37.3382,
    "lon": -121.8863,
    "city": "San Jose",
    "state": "California",
    "country": "United States"
  },
  "scenario_type": "highway_merge",
  "description": "Ego vehicle merges onto I-880 northbound during moderate traffic."
}
```

**telemetry.csv**
```
timestamp_ms,speed_mps,acceleration_mps2,jerk_mps3,heading_deg,lat,lon
0,18.2,0.0,0.0,45.0,37.3380,-121.8865
...
```

---

## Output

Each run produces:
- `reports/<scenario_id>.html` — visual report with scores, blind spots, law citations
- `reports/<scenario_id>.json` — machine-readable full verdict

---

## Running Tests

```bash
pytest
```

Tests cover: jurisdiction resolution, law caching, metric agreement logic, and divergence detection — all without hitting the API.

---

## Why This Matters

AV evaluation is the last safety layer before real-world deployment. If your evaluation methodology has blind spots, those blind spots ship to production. behavior-judge doesn't replace metric-based evaluation — it audits it.
