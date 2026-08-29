# Autonomous Patrol Mission – SkyGuard AI

## Issue Completion Documentation

### Objective

Implemented a repeatable autonomous drone patrol mission using **PX4 SITL and MAVLink**. The system defines a patrol area, uploads GPS waypoints, executes the route autonomously, and returns the drone to the launch position after completing the patrol.

---

## Implementation

The patrol mission was implemented using:

```text
flight-software/mission-scripts/patrol_route.py
```

The script handles the complete mission workflow:

```text
PX4 SITL
   ↓
MAVLink Connection
   ↓
Clear Previous Mission
   ↓
Upload Patrol Waypoints
   ↓
Arm Drone
   ↓
AUTO.MISSION
   ↓
Execute Patrol Route
   ↓
Final Waypoint
   ↓
Return To Launch (RTL)
   ↓
Mission Complete
```

---

## Patrol Area

A rectangular patrol area was defined using four GPS waypoints.

| Waypoint |   Latitude | Longitude | Altitude |
| -------- | ---------: | --------: | -------: |
| WP0      | 47.3977500 | 8.5456000 |     15 m |
| WP1      | 47.3977500 | 8.5466000 |     15 m |
| WP2      | 47.3985000 | 8.5466000 |     15 m |
| WP3      | 47.3985000 | 8.5456000 |     15 m |

The drone follows these waypoints sequentially to cover the defined patrol area.

---

## MAVLink Configuration

During testing, UDP port `14550` was already being used by QGroundControl. To avoid a port conflict, a dedicated MAVLink connection was configured for the Python mission script.

PX4 MAVLink endpoint:

```text
Local Port: 18571
Remote Port: 14551
Mode: onboard
```

Python connection:

```text
udpin:127.0.0.1:14551
```

This allows QGroundControl and the Python mission controller to communicate with PX4 simultaneously.

---

## Mission Execution

The script performs the following operations:

1. Connects to PX4 SITL.
2. Waits for the PX4 heartbeat.
3. Clears any previously uploaded mission.
4. Uploads the four patrol waypoints.
5. Confirms successful mission upload.
6. Arms the vehicle.
7. Switches the vehicle to `AUTO.MISSION`.
8. Monitors patrol progress.
9. Detects completion of the final waypoint.
10. Sends the Return-To-Launch command.
11. Monitors the RTL operation.
12. Reports mission completion.

---

## Testing

The mission was tested in the PX4 SITL environment.

The MAVLink connection was verified using:

```text
mavlink status
```

The mission script was executed using:

```bash
cd ~/flight-software/mavlink-client
source venv/bin/activate
python3 patrol_route.py
```

The mission was tested repeatedly in simulation to verify consistent waypoint execution and RTL behavior.

---

## Troubleshooting Performed

### UDP Port Conflict

Initially, the Python MAVLink client produced:

```text
OSError: [Errno 98] Address already in use
```

Port `14550` was investigated using:

```bash
sudo ss -lunp | grep 14550
sudo lsof -i :14550
```

The Windows host was then checked:

```powershell
Get-NetUDPEndpoint -LocalPort 14550
netstat -ano -p udp | findstr :14550
Get-Process -Id 5604
```

The port was found to be used by **QGroundControl**.

A separate MAVLink endpoint was therefore configured for the Python mission client.

---

### Invalid MAVLink Mode

An initial PX4 command using:

```text
mavlink start -u 18571 -o 14551 -r 4000000 -m normal
```

returned:

```text
ERROR [mavlink] invalid mode
```

The command was corrected to:

```text
mavlink start -u 18571 -o 14551 -r 4000000 -m onboard
```

The connection was then verified using:

```text
mavlink status
```

---

### Mission Upload / RTL Handling

The initial implementation attempted to include RTL as an additional mission item, which resulted in a mission rejection.

The mission logic was corrected so that RTL is triggered separately after the final patrol waypoint:

```text
WP0 → WP1 → WP2 → WP3 → RTL
```

This provides a cleaner and more reliable PX4 mission workflow.

---

## Final File

The completed mission script is:

```text
flight-software/mission-scripts/patrol_route.py
```

The script provides a reusable SITL patrol mission that can be executed multiple times without manually entering individual waypoint commands.

---

## Acceptance Criteria

| Requirement                       | Status      |
| --------------------------------- | ----------- |
| Patrol area defined               | ✅ Completed |
| Waypoints uploaded                | ✅ Completed |
| Autonomous route implemented      | ✅ Completed |
| Return-to-Launch implemented      | ✅ Completed |
| PX4 SITL integration              | ✅ Completed |
| MAVLink communication             | ✅ Completed |
| Patrol route tested in simulation | ✅ Completed |
| Same route tested repeatedly      | ✅ Completed |
| Mission script created            | ✅ Completed |
| Mission script committed          | ✅ Completed |

---

## Completion Status

**Issue Status: COMPLETED ✅**

The autonomous patrol mission has been implemented and integrated with PX4 SITL. The system can upload the predefined patrol route, execute the waypoints autonomously, and initiate Return-To-Launch after completing the patrol.

**Deliverable:**

```text
flight-software/mission-scripts/patrol_route.py
```
