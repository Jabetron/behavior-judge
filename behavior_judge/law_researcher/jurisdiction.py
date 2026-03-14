from __future__ import annotations

from behavior_judge.models import Location


def resolve_jurisdiction(location: Location) -> str:
    """Convert a Location to a human-readable jurisdiction string."""
    if location.city and location.state and location.country:
        return f"{location.city}, {location.state}, {location.country}"

    try:
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut

        geolocator = Nominatim(user_agent="behavior-judge")
        result = geolocator.reverse(f"{location.lat}, {location.lon}", language="en")
        if result:
            addr = result.raw.get("address", {})
            parts = [
                addr.get("city") or addr.get("town") or addr.get("village"),
                addr.get("state"),
                addr.get("country"),
            ]
            return ", ".join(p for p in parts if p)
    except Exception:
        pass

    return f"{location.lat:.4f}, {location.lon:.4f}"
