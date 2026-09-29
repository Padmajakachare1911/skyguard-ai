"""
inference/adapters.py — adapt CV §2.2 violation events to Rachna's backend schema.

Rachna POST /violations expects ViolationCreate:
  type, confidence, latitude, longitude, timestamp, image_url
(id is server-generated int; uuid4 id from CV is dropped on POST)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def to_backend_payload(event: dict[str, Any]) -> dict[str, Any]:
    """Map a CV JSONL event to Rachna's ViolationCreate shape."""
    lat = event.get("latitude", event.get("lat", 0.0))
    lon = event.get("longitude", event.get("lon", 0.0))
    ts = event.get("timestamp", "")
    if isinstance(ts, str) and ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return {
        "type": event["type"],
        "confidence": float(event["confidence"]),
        "latitude": float(lat),
        "longitude": float(lon),
        "timestamp": ts,
        "image_url": event.get("image_url", ""),
    }


def validate_cv_event(event: dict[str, Any]) -> list[str]:
    """Return list of schema violations (empty = valid)."""
    errors: list[str] = []
    required = ("id", "type", "confidence", "lat", "lon", "timestamp", "image_url")
    for key in required:
        if key not in event:
            errors.append(f"missing field: {key}")
    allowed_types = {
        "no-helmet", "no-vest", "restricted-zone-entry",
        "machinery-proximity", "person-down",
    }
    if event.get("type") not in allowed_types:
        errors.append(f"invalid type: {event.get('type')}")
    try:
        float(event.get("confidence", -1))
    except (TypeError, ValueError):
        errors.append("confidence must be numeric")
    return errors
