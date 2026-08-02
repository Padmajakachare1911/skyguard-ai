from pymavlink import mavutil
import time

# ---------------------------------------------------------------------
# Connect to PX4
# ---------------------------------------------------------------------

print("Connecting to PX4 SITL...")

master = mavutil.mavlink_connection("udp:127.0.0.1:14540")

master.wait_heartbeat()

print(f"Heartbeat received from System {master.target_system}")

# ---------------------------------------------------------------------
# Mission Waypoints
# ---------------------------------------------------------------------

waypoints = [

    # Takeoff
    {
        "command": mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        "lat": 47.397742,
        "lon": 8.545594,
        "alt": 10
    },

    # WP1
    {
        "command": mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
        "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        "lat": 47.397842,
        "lon": 8.545694,
        "alt": 10
    },

    # WP2
    {
        "command": mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
        "frame": mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        "lat": 47.397942,
        "lon": 8.545794,
        "alt": 10
    }
]

print("Uploading Mission...")

master.mav.mission_clear_all_send(
    master.target_system,
    master.target_component
)

time.sleep(1)

master.mav.mission_count_send(
    master.target_system,
    master.target_component,
    len(waypoints),
    mavutil.mavlink.MAV_MISSION_TYPE_MISSION
)

while True:

    msg = master.recv_match(
        type=['MISSION_REQUEST_INT','MISSION_REQUEST'],
        blocking=True
    )

    seq = msg.seq

    wp = waypoints[seq]

    print(f"Uploading waypoint {seq}")

    master.mav.mission_item_int_send(

        master.target_system,
        master.target_component,

        seq,

        wp["frame"],

        wp["command"],

        0,          # current

        1,          # autocontinue

        0,0,0,0,

        int(wp["lat"]*1e7),

        int(wp["lon"]*1e7),

        wp["alt"],

        mavutil.mavlink.MAV_MISSION_TYPE_MISSION
    )

    if seq == len(waypoints)-1:
        break

ack = master.recv_match(type='MISSION_ACK', blocking=True)

print("Mission Upload Successful")

# ---------------------------------------------------------------------
# ARM
# ---------------------------------------------------------------------

print("Arming...")

master.mav.command_long_send(

    master.target_system,

    master.target_component,

    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,

    0,

    1,

    0,0,0,0,0,0
)

master.motors_armed_wait()

print("Vehicle Armed")

# ---------------------------------------------------------------------
# Set Mission Mode
# ---------------------------------------------------------------------

print("Switching to MISSION mode")

master.set_mode("MISSION")

time.sleep(3)

# ---------------------------------------------------------------------
# Start Mission
# ---------------------------------------------------------------------

print("Starting Mission")

master.mav.command_long_send(

    master.target_system,

    master.target_component,

    mavutil.mavlink.MAV_CMD_MISSION_START,

    0,

    0,

    0,

    0,

    0,

    0,

    0,

    0
)

print("Mission Started\n")

# ---------------------------------------------------------------------
# Monitor Mission
# ---------------------------------------------------------------------

while True:

    msg = master.recv_match(blocking=True)

    if msg is None:
        continue

    mtype = msg.get_type()

    if mtype == "MISSION_CURRENT":

        print(f"Current Waypoint : {msg.seq}")

    elif mtype == "MISSION_ITEM_REACHED":

        print(f"Reached Waypoint {msg.seq}")

    elif mtype == "GLOBAL_POSITION_INT":

        print(
            f"Lat:{msg.lat/1e7:.6f} "
            f"Lon:{msg.lon/1e7:.6f} "
            f"Alt:{msg.relative_alt/1000:.1f}m"
        )

    elif mtype == "STATUSTEXT":

        print(msg.text)

    elif mtype == "HEARTBEAT":

        mode = mavutil.mode_string_v10(msg)

        print(f"Mode : {mode}")

        if mode == "RTL":

            print("Return To Launch")

        if mode == "MANUAL":
            print("Mission Finished")
            break