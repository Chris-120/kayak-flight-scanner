from __future__ import annotations

from typing import Dict, Optional

# Minimal airline metadata (expand as needed)
# Source-free small sample to enrich visuals; you can add more codes without changing the rest of the app.
_AIRLINES = {
    "GA": {"name": "Garuda Indonesia", "logo": "https://logos.airlines.example/GA.png"},
    "OD": {"name": "Batik Air", "logo": "https://logos.airlines.example/OD.png"},
    "QF": {"name": "Qantas", "logo": "https://logos.airlines.example/QF.png"},
    "BA": {"name": "British Airways", "logo": "https://logos.airlines.example/BA.png"},
    "MULT": {"name": "Multiple Airlines", "logo": "https://logos.airlines.example/MULT.png"},
}

def enrich_airline(code: Optional[str], name: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Given an optional airline IATA code and name, return a dict containing:
      { "code": CODE, "name": NAME, "logo": URL }
    Falls back to provided name if code not found.
    """
    code_norm = (code or "").upper().strip() or None
    if code_norm and code_norm in _AIRLINES:
        base = _AIRLINES[code_norm]
        return {"code": code_norm, "name": base["name"], "logo": base["logo"]}

    # Try reverse lookup by name
    name_norm = (name or "").strip()
    for k, v in _AIRLINES.items():
        if v["name"].lower() == name_norm.lower():
            return {"code": k, "name": v["name"], "logo": v["logo"]}

    # Best-effort fallback
    return {"code": code_norm, "name": name_norm or None, "logo": None}

def parse_airline_from_segment(segment: dict) -> Optional[str]:
    """
    Accepts a segment dict and tries to infer an airline name from potential alt fields.
    """
    for k in ("carrier", "marketingAirline", "operatingAirline"):
        val = segment.get(k)
        if isinstance(val, dict):
            return val.get("name") or val.get("code")
        if isinstance(val, str):
            return val
    return None