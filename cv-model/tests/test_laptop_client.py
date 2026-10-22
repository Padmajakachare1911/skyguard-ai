"""Tests for inference.laptop_client against a stdlib mock backend."""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inference.infer_video import make_violation_event
from inference.laptop_client import LaptopClient

_calls: list[tuple[str, object]] = []


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        if self.path == "/violations/upload-snapshot":
            _calls.append(("upload", body))
            out = {"image_url": "20260101_000000_snap.jpg"}
        elif self.path == "/violations":
            _calls.append(("violation", json.loads(body)))
            out = {"id": 1}
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(out).encode())

    def log_message(self, *_):
        pass


def _server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def _client(tmp_path, **kw):
    return LaptopClient(snapshot_dir=tmp_path, backoff_s=0.0, timeout=2.0, **kw)


FRAME = np.zeros((48, 64, 3), dtype=np.uint8)


def test_upload_before_violation_and_bare_filename(tmp_path):
    _calls.clear()
    server, url = _server()
    client = _client(tmp_path)
    ev = make_violation_event("no-helmet", 0.9, "pi/frame_1.jpg", 19.0, 73.0)
    assert client.send(FRAME, ev, url)
    assert client.flush()
    server.shutdown()

    assert [c[0] for c in _calls] == ["upload", "violation"]
    payload = _calls[1][1]
    assert payload["image_url"] == "20260101_000000_snap.jpg"
    assert "/" not in payload["image_url"]
    assert ev["image_url"] == "20260101_000000_snap.jpg"
    assert len(list(tmp_path.glob("no-helmet_*.jpg"))) == 1


def test_cooldown_suppresses_duplicates(tmp_path):
    _calls.clear()
    server, url = _server()
    client = _client(tmp_path, cooldown_s=60.0)
    e1 = make_violation_event("no-vest", 0.8, "x.jpg")
    e2 = make_violation_event("no-vest", 0.8, "x.jpg")
    e3 = make_violation_event("no-helmet", 0.8, "x.jpg")
    assert client.send(FRAME, e1, url) is True
    assert client.send(FRAME, e2, url) is False
    assert client.send(FRAME, e3, url) is True  # different type is independent
    assert client.flush()
    server.shutdown()
    assert [c[0] for c in _calls].count("violation") == 2


def test_unreachable_backend_does_not_raise(tmp_path):
    client = _client(tmp_path, retries=1)
    ev = make_violation_event("no-helmet", 0.9, "x.jpg")
    assert client.send(FRAME, ev, "http://127.0.0.1:1") is True  # accepted, queued
    assert client.flush()
    assert client.pending == 1
