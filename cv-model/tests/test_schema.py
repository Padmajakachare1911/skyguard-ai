"""Validate violation event schema (#23)."""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inference.adapters import validate_cv_event, to_backend_payload
from inference.infer_video import make_violation_event


def test_make_violation_event_schema():
    ev = make_violation_event("no-helmet", 0.87, "reports/test.jpg", 19.033, 73.0297)
    assert validate_cv_event(ev) == []
    assert ev["type"] == "no-helmet"
    assert ev["lat"] == 19.033
    uuid.UUID(ev["id"])


def test_backend_adapter():
    ev = make_violation_event("no-vest", 0.75, "snap.jpg")
    payload = to_backend_payload(ev)
    assert "latitude" in payload
    assert "longitude" in payload
    assert "id" not in payload


def test_jsonl_roundtrip(tmp_path):
    ev = make_violation_event("person-down", 0.9, "x.jpg")
    p = tmp_path / "events.jsonl"
    p.write_text(json.dumps(ev) + "\n")
    loaded = json.loads(p.read_text().strip())
    assert validate_cv_event(loaded) == []
