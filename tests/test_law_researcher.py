from __future__ import annotations

from unittest.mock import patch

from behavior_judge.law_researcher.jurisdiction import resolve_jurisdiction
from behavior_judge.law_researcher.researcher import (
    list_supported_jurisdictions,
    list_supported_scenario_types,
    research_traffic_laws,
)
from behavior_judge.models import Location


def make_location(**kwargs) -> Location:
    defaults = {"lat": 37.3382, "lon": -121.8863}
    return Location(**{**defaults, **kwargs})


class TestResolveJurisdiction:
    def test_uses_explicit_fields_when_present(self):
        loc = make_location(city="San Jose", state="California", country="United States")
        assert resolve_jurisdiction(loc) == "San Jose, California, United States"

    def test_falls_back_to_coords_when_geocoding_fails(self):
        loc = make_location()
        with patch("geopy.geocoders.Nominatim") as mock_cls:
            mock_cls.return_value.reverse.side_effect = Exception("network error")
            result = resolve_jurisdiction(loc)
        assert "37.3382" in result
        assert "-121.8863" in result


class TestResearchTrafficLaws:
    def test_exact_jurisdiction_match(self):
        loc = make_location(city="San Jose", state="California", country="United States")
        result = research_traffic_laws(loc, "highway_merge")
        assert result.jurisdiction == "San Jose, California, United States"
        assert len(result.relevant_laws) > 0
        sources = [law.source for law in result.relevant_laws]
        assert any("CA VC" in s for s in sources)

    def test_country_level_fallback(self):
        # Austin, TX should fall back to Texas laws
        loc = make_location(city="Austin", state="Texas", country="United States", lat=30.27, lon=-97.74)
        result = research_traffic_laws(loc, "lane_change")
        assert len(result.relevant_laws) > 0

    def test_unknown_jurisdiction_returns_empty(self):
        loc = make_location(city="Unknown City", state="Unknown State", country="Unknown Country")
        result = research_traffic_laws(loc, "highway_merge")
        assert result.relevant_laws == []
        assert "No jurisdiction-specific laws" in result.research_summary

    def test_all_scenario_types_have_laws_for_california(self):
        loc = make_location(city="Los Angeles", state="California", country="United States")
        for scenario_type in ["highway_merge", "lane_change", "intersection", "pedestrian_crosswalk", "school_zone"]:
            result = research_traffic_laws(loc, scenario_type)
            assert len(result.relevant_laws) > 0, f"No laws found for {scenario_type}"

    def test_list_supported_jurisdictions(self):
        jurisdictions = list_supported_jurisdictions()
        assert "California, United States" in jurisdictions
        assert len(jurisdictions) >= 5

    def test_list_supported_scenario_types(self):
        types = list_supported_scenario_types()
        assert "highway_merge" in types
        assert "pedestrian_crosswalk" in types
