# Week 01 Logbook

## Issue #5 - Connect QGroundControl to PX4 SITL

---

## Objective

Connect QGroundControl to PX4 SITL and perform a simulated manual flight.

---

# Procedure

## Step 1

Started PX4 SITL.

```bash
cd ~/PX4/PX4-Autopilot

make px4_sitl gz_x500
```

---

## Step 2

Opened QGroundControl on Windows.

QGroundControl automatically detected the MAVLink connection from the WSL2 PX4 instance.

Connection status changed to:

```
Ready To Fly
```

---

## Step 3

Verified MAVLink communication.

PX4 console displayed:

```
INFO [mavlink] partner IP: 127.0.0.1
INFO [commander] Ready for takeoff!
```

This confirmed successful communication between:

- PX4 SITL
- Gazebo Sim
- QGroundControl

---

## Step 4

Performed manual flight test.

Completed:

- Vehicle Arm
- Takeoff
- Hover
- Direction Change
- Landing

---

# PX4 Console Logs

Observed:

```
INFO [commander] Armed by internal command

INFO [navigator] Using default takeoff altitude

INFO [commander] Takeoff detected

INFO [commander] Landing detected

INFO [commander] Disarmed by landing
```

---

# Test Observations

| Test | Status |
|-------|--------|
| Gazebo Launch | ✅ |
| Drone Spawn | ✅ |
| MAVLink Connection | ✅ |
| QGroundControl Connected | ✅ |
| Vehicle Armed | ✅ |
| Takeoff | ✅ |
| Hover | ✅ |
| Landing | ✅ |

---

# Evidence

The screenshot below shows:

- Gazebo Sim running
- PX4 SITL console
- QGroundControl connected
- Vehicle Ready To Fly

![Issue 5 Proof](../../sitl-setup/images/issue-4-completed.png)

---

# Flight Recording

Flight log (.ulg) generated automatically by PX4.

Example:

```
./log/2026-07-30/07_01_46.ulg
```

---

# Outcome

Successfully completed the following:

- Connected QGroundControl to PX4 SITL
- Verified MAVLink communication
- Performed manual takeoff
- Performed simulated flight
- Successfully landed the vehicle

---

# Acceptance Criteria

- ✅ QGroundControl connected to SITL
- ✅ Manual flight completed
- ✅ Takeoff verified
- ✅ Landing verified
- ✅ Screenshot captured
- ✅ Flight log generated