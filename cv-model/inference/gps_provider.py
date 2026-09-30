"""
GPS providers for Pi / MAVLink integration (#61).

StubGps: fixed coordinates for bench tests.
MavlinkGps: nearest fix from pymavlink GLOBAL_POSITION_INT stream.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class GpsFix:
    lat: float
    lon: float
    timestamp: datetime


class GpsProvider(ABC):
    @abstractmethod
    def get_fix(self, timestamp: datetime | None = None) -> GpsFix:
        ...


class StubGps(GpsProvider):
    """Hardcoded site coordinates for simulated integration tests."""

    def __init__(self, lat: float = 19.0330, lon: float = 73.0297):
        self._lat = lat
        self._lon = lon

    def get_fix(self, timestamp: datetime | None = None) -> GpsFix:
        ts = timestamp or datetime.now(timezone.utc)
        return GpsFix(self._lat, self._lon, ts)


class MavlinkGps(GpsProvider):
    """
    Poll MAVLink for GPS fixes; returns nearest fix to requested timestamp.
    Connection string via SKYGUARD_MAVLINK (default udpin:0.0.0.0:14561).
    """

    def __init__(self, connection: str | None = None):
        self.connection = connection or os.environ.get(
            "SKYGUARD_MAVLINK", "udpin:0.0.0.0:14561"
        )
        self._fixes: list[GpsFix] = []
        self._master = None

    def _connect(self) -> None:
        if self._master is not None:
            return
        from pymavlink import mavutil

        self._master = mavutil.mavlink_connection(self.connection)
        self._master.wait_heartbeat(timeout=10)

    def _poll(self, max_messages: int = 20) -> None:
        self._connect()
        for _ in range(max_messages):
            msg = self._master.recv_match(blocking=False)
            if msg is None:
                break
            if msg.get_type() == "GLOBAL_POSITION_INT":
                ts = datetime.now(timezone.utc)
                self._fixes.append(
                    GpsFix(msg.lat / 1e7, msg.lon / 1e7, ts)
                )

    def get_fix(self, timestamp: datetime | None = None) -> GpsFix:
        self._poll()
        if not self._fixes:
            return GpsFix(0.0, 0.0, timestamp or datetime.now(timezone.utc))
        if timestamp is None:
            return self._fixes[-1]
        return min(
            self._fixes,
            key=lambda f: abs((f.timestamp - timestamp).total_seconds()),
        )
