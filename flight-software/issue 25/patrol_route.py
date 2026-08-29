#!/usr/bin/env python3

"""
SkyGuard AI - Autonomous Patrol Mission

Mission flow:
    PX4 SITL
       ↓
    MAVLink UDP 14551
       ↓
    Python MAVLink Client
       ↓
    Upload 4 patrol waypoints
       ↓
    Arm
       ↓
    AUTO.MISSION
       ↓
    Complete patrol
       ↓
    Return To Launch (RTL)
"""

from pymavlink import mavutil
import time
import sys


# ============================================================
# CONFIGURATION
# ============================================================

# Dedicated MAVLink connection for Python.
# QGroundControl continues to use UDP 14550.
CONNECTION = "udpin:127.0.0.1:14551"

PATROL_ALTITUDE = 15  # meters

HEARTBEAT_TIMEOUT = 30
MISSION_TIMEOUT = 15
WAYPOINT_TIMEOUT = 120
RTL_TIMEOUT = 120

# Patrol rectangle
PATROL_AREA = [
    (47.3977500, 8.5456000),  # WP0
    (47.3977500, 8.5466000),  # WP1
    (47.3985000, 8.5466000),  # WP2
    (47.3985000, 8.5456000),  # WP3
]


# ============================================================
# CONNECT TO PX4
# ============================================================

def connect_to_px4():
    print("Connecting to PX4 SITL...")

    vehicle = mavutil.mavlink_connection(
        CONNECTION,
        source_system=250,
        source_component=1
    )

    print("Waiting for heartbeat...")

    heartbeat = vehicle.wait_heartbeat(timeout=HEARTBEAT_TIMEOUT)

    if heartbeat is None:
        raise RuntimeError(
            "No heartbeat received from PX4 SITL."
        )

    system_id = heartbeat.get_srcSystem()
    component_id = heartbeat.get_srcComponent()

    if system_id <= 0:
        raise RuntimeError(
            f"Invalid PX4 system ID received: {system_id}"
        )

    vehicle.target_system = system_id
    vehicle.target_component = component_id

    print(
        f"Connected to system={system_id}, "
        f"component={component_id}"
    )

    return vehicle


# ============================================================
# CLEAR OLD MISSION
# ============================================================

def clear_mission(vehicle):

    print("\nClearing previous mission...")

    vehicle.mav.mission_clear_all_send(
        vehicle.target_system,
        vehicle.target_component,
        mavutil.mavlink.MAV_MISSION_TYPE_MISSION
    )

    # Wait for PX4 acknowledgement.
    ack = vehicle.recv_match(
        type="MISSION_ACK",
        blocking=True,
        timeout=5
    )

    if ack is not None:
        if ack.type != mavutil.mavlink.MAV_MISSION_ACCEPTED:
            print(
                f"Warning: mission clear ACK type={ack.type}"
            )

    time.sleep(1)


# ============================================================
# UPLOAD PATROL WAYPOINTS
# ============================================================

def upload_mission(vehicle):

    clear_mission(vehicle)

    waypoint_count = len(PATROL_AREA)

    print(
        f"Uploading {waypoint_count} patrol waypoints"
    )

    # Tell PX4 how many mission items will be uploaded.
    vehicle.mav.mission_count_send(
        vehicle.target_system,
        vehicle.target_component,
        waypoint_count,
        mavutil.mavlink.MAV_MISSION_TYPE_MISSION
    )

    uploaded = 0

    deadline = time.time() + MISSION_TIMEOUT

    while uploaded < waypoint_count:

        remaining = deadline - time.time()

        if remaining <= 0:
            raise RuntimeError(
                f"Timeout waiting for mission request "
                f"for waypoint {uploaded}"
            )

        msg = vehicle.recv_match(
            type=[
                "MISSION_REQUEST_INT",
                "MISSION_REQUEST"
            ],
            blocking=True,
            timeout=remaining
        )

        if msg is None:
            raise RuntimeError(
                f"Timeout waiting for mission request "
                f"{uploaded}"
            )

        seq = msg.seq

        if seq < 0 or seq >= waypoint_count:
            raise RuntimeError(
                f"PX4 requested invalid waypoint sequence: {seq}"
            )

        lat, lon = PATROL_AREA[seq]

        print(
            f"Waypoint {seq}: "
            f"lat={lat}, "
            f"lon={lon}, "
            f"alt={PATROL_ALTITUDE}m"
        )

        vehicle.mav.mission_item_int_send(
            vehicle.target_system,
            vehicle.target_component,

            seq,

            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,

            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,

            0,      # current
            1,      # autocontinue

            0,      # param1: hold time
            2,      # param2: acceptance radius
            0,      # param3: pass through
            0,      # param4: yaw

            int(lat * 1e7),
            int(lon * 1e7),

            PATROL_ALTITUDE
        )

        uploaded += 1

        deadline = time.time() + MISSION_TIMEOUT

    # PX4 should send final MISSION_ACK.
    ack = vehicle.recv_match(
        type="MISSION_ACK",
        blocking=True,
        timeout=MISSION_TIMEOUT
    )

    if ack is None:
        raise RuntimeError(
            "No MISSION_ACK received after waypoint upload."
        )

    if ack.type != mavutil.mavlink.MAV_MISSION_ACCEPTED:
        raise RuntimeError(
            f"Mission rejected. ACK type: {ack.type}"
        )

    print("\nMission uploaded successfully.")


# ============================================================
# ARM VEHICLE
# ============================================================

def arm_vehicle(vehicle):

    print("\nArming vehicle...")

    vehicle.mav.command_long_send(
        vehicle.target_system,
        vehicle.target_component,

        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,

        0,

        1,  # ARM
        0,
        0,
        0,
        0,
        0,
        0
    )

    # Wait for armed state.
    start = time.time()

    while time.time() - start < 15:

        msg = vehicle.recv_match(
            type="HEARTBEAT",
            blocking=True,
            timeout=2
        )

        if msg is None:
            continue

        if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:

            print("Vehicle armed.")
            return

    raise RuntimeError(
        "Vehicle did not arm within timeout."
    )


# ============================================================
# SET AUTO MISSION MODE
# ============================================================

def start_mission(vehicle):

    print("\nStarting AUTO.MISSION...")

    # PX4 custom mode for AUTO.MISSION.
    vehicle.set_mode("AUTO.MISSION")

    time.sleep(2)

    # Confirm mode.
    msg = vehicle.recv_match(
        type="HEARTBEAT",
        blocking=True,
        timeout=5
    )

    if msg is not None:

        mode = mavutil.mode_string_v10(msg)

        print(f"Current flight mode: {mode}")

    print("AUTO.MISSION command sent.")


# ============================================================
# MONITOR PATROL
# ============================================================

def monitor_patrol(vehicle):

    print("\nMonitoring patrol mission...\n")

    final_waypoint = len(PATROL_AREA) - 1

    last_waypoint = -1

    start_time = time.time()

    while True:

        if time.time() - start_time > WAYPOINT_TIMEOUT:
            raise RuntimeError(
                "Patrol mission timed out."
            )

        msg = vehicle.recv_match(
            type=[
                "MISSION_CURRENT",
                "HEARTBEAT"
            ],
            blocking=True,
            timeout=5
        )

        if msg is None:
            continue

        # ----------------------------------------
        # Mission progress
        # ----------------------------------------

        if msg.get_type() == "MISSION_CURRENT":

            seq = msg.seq

            if seq != last_waypoint:

                print(
                    f"Mission progress: "
                    f"WP{seq} "
                    f"({seq + 1}/{len(PATROL_AREA)})"
                )

                last_waypoint = seq

            if seq >= final_waypoint:

                print(
                    "\nFinal patrol waypoint reached."
                )

                return


# ============================================================
# RETURN TO LAUNCH
# ============================================================

def return_to_launch(vehicle):

    print("\nSending RETURN TO LAUNCH...")

    vehicle.mav.command_long_send(
        vehicle.target_system,
        vehicle.target_component,

        mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,

        0,

        0,
        0,
        0,
        0,
        0,
        0
    )

    time.sleep(2)

    print("RTL command sent.")


# ============================================================
# MONITOR RTL
# ============================================================

def monitor_rtl(vehicle):

    print("\nMonitoring RTL...")

    start_time = time.time()

    while time.time() - start_time < RTL_TIMEOUT:

        msg = vehicle.recv_match(
            type=[
                "HEARTBEAT",
                "GLOBAL_POSITION_INT"
            ],
            blocking=True,
            timeout=5
        )

        if msg is None:
            continue

        if msg.get_type() == "HEARTBEAT":

            mode = mavutil.mode_string_v10(msg)

            print(
                f"\rCurrent flight mode: {mode}",
                end=""
            )

            # PX4 normally switches to a landed/idle mode
            # after completing RTL.
            if mode in [
                "STANDBY",
                "STABILIZED",
                "POSCTL"
            ]:

                print(
                    f"\nRTL completed. "
                    f"Current mode: {mode}"
                )

                return

    print("\nRTL monitoring timeout reached.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("SKYGUARD AI - AUTONOMOUS PATROL MISSION")
    print("=" * 60)

    print("\nPatrol area:")

    for i, (lat, lon) in enumerate(PATROL_AREA):

        print(
            f"  WP{i}: "
            f"{lat:.7f}, "
            f"{lon:.7f}"
        )

    print()

    vehicle = None

    try:

        # 1. Connect
        vehicle = connect_to_px4()

        # 2. Upload mission
        upload_mission(vehicle)

        # 3. Arm
        arm_vehicle(vehicle)

        # 4. Start autonomous mission
        start_mission(vehicle)

        # 5. Monitor waypoints
        monitor_patrol(vehicle)

        # 6. Return home
        return_to_launch(vehicle)

        # 7. Monitor RTL
        monitor_rtl(vehicle)

        print("\n")
        print("=" * 60)
        print("PATROL MISSION COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except KeyboardInterrupt:

        print("\n\nMission interrupted by user.")

        if vehicle is not None:
            try:
                vehicle.close()
            except Exception:
                pass

        sys.exit(1)

    except Exception as error:

        print("\n")
        print("=" * 60)
        print("PATROL MISSION FAILED")
        print("=" * 60)
        print(f"Error: {error}")

        if vehicle is not None:
            try:
                vehicle.close()
            except Exception:
                pass

        sys.exit(1)

    finally:

        if vehicle is not None:
            vehicle.close()


if __name__ == "__main__":
    main()