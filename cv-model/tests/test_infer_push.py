"""Test POST /violations push path against mock stdlib server (#23)."""

import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inference.adapters import to_backend_payload
from inference.infer_video import make_violation_event, post_violation

_received: list[dict] = []


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/violations":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        _received.append(body)
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"id": len(_received), **body}).encode())

    def log_message(self, *_):
        pass


def test_post_violation_mock_backend():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    url = f"http://127.0.0.1:{port}/violations"
    event = make_violation_event("no-helmet", 0.9, "reports/x.jpg", 19.0, 73.0)
    assert post_violation(url, event, timeout=2.0, retries=2) is True
    assert len(_received) == 1
    assert _received[0]["type"] == "no-helmet"
    assert "latitude" in _received[0]

    server.shutdown()
