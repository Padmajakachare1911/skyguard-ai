# SITL Telemetry + Geofence Integration

## Issue

Use live PX4 SITL telemetry data for restricted-zone detection by integrating the MAVLink telemetry reader with a geofence checker.

## Objective

The objective of this issue was to connect live PX4 SITL telemetry with geofence logic so that the system can receive the drone's GPS coordinates, determine its restricted-zone status, and detect zone entry and exit events.

## Implementation

The following workflow was implemented:

PX4 SITL
   ↓
MAVLink / UDP
   ↓
MAVLink Telemetry Reader
   ↓
Latitude + Longitude
   ↓
Geofence Checker
   ↓
Inside / Outside
   ↓
Zone Entry / Zone Exit


## Features Implemented

- Connected Python application to PX4 SITL using `pymavlink`.
- Received live `GLOBAL_POSITION_INT` MAVLink messages.
- Extracted live latitude and longitude from SITL.
- Extracted relative altitude and flight mode for telemetry monitoring.
- Implemented a dedicated `geofence.py` module.
- Implemented circular restricted-zone detection.
- Used the Haversine formula to calculate distance from the geofence center.
- Added inside/outside zone detection.
- Added `ZONE_ENTRY` detection.
- Added `ZONE_EXIT` detection.
- Integrated the geofence checker with live MAVLink telemetry.
- Added continuous monitoring of the drone's position.

## Project Files

```text
mavlink-client/
│
├── README.md
├── telemetry_reader.py
├── telemetry_geofence.py
├── geofence.py
├── requirements.txt
└── venv/
````

### `telemetry_reader.py`

Reads live telemetry from PX4 SITL using MAVLink and displays:

* Latitude
* Longitude
* Altitude
* Flight mode

### `geofence.py`

Contains the geofence logic responsible for:

* Calculating distance from the restricted-zone center.
* Determining whether the drone is inside or outside.
* Detecting zone entry.
* Detecting zone exit.

### `telemetry_geofence.py`

Integrates the MAVLink telemetry reader with the geofence checker.

It receives live GPS data and passes the latitude and longitude to the geofence module.

## MAVLink Connection

The integration uses the PX4 SITL MAVLink UDP connection:

```python
udpin:127.0.0.1:14540
```

The connection was verified using the PX4 command:

```text
pxh> mavlink status
```

PX4 was observed sending MAVLink data through UDP with:

```text
UDP (14580, remote port: 14540)
```

## Geofence Configuration

For SITL testing, a circular restricted zone was configured around the simulated drone's starting position.

Example configuration:

```text
Center Latitude  : 47.3979708
Center Longitude : 8.5461638
Radius           : 20 meters
```

The radius can be changed according to the required restricted area.

## Detection Logic

The system calculates the distance between the current drone position and the center of the restricted zone.

```text
Distance <= Radius
        ↓
     INSIDE

Distance > Radius
        ↓
     OUTSIDE
```

The system also maintains the previous zone state.

```text
INSIDE → OUTSIDE
    ↓
ZONE_EXIT
```

```text
OUTSIDE → INSIDE
    ↓
ZONE_ENTRY
```

The initial GPS reading establishes the starting state and does not generate a false entry/exit event.

## Commands Used

### Navigate to the project

```bash
cd ~/flight-software/mavlink-client
```

### Activate virtual environment

```bash
source venv/bin/activate
```

### Install pymavlink

```bash
pip install pymavlink
```

### Start PX4 SITL

From the PX4 directory:

```bash
cd ~/PX4/PX4-Autopilot
make px4_sitl gz_x500
```

### Check MAVLink status

Inside the PX4 terminal:

```text
pxh> mavlink status
```

### Run telemetry + geofence integration

```bash
cd ~/flight-software/mavlink-client
source venv/bin/activate
python3 telemetry_geofence.py
```

### Check Python syntax

```bash
python3 -m py_compile geofence.py telemetry_geofence.py
```

## Testing

The integration was tested against the running PX4 SITL simulator.

Live GPS data was successfully received, for example:

```text
Latitude  : 47.3979708
Longitude : 8.5461638
Altitude  : 0.03 m
```

The received coordinates were passed to the geofence checker, which calculated the distance from the restricted-zone center and reported the current zone status.

Example:

```text
Distance  : 0.04 m
Zone      : INSIDE
```

When the drone crosses the configured geofence boundary, the system generates the corresponding event:

```text
ZONE_EXIT
```

or:

```text
ZONE_ENTRY
```

## Acceptance Criteria

| Acceptance Criteria                        | Status      |
| ------------------------------------------ | ----------- |
| Live SITL GPS data received                | ✅ Completed |
| Latitude and longitude received            | ✅ Completed |
| Coordinates passed to geofence logic       | ✅ Completed |
| Zone status checked continuously           | ✅ Completed |
| Zone entry detected                        | ✅ Completed |
| Zone exit detected                         | ✅ Completed |
| Telemetry-geofence integration implemented | ✅ Completed |

## Issue Status

**Status: COMPLETED ✅**

The assigned SITL telemetry and geofence integration issue has been completed separately.

The system successfully connects to PX4 SITL, receives live GPS telemetry through MAVLink, passes the coordinates to the geofence module, determines restricted-zone status, and detects zone entry and exit events.

## Completion Summary

The following pipeline is now functional:

```text
PX4 SITL
   ↓
Live MAVLink Telemetry
   ↓
GPS Latitude / Longitude
   ↓
Geofence Checker
   ↓
Distance Calculation
   ↓
Inside / Outside Detection
   ↓
Zone Entry / Exit Event
```

This implementation provides the software foundation for connecting future SkyGuard AI geofence events with the backend, dashboard alerts, violation logging, and autonomous safety actions.

````