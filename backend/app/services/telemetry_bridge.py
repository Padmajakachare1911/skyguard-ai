import time
from datetime import datetime, timezone

import requests
from pymavlink import mavutil


MAVLINK_CONNECTION = "udpin:0.0.0.0:14561"
BACKEND_URL = "http://127.0.0.1:8000/telemetry"


print("=" * 60)
print("SKYGUARD AI - MAVLINK TELEMETRY BRIDGE")
print("=" * 60)

print()
print("Connecting to PX4 SITL...")
print(f"MAVLink connection: {MAVLINK_CONNECTION}")

master = mavutil.mavlink_connection(
    MAVLINK_CONNECTION
)

print("Waiting for PX4 heartbeat...")

master.wait_heartbeat()

print()
print("Connected to PX4 SITL!")
print(
    f"Heartbeat received from system "
    f"{master.target_system} "
    f"component {master.target_component}"
)

flight_mode = "UNKNOWN"

print()
print("Sending telemetry to FastAPI...")
print(f"Backend: {BACKEND_URL}")
print()

try:

    while True:

        msg = master.recv_match(
            blocking=True
        )

        if msg is None:
            continue

        msg_type = msg.get_type()

        # ====================================================
        # FLIGHT MODE
        # ====================================================

        if msg_type == "HEARTBEAT":

            flight_mode = mavutil.mode_string_v10(msg)

        # ====================================================
        # GPS POSITION
        # ====================================================

        elif msg_type == "GLOBAL_POSITION_INT":

            latitude = msg.lat / 1e7
            longitude = msg.lon / 1e7
            altitude = msg.relative_alt / 1000.0

            # Current UTC timestamp
            timestamp = datetime.now(
                timezone.utc
            ).isoformat()

            telemetry = {
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "flight_mode": flight_mode,
                "timestamp": timestamp
            }

            try:

                response = requests.post(
                    BACKEND_URL,
                    json=telemetry,
                    timeout=2
                )

                response.raise_for_status()

                print(
                    f"Lat: {latitude:.7f} | "
                    f"Lon: {longitude:.7f} | "
                    f"Alt: {altitude:.2f} m | "
                    f"Mode: {flight_mode} | "
                    f"Time: {timestamp} | "
                    f"Backend: OK"
                )

            except requests.RequestException as error:

                print(
                    f"Backend connection error: {error}"
                )

            time.sleep(0.5)

except KeyboardInterrupt:

    print()
    print("=" * 60)
    print("Telemetry bridge stopped.")
    print("=" * 60)