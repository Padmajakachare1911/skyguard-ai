# MAVLink Telemetry Client

## Issue Summary

This task implements a MAVLink client that connects to the PX4 Software-In-The-Loop (SITL) simulator and reads live telemetry data from the simulated drone. The client is developed using Python and the `pymavlink` library.

The script establishes a MAVLink connection with PX4 SITL, waits for a heartbeat to confirm communication, and continuously displays telemetry information in the terminal.

---

## Objective

Create a MAVLink client to read live drone telemetry from PX4 SITL.

---

## Features

- Connects to PX4 SITL over the MAVLink protocol.
- Waits for a valid MAVLink heartbeat before starting telemetry.
- Reads and displays live drone telemetry:
  - Latitude
  - Longitude
  - Relative Altitude
  - Flight Mode
- Continuously updates telemetry in the console.

---

## Project Structure

```text
flight-software/
│
├── sitl-setup/
│   └── README.md
│
└── mavlink-client/
    ├── telemetry_reader.py
    ├── requirements.txt
    └── README.md
```

---

## Requirements

- Windows 11
- WSL2 Ubuntu 24.04
- Python 3.12
- PX4 Autopilot
- Gazebo Sim
- QGroundControl
- pymavlink

---

## Installation

### 1. Navigate to the project directory

```bash
cd ~/flight-software/mavlink-client
```

### 2. Create a virtual environment (optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running PX4 SITL

Start the simulator from the PX4 directory.

```bash
cd ~/PX4/PX4-Autopilot
make px4_sitl gz_x500
```

Wait until PX4 reports:

```text
INFO [commander] Ready for takeoff!
```

---

## Running the MAVLink Client

Open another terminal.

```bash
cd ~/flight-software/mavlink-client

source venv/bin/activate

python3 telemetry_reader.py
```

---

## Example Output

```text
Connecting to PX4 SITL...

Connected!
System ID: 1
Component ID: 1

Receiving live telemetry...

--------------------------------
Latitude   : 47.3977420
Longitude  : 8.5455940
Altitude   : 0.01 m
Flight Mode: Manual

--------------------------------
Latitude   : 47.3977420
Longitude  : 8.5455940
Altitude   : 0.03 m
Flight Mode: Position
```

---

## Implementation Details

The client performs the following steps:

1. Creates a MAVLink UDP connection.
2. Waits until a heartbeat is received from PX4.
3. Continuously listens for MAVLink messages.
4. Extracts telemetry from:
   - `GLOBAL_POSITION_INT`
   - `HEARTBEAT`
5. Displays the latest telemetry in the terminal.

---

## Files Included

| File | Description |
|------|-------------|
| `telemetry_reader.py` | Python script for reading MAVLink telemetry |
| `requirements.txt` | Python dependencies |
| `README.md` | Documentation for the MAVLink client |

---

## Challenges Faced

### Virtual Environment Setup

Initially, creating a Python virtual environment failed because the `python3-venv` package was not installed.

**Solution**

```bash
sudo apt update
sudo apt install python3-venv
```

---

### UDP Port Conflict

While connecting to PX4, the following error occurred:

```text
OSError: [Errno 98] Address already in use
```

**Cause**

QGroundControl was already using the default MAVLink UDP port (`14550`).

**Solution**

- Verified active MAVLink instances using:

```text
mavlink status
```

- Investigated PX4 UDP endpoints.
- Configured and tested additional MAVLink instances during debugging.

---

### Heartbeat Waiting

The client initially remained at:

```text
Connecting to PX4 SITL...
```

This occurred because the client was waiting for a MAVLink heartbeat while the telemetry endpoint configuration was being investigated.

---

## Acceptance Criteria

| Requirement | Status |
|------------|--------|
| Connect to PX4 SITL | ✅ Completed |
| Read live telemetry | ✅ Completed |
| Display Latitude | ✅ Completed |
| Display Longitude | ✅ Completed |
| Display Altitude | ✅ Completed |
| Display Flight Mode | ✅ Completed |
| Telemetry reader implemented | ✅ Completed |
| Code committed to repository | ✅ Completed |

---

## Technologies Used

- Python 3.12
- pymavlink
- PX4 Autopilot
- Gazebo Sim
- MAVLink Protocol
- QGroundControl
- WSL2 Ubuntu 24.04

---

## Conclusion

The MAVLink telemetry client was successfully developed to interface with PX4 SITL using the MAVLink protocol. The application establishes communication with the simulated vehicle, receives telemetry messages, and displays key flight information including latitude, longitude, altitude, and flight mode in real time. During development, MAVLink networking and UDP communication were analyzed to resolve connection and port configuration issues, resulting in a functional telemetry monitoring client suitable for future flight software development and testing.