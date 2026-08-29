from datetime import datetime

from pymavlink import mavutil

from geofence import Geofence


# ============================================================
# PX4 MAVLink CONNECTION
# ============================================================

# Current working PX4 SITL connection.
#
# PX4:
# UDP 14580
#     ↓
# remote port 14540
#     ↓
# Python MAVLink client

MAVLINK_CONNECTION = "udpin:127.0.0.1:14540"


# ============================================================
# RESTRICTED ZONE CONFIGURATION
# ============================================================

# Current SITL starting position observed from telemetry.
ZONE_CENTER_LAT = 47.3979708
ZONE_CENTER_LON = 8.5461638

# Restricted-zone radius in meters.
ZONE_RADIUS_M = 20.0


# ============================================================
# PROGRAM START
# ============================================================

print("=" * 60)
print("        SKYGUARD AI - TELEMETRY + GEOFENCE")
print("=" * 60)

print()
print("Connecting to PX4 SITL...")
print(f"MAVLink connection: {MAVLINK_CONNECTION}")


# ============================================================
# MAVLink CONNECTION
# ============================================================

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


# ============================================================
# INITIALIZE GEOFENCE
# ============================================================

geofence = Geofence(
    center_lat=ZONE_CENTER_LAT,
    center_lon=ZONE_CENTER_LON,
    radius_m=ZONE_RADIUS_M
)

print()
print("=" * 60)
print("RESTRICTED ZONE CONFIGURATION")
print("=" * 60)

print(f"Center Latitude : {ZONE_CENTER_LAT:.7f}")
print(f"Center Longitude: {ZONE_CENTER_LON:.7f}")
print(f"Radius          : {ZONE_RADIUS_M:.2f} meters")


# ============================================================
# FLIGHT MODE
# ============================================================

flight_mode = "UNKNOWN"


# ============================================================
# TELEMETRY LOOP
# ============================================================

print()
print("=" * 60)
print("LIVE TELEMETRY + GEOFENCE MONITORING")
print("=" * 60)

print("Press Ctrl+C to stop.")
print()


try:

    while True:

        # Receive MAVLink message.
        msg = master.recv_match(
            blocking=True
        )

        if msg is None:
            continue

        msg_type = msg.get_type()


        # ====================================================
        # HEARTBEAT
        # ====================================================

        if msg_type == "HEARTBEAT":

            # Get current PX4 flight mode.
            flight_mode = mavutil.mode_string_v10(msg)


        # ====================================================
        # GPS POSITION
        # ====================================================

        elif msg_type == "GLOBAL_POSITION_INT":

            # ------------------------------------------------
            # Convert MAVLink GPS values
            # ------------------------------------------------

            # Latitude and longitude are scaled by 1e7.
            latitude = msg.lat / 1e7
            longitude = msg.lon / 1e7

            # Relative altitude is provided in millimeters.
            altitude = msg.relative_alt / 1000.0


            # ------------------------------------------------
            # Run Geofence Check
            # ------------------------------------------------

            result = geofence.check_position(
                latitude,
                longitude
            )

            distance_m = result["distance_m"]
            inside = result["inside"]
            event = result["event"]


            # ------------------------------------------------
            # Determine Zone Status
            # ------------------------------------------------

            if inside:
                zone_status = "INSIDE"
            else:
                zone_status = "OUTSIDE"


            # ------------------------------------------------
            # Current Time
            # ------------------------------------------------

            timestamp = datetime.now().strftime(
                "%H:%M:%S"
            )


            # ------------------------------------------------
            # Display Telemetry
            # ------------------------------------------------

            print()
            print("-" * 60)

            print(f"Time      : {timestamp}")
            print(f"Latitude  : {latitude:.7f}")
            print(f"Longitude : {longitude:.7f}")
            print(f"Altitude  : {altitude:.2f} m")
            print(f"Mode      : {flight_mode}")
            print(f"Distance  : {distance_m:.2f} m")
            print(f"Zone      : {zone_status}")


            # ------------------------------------------------
            # Zone Entry Event
            # ------------------------------------------------

            if event == "ZONE_ENTRY":

                print()
                print("⚠️  GEOFENCE ALERT")
                print("Drone ENTERED the restricted zone.")
                print()


            # ------------------------------------------------
            # Zone Exit Event
            # ------------------------------------------------

            elif event == "ZONE_EXIT":

                print()
                print("🚨 GEOFENCE ALERT")
                print("Drone EXITED the restricted zone.")
                print()


except KeyboardInterrupt:

    print()
    print("=" * 60)
    print("Telemetry + geofence monitoring stopped.")
    print("=" * 60)