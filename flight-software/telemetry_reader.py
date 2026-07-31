from pymavlink import mavutil

print("Connecting to PX4 SITL...")

# Connect to PX4 SITL UDPIN port 14561
master = mavutil.mavlink_connection("udpin:0.0.0.0:14561")

# Wait for heartbeat
master.wait_heartbeat()

print("Connected!")
print(
    f"Heartbeat received from system "
    f"{master.target_system} component {master.target_component}"
)

flight_mode = "Unknown"

while True:
    msg = master.recv_match(blocking=True)

    if msg is None:
        continue

    msg_type = msg.get_type()

    # GPS position
    if msg_type == "GLOBAL_POSITION_INT":
        latitude = msg.lat / 1e7
        longitude = msg.lon / 1e7
        altitude = msg.relative_alt / 1000

        print("\n-----------------------------")
        print(f"Latitude : {latitude:.7f}")
        print(f"Longitude: {longitude:.7f}")
        print(f"Altitude : {altitude:.2f} m")
        print(f"Mode     : {flight_mode}")

    # Flight mode
    elif msg_type == "HEARTBEAT":
        flight_mode = mavutil.mode_string_v10(msg)