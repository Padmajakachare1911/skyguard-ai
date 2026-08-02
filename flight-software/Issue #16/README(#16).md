# Automated Waypoint Mission Execution using MAVLink

## Overview

This project implements an automated waypoint mission execution system for the PX4 Software-In-The-Loop (SITL) environment using Python and the `pymavlink` library.

The mission script connects to the PX4 simulator, uploads a waypoint mission, arms the vehicle, switches it to Mission mode, starts autonomous flight, and monitors mission progress through MAVLink telemetry.

---

## Objective

Develop a MAVLink mission script that can:

- Upload waypoint missions to PX4 SITL
- Start the mission automatically
- Monitor mission execution
- Complete the mission with a Return-to-Launch (RTL) sequence

---

## Project Structure

```
flight-software/
└── mission-scripts/
    ├── mission_upload.py
    ├── requirements.txt
    └── README.md
```

---

## Technologies Used

- Python 3.12
- PX4 SITL
- Gazebo Sim
- MAVLink
- pymavlink
- QGroundControl
- WSL2 Ubuntu 24.04.4 LTS

---

## Features Implemented

- Establishes MAVLink connection with PX4 SITL
- Waits for vehicle heartbeat
- Clears existing missions
- Uploads waypoint mission
- Waits for mission acknowledgement
- Arms the vehicle
- Switches vehicle to Mission mode
- Starts autonomous mission
- Monitors waypoint progress
- Displays live mission status and telemetry

---

## Mission Workflow

```
Start PX4 SITL
        │
        ▼
Connect to Vehicle
        │
        ▼
Wait for Heartbeat
        │
        ▼
Clear Previous Mission
        │
        ▼
Upload Waypoints
        │
        ▼
Receive Mission ACK
        │
        ▼
Arm Vehicle
        │
        ▼
Switch to Mission Mode
        │
        ▼
Start Mission
        │
        ▼
Monitor Mission Progress
        │
        ▼
Return to Launch (RTL)
        │
        ▼
Mission Complete
```

---

## Installation

Clone the repository and navigate to the project directory.

```bash
cd flight-software/mission-scripts
```

Create a virtual environment.

```bash
python3 -m venv venv
```

Activate the virtual environment.

```bash
source venv/bin/activate
```

Install the required dependencies.

```bash
pip install -r requirements.txt
```

---

## Running the Project

### Start PX4 SITL

```bash
cd ~/PX4/PX4-Autopilot
```

```bash
make px4_sitl gz_x500
```

Wait until:

- Gazebo Sim launches
- X500 drone spawns
- QGroundControl connects

---

### Execute Mission Script

Open another terminal.

```bash
cd ~/flight-software/mission-scripts
```

Activate the virtual environment.

```bash
source venv/bin/activate
```

Run the mission script.

```bash
python3 mission_upload.py
```

---

## Expected Console Output

```
Connecting to PX4 SITL...
Heartbeat received from System 1

Uploading Mission...
Mission Upload Successful

Arming...
Vehicle Armed

Switching to MISSION mode...

Starting Mission...

Current Waypoint : 1

Reached Waypoint 1

Current Waypoint : 2

Mission Completed

Returning To Launch...
```

---

## Deliverables

- `mission_upload.py`
- `requirements.txt`
- `README.md`

---

## Acceptance Criteria

| Requirement | Status |
|-------------|:------:|
| Upload waypoints successfully | ✅ |
| Start mission automatically | ✅ |
| Monitor mission progress | ✅ |
| Complete Return-to-Launch sequence | ✅ |
| Tested using PX4 SITL | ✅ |
| Script committed to repository | ✅ |

---

## Learning Outcomes

Through this task, I gained practical experience with:

- MAVLink communication using `pymavlink`
- PX4 SITL mission automation
- MAVLink mission upload protocol
- Vehicle arming and flight mode control
- Monitoring autonomous mission execution
- Working with Gazebo Sim and QGroundControl for testing

---

## Conclusion

The automated waypoint mission execution script was successfully developed for the PX4 SITL environment. The implementation demonstrates the complete mission workflow, including connecting to the simulator, uploading waypoints, initiating autonomous flight, monitoring mission execution, and performing a Return-to-Launch sequence. The project fulfills the assigned objective and provides a foundation for developing more advanced autonomous flight missions using MAVLink.