from __future__ import annotations

from datetime import datetime

def ensure_iso_date(date_str: str) -> str:
    """
    Accepts a string and returns a normalized YYYY-MM-DD date.
    Raises ValueError if not parseable as YYYY-MM-DD.
    """
    # Strict parse first
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.date().isoformat()
    except ValueError as e:
        raise ValueError(f"Invalid date (expected YYYY-MM-DD): {date_str}") from e