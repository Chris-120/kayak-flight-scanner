from __future__ import annotations

from typing import Dict, List, Any

def _segment_weight(segment: dict) -> float:
    """
    Very rough heuristic for distance/weighting when no distances are available.
    Uses duration if present; defaults to a small constant so we don't divide by zero.
    """
    dur = segment.get("duration")
    if isinstance(dur, (int, float)):
        return float(dur)
    # Try "11h 35m" format
    dstr = str(dur or "")
    hours = 0.0
    minutes = 0.0
    try:
        if "h" in dstr:
            hours = float(dstr.split("h")[0].strip())
            if "m" in dstr:
                minutes = float(dstr.split("h")[1].split("m")[0].strip())
        elif "m" in dstr:
            minutes = float(dstr.split("m")[0].strip())
    except Exception:
        pass
    total_minutes = hours * 60.0 + minutes
    return total_minutes if total_minutes > 0 else 60.0

def estimate_co2_for_legs(legs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Returns a basic CO2 estimate dict for the given legs:
    {
      "estimatedKgCO2": float,           # total estimate
      "averagePerSegmentKg": float,      # average per segment
      "method": "heuristic-duration"
    }
    This is a heuristic intended for demonstration only.
    """
    weights = []
    for leg in legs:
        for seg in leg.get("segments", []):
            weights.append(_segment_weight(seg))

    if not weights:
        return {"estimatedKgCO2": None, "averagePerSegmentKg": None, "method": "none"}

    # Assume linear proportionality to "weight" with a factor (arbitrary, demo only)
    FACTOR = 2.3  # kg CO2 per "minute" proxy
    total = sum(weights) * FACTOR
    avg = total / len(weights)
    return {"estimatedKgCO2": round(total, 2), "averagePerSegmentKg": round(avg, 2), "method": "heuristic-duration"}