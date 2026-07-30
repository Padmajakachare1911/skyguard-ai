# Issue #4 - PX4 SITL Environment Setup using Gazebo Sim

## Objective

Set up a complete PX4 Software-In-The-Loop (SITL) simulation environment for flight software testing.

> Note:
> The original issue specifies **jMAVSim**.
> Since the latest PX4 versions (v1.18+) officially support **Gazebo Sim**, Gazebo Sim was used instead.

---

# Development Environment

| Component | Version |
|-----------|----------|
| Operating System | Windows 11 |
| Linux Environment | WSL2 Ubuntu 24.04.4 LTS |
| PX4 Firmware | v1.18.0-beta1 |
| Gazebo Sim | 8.14.0 |
| GCC | 13.3.0 |

---

# Software Installed

- PX4 Autopilot
- Gazebo Sim
- QGroundControl
- Build dependencies
- MAVLink support

---

# Installation Steps

## 1. Clone PX4

```bash
mkdir -p ~/PX4
cd ~/PX4

git clone https://github.com/PX4/PX4-Autopilot.git

cd PX4-Autopilot
```

---

## 2. Install Dependencies

```bash
bash ./Tools/setup/ubuntu.sh
```

Restart WSL after installation.

---

## 3. Build PX4 SITL

```bash
make px4_sitl
```

The build completed successfully.

---

## 4. Launch Gazebo Simulation

```bash
make px4_sitl gz_x500
```

Gazebo Sim started successfully.

The X500 drone model spawned correctly.

---

# Verification

Successfully verified:

- PX4 started successfully
- Gazebo launched
- Ground plane loaded
- X500 drone spawned
- MAVLink server started
- SITL running correctly

Console output included:

```
INFO [px4] Startup script returned successfully
```

---

# Commands Used

```bash
cd ~/PX4/PX4-Autopilot

make px4_sitl

make px4_sitl gz_x500
```

---

# Issues Faced

## Issue 1

```
Preflight Fail:
No connection to the GCS
```

Reason:

QGroundControl was not connected.

Solution:

Started QGroundControl and allowed it to connect over MAVLink.

---

## Issue 2

```
ninja: no work to do
```

Reason:

PX4 was already built successfully.

No rebuild was required.

---

## Issue 3

```
No heading reference
```

Reason:

Compass heading is unavailable before GPS lock.

This warning disappears after simulation initializes.

---

# Proof

Simulation launched successfully.

![Gazebo Simulation](images/issue-4-completed.png)

---

# Acceptance Criteria

- ✅ PX4 SITL running locally
- ✅ Gazebo Sim launched successfully
- ✅ Virtual drone spawned
- ✅ Basic movement verified
- ✅ Ready for QGroundControl integration