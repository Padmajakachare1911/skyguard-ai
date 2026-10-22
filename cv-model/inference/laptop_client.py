"""
Pi -> laptop link: upload a violation snapshot, then POST its metadata.

Flow per violation (runs on a background thread, never blocks inference):
  1. frame saved locally as JPEG (reports/pi_snapshots/<type>_<timestamp>.jpg)
  2. POST {backend}/violations/upload-snapshot (multipart "file") -> {"image_url": "<filename>"}
  3. event["image_url"] = <filename> (bare name; dashboard builds {backend}/snapshots/<image_url>)
  4. POST {backend}/violations with inference.adapters.to_backend_payload(event)

Failed deliveries stay in an in-memory queue and are retried later.
Never raises on network failure.
"""

from __future__ import annotations

import os
import queue
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import cv2

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore

from inference.adapters import to_backend_payload

LAPTOP_URL = os.environ.get("SKYGUARD_BACKEND", "http://<laptop-ip>:8000")
SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "reports" / "pi_snapshots"
RETRY_INTERVAL_S = 10.0


def check_backend(backend_url: str, timeout: float = 5.0) -> bool:
    """GET {backend}/ once; print a clear error if the laptop is unreachable."""
    try:
        requests.get(backend_url.rstrip("/") + "/", timeout=timeout).raise_for_status()
        print(f"[laptop_client] backend reachable: {backend_url}")
        return True
    except Exception as exc:
        print(
            f"[laptop_client] ERROR: cannot reach {backend_url} ({exc}). Check that the Pi and "
            "laptop are on the same Wi-Fi, the backend is running, and Windows Firewall allows "
            "inbound TCP 8000."
        )
        return False


class LaptopClient:
    def __init__(self, cooldown_s: float = 5.0, timeout: float = 5.0, retries: int = 3,
                 backoff_s: float = 0.5, snapshot_dir: Path = SNAPSHOT_DIR):
        self.cooldown_s = cooldown_s
        self.timeout = timeout
        self.retries = retries
        self.backoff_s = backoff_s
        self.snapshot_dir = Path(snapshot_dir)
        self._last_sent: dict[str, float] = {}
        self._jobs: queue.Queue = queue.Queue()
        self._pending: deque = deque()  # failed jobs awaiting retry
        self._last_retry = 0.0
        threading.Thread(target=self._worker, daemon=True).start()

    def send(self, frame, event: dict, backend_url: str) -> bool:
        """Queue one violation. Returns False if suppressed by the per-type cooldown."""
        now = time.monotonic()
        vtype = event["type"]
        last = self._last_sent.get(vtype)
        if last is not None and now - last < self.cooldown_s:
            return False
        self._last_sent[vtype] = now
        try:
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
            path = self.snapshot_dir / f"{vtype}_{stamp}.jpg"
            cv2.imwrite(str(path), frame)
        except Exception as exc:
            print(f"[laptop_client] could not save snapshot: {exc}")
            return False
        self._jobs.put({"path": path, "event": event, "backend": backend_url.rstrip("/"),
                        "uploaded": None})
        return True

    def flush(self, timeout: float = 30.0) -> bool:
        """Block until the job queue is drained (used by tests / shutdown)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._jobs.unfinished_tasks == 0:
                return True
            time.sleep(0.02)
        return False

    @property
    def pending(self) -> int:
        return len(self._pending)

    def _worker(self) -> None:
        while True:
            try:
                job = self._jobs.get(timeout=1.0)
            except queue.Empty:
                job = None
            try:
                if job is not None and not self._deliver(job):
                    self._pending.append(job)
                if self._pending and time.monotonic() - self._last_retry >= RETRY_INTERVAL_S:
                    self._last_retry = time.monotonic()
                    for _ in range(len(self._pending)):
                        j = self._pending.popleft()
                        if not self._deliver(j):
                            self._pending.append(j)
            except Exception as exc:  # never let the worker die
                print(f"[laptop_client] unexpected error: {exc}")
            finally:
                if job is not None:
                    self._jobs.task_done()

    def _deliver(self, job: dict) -> bool:
        if requests is None:
            return False
        backend, event = job["backend"], job["event"]
        for attempt in range(self.retries):
            try:
                if job["uploaded"] is None:
                    with open(job["path"], "rb") as fh:
                        r = requests.post(
                            f"{backend}/violations/upload-snapshot",
                            files={"file": (job["path"].name, fh, "image/jpeg")},
                            timeout=self.timeout,
                        )
                    if r.status_code in (200, 201):
                        job["uploaded"] = r.json()["image_url"]
                if job["uploaded"] is not None:
                    event["image_url"] = os.path.basename(job["uploaded"])
                    r = requests.post(f"{backend}/violations", json=to_backend_payload(event),
                                      timeout=self.timeout)
                    if r.status_code in (200, 201):
                        return True
            except Exception:
                pass
            time.sleep(self.backoff_s * (attempt + 1))
        return False


_default: LaptopClient | None = None


def send_violation(frame, event: dict, backend_url: str | None = None,
                   cooldown_s: float = 5.0) -> bool:
    """Module-level convenience used by infer_pi. Never raises."""
    global _default
    try:
        if _default is None:
            _default = LaptopClient(cooldown_s=cooldown_s)
        return _default.send(frame, event, backend_url or LAPTOP_URL)
    except Exception as exc:
        print(f"[laptop_client] send failed: {exc}")
        return False
