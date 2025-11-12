from __future__ import annotations

from typing import Any, Dict, List, Optional

from .airline_info import enrich_airline, parse_airline_from_segment
from .co2_metrics import estimate_co2_for_legs

def _min_price_from_options(options_by_fare: List[Dict[str, Any]]) -> Optional[float]:
    """
    Accepts a list like:
      [{"fareName":"Economy","displayPrice":"$236","provider":"Trip.com"}]
    Returns a numeric minimal price if possible.
    """
    best = None
    for opt in options_by_fare or []:
        price_raw = opt.get("displayPrice") or opt.get("price") or ""
        # Extract digits/decimal
        digits = "".join(ch if (ch.isdigit() or ch == "." or ch == ",") else "" for ch in str(price_raw))
        digits = digits.replace(",", "")
        try:
            val = float(digits)
            if best is None or val < best:
                best = val
        except ValueError:
            continue
    return best

def _normalize_leg(leg: Dict[str, Any]) -> Dict[str, Any]:
    segs = leg.get("segments") or []
    normalized_segments = []
    for seg in segs:
        airline_name = seg.get("airline") or parse_airline_from_segment(seg)
        dep = seg.get("departure") or seg.get("from") or seg.get("origin")
        arr = seg.get("arrival") or seg.get("to") or seg.get("destination")
        normalized_segments.append(
            {
                "airline": airline_name,
                "departure": dep,
                "arrival": arr,
                "duration": seg.get("duration") or seg.get("durationDisplay"),
                "flightNumber": seg.get("flightNumber"),
                "aircraft": seg.get("aircraft"),
            }
        )
    return {
        "legDurationDisplay": leg.get("legDurationDisplay") or leg.get("duration") or leg.get("durationDisplay"),
        "overnight": leg.get("overnight", False),
        "segments": normalized_segments,
    }

def _collect_distinct_airlines(legs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = {}
    for leg in legs:
        for seg in leg.get("segments", []):
            name = seg.get("airline")
            if not name:
                continue
            key = name.strip().lower()
            if key not in seen:
                # We don't have IATA code here reliably, keep only name and allow enrichment at top level if provided
                seen[key] = {"name": name}
    return list(seen.values())

def normalize_flights(raw_payload: Any, defaults: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Accepts either:
      - List of itineraries (as in README Example Output)
      - Dict with a key containing a list (e.g., {"results":[...]})
    Returns a list of normalized itineraries with consistent keys and lightweight enrichment.
    """
    defaults = defaults or {}
    itineraries: List[Dict[str, Any]] = []
    data = raw_payload

    if isinstance(data, dict):
        # try to discover a list-like container
        for key in ("results", "data", "items", "itineraries", "flights"):
            if isinstance(data.get(key), list):
                data = data[key]
                break

    if not isinstance(data, list):
        # Nothing we can do: return empty standardized list
        return []

    for item in data:
        cabin = (item.get("cabinCode") or item.get("cabin") or "").lower()[:1] or "e"

        # Display airline
        disp = item.get("displayAirline") or {}
        code = disp.get("code")
        name = disp.get("name") or "Multiple Airlines"
        display_airline = enrich_airline(code=code, name=name)

        # Legs
        raw_legs = item.get("legs") or []
        legs = [_normalize_leg(leg) for leg in raw_legs]

        # Distinct airlines
        distinct = item.get("distinctAirlines") or _collect_distinct_airlines(legs)
        # If any have a "code" enrich them; else leave names
        enriched_distinct = []
        for a in distinct:
            enriched_distinct.append(enrich_airline(code=a.get("code"), name=a.get("name")))

        # Fare options / provider info
        options = item.get("optionsByFare") or []
        min_price = _min_price_from_options(options)

        provider = item.get("providerInfo") or {}
        provider_info = {
            "name": provider.get("name") or (options[0].get("provider") if options else None),
            "logo": provider.get("logo"),
            "currency": provider.get("currency") or None,
        }

        # CO2 estimation if missing
        co2 = item.get("co2Info") or estimate_co2_for_legs(legs)

        normalized = {
            "cabinCode": cabin,
            "displayAirline": display_airline,
            "distinctAirlines": enriched_distinct,
            "legs": legs,
            "optionsByFare": options,
            "minDisplayPrice": min_price,
            "providerInfo": provider_info,
            "co2Info": co2,
            "origin": item.get("origin") or defaults.get("origin"),
            "destination": item.get("destination") or defaults.get("destination"),
            "operationalDisclosures": item.get("operationalDisclosures") or [],
        }
        itineraries.append(normalized)

    return itineraries