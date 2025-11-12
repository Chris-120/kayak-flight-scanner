from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

def write_json(records: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def _flatten(itin: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten a normalized itinerary into a one-row CSV-friendly dict.
    We keep core fields and summarize others.
    """
    display = itin.get("displayAirline") or {}
    provider = itin.get("providerInfo") or {}
    legs = itin.get("legs") or []
    segments_count = sum(len(l.get("segments", [])) for l in legs)

    # Try to pick a human-readable duration from first leg
    leg_duration = None
    if legs:
        leg_duration = legs[0].get("legDurationDisplay")

    return {
        "origin": itin.get("origin"),
        "destination": itin.get("destination"),
        "cabinCode": itin.get("cabinCode"),
        "displayAirlineCode": display.get("code"),
        "displayAirlineName": display.get("name"),
        "minDisplayPrice": itin.get("minDisplayPrice"),
        "providerName": provider.get("name"),
        "providerCurrency": provider.get("currency"),
        "legs": len(legs),
        "segments": segments_count,
        "firstLegDuration": leg_duration,
        "co2EstimatedKg": (itin.get("co2Info") or {}).get("estimatedKgCO2"),
    }

def write_csv(records: Iterable[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [_flatten(r) for r in records]
    if not rows:
        # Create an empty file with header only
        header = [
            "origin",
            "destination",
            "cabinCode",
            "displayAirlineCode",
            "displayAirlineName",
            "minDisplayPrice",
            "providerName",
            "providerCurrency",
            "legs",
            "segments",
            "firstLegDuration",
            "co2EstimatedKg",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
        return

    header = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)