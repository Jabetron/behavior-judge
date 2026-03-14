from __future__ import annotations

import json
from pathlib import Path

from behavior_judge.law_researcher.jurisdiction import resolve_jurisdiction
from behavior_judge.models import LegalityResearch, Location, RelevantLaw

_DB_PATH = Path(__file__).parent / "law_db.json"
_LAW_DB: dict = json.loads(_DB_PATH.read_text())

_FALLBACK_SUMMARY = (
    "No jurisdiction-specific laws found in the database for this scenario type. "
    "Evaluate behavior against general safe driving principles."
)


def research_traffic_laws(location: Location, scenario_type: str) -> LegalityResearch:
    """
    Look up applicable traffic laws from the static law database.
    Matches on jurisdiction (country/state level) and scenario type.
    """
    jurisdiction = resolve_jurisdiction(location)

    # Try exact match first, then country-level fallback
    laws_data = (
        _LAW_DB.get(jurisdiction, {}).get(scenario_type)
        or _match_by_country(jurisdiction, scenario_type)
        or []
    )

    laws = [RelevantLaw(**law) for law in laws_data]

    summary = (
        f"{len(laws)} applicable law(s) found in {jurisdiction} for '{scenario_type}' scenarios."
        if laws
        else _FALLBACK_SUMMARY
    )

    return LegalityResearch(
        jurisdiction=jurisdiction,
        relevant_laws=laws,
        research_summary=summary,
    )


def _match_by_country(jurisdiction: str, scenario_type: str) -> list[dict] | None:
    """
    If no exact jurisdiction match, try matching any DB entry whose key is a
    substring of the resolved jurisdiction (e.g. 'United States' matches
    'California, United States').
    """
    for db_key, scenarios in _LAW_DB.items():
        if db_key in jurisdiction or jurisdiction in db_key:
            laws = scenarios.get(scenario_type)
            if laws:
                return laws
    return None


def list_supported_jurisdictions() -> list[str]:
    return list(_LAW_DB.keys())


def list_supported_scenario_types() -> list[str]:
    types: set[str] = set()
    for scenarios in _LAW_DB.values():
        types.update(scenarios.keys())
    return sorted(types)
