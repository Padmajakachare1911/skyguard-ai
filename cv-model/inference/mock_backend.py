"""
Tiny local FastAPI server to test POST /violations push path (#23 fallback).

Usage:
    python -m inference.mock_backend --port 8765

Then:
    python -m inference.infer_video ... --post-url http://127.0.0.1:8765/violations
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    FastAPI = None  # type: ignore

from inference.adapters import validate_cv_event, to_backend_payload

_received: list[dict[str, Any]] = []


if FastAPI is not None:

    class ViolationCreate(BaseModel):
        type: str
        confidence: float
        latitude: float
        longitude: float
        timestamp: datetime
        image_url: str

    app = FastAPI(title="SkyGuard Mock Violations API")

    @app.post("/violations")
    def create_violation(v: ViolationCreate):
        payload = v.model_dump()
        _received.append(payload)
        return {"id": len(_received), **payload}

    @app.get("/violations")
    def list_violations():
        return _received


def run_server(port: int = 8765) -> None:
    if FastAPI is None:
        raise RuntimeError("Install fastapi and uvicorn: pip install fastapi uvicorn")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def run_stdlib_server(port: int = 8765) -> None:
    """Fallback HTTP server when FastAPI is not installed."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
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

    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    try:
        run_server(args.port)
    except RuntimeError:
        print("[mock_backend] FastAPI unavailable; using stdlib HTTP server")
        run_stdlib_server(args.port)
