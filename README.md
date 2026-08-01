<div align="center">

# 🛡️ SkyGuard AI

### An Autonomous Drone That Never Stops Watching Out for You

*AI-powered aerial safety audits for construction sites, factories, and industrial facilities*

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Platform](https://img.shields.io/badge/flight%20stack-PX4%20%2F%20Pixhawk-red)
![CV](https://img.shields.io/badge/vision-YOLOv8-purple)
![Backend](https://img.shields.io/badge/backend-FastAPI-teal)
![Frontend](https://img.shields.io/badge/frontend-React-blue)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

---

## 👀 What is SkyGuard AI?

CCTV has blind spots. Manual inspections happen once a week. Unsafe habits creep back in the moment the safety officer walks away.

**SkyGuard AI** is a Pixhawk-based drone that flies its own inspection routes, watches everything through a real-time computer vision pipeline, and flags safety violations the instant they happen — no fixed camera, no waiting for the next scheduled walkthrough.

It detects missing PPE, unauthorized entry into restricted zones, unsafe proximity to machinery, and person-down emergencies — then geo-tags every violation, streams it to a live dashboard, and compiles it all into an automated safety report.

> Built as a Semester 5 mini project, aligned with **SDG 3** (Good Health & Well-Being), **SDG 8** (Decent Work & Economic Growth), and **SDG 9** (Industry, Innovation & Infrastructure).

---

## ✨ Key Features

- 🪖 **PPE Compliance Detection** — flags missing helmets and safety vests in real time
- 🚧 **Restricted-Zone Monitoring** — geofence-based alerts the moment someone enters a no-go area
- ⚙️ **Machinery Proximity Alerts** — warns when a worker gets too close to active equipment
- 🧍 **Person-Down Detection** — catches potential fall or medical emergencies mid-flight
- 📍 **GPS-Tagged Violations** — every flagged event is stamped with exact location and timestamp
- 📊 **Live Dashboard** — real-time drone position, violation feed, and risk score, all in one view
- 📄 **Auto-Generated Reports** — a full safety report waiting for you the moment the drone lands

---

## 🧠 How It Works

```
   Pixhawk (PX4) flies the mission  →  Pi Camera streams live video
              ↓                                    ↓
   GPS + telemetry via MAVLink  →  Raspberry Pi 5 runs YOLO inference
              ↓                                    ↓
                    Violation detected + geo-tagged
                                ↓
              Sent to ground station over WiFi/telemetry
                                ↓
        FastAPI backend stores it → React dashboard shows it live
```

Full architecture diagrams live in [`/docs/architecture`](./docs/architecture).

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Flight Controller | Pixhawk running **PX4**, simulated via **SITL** during development |
| Companion Computer | Raspberry Pi 5 + Pi Camera |
| Computer Vision | **YOLOv8** (Ultralytics), OpenCV |
| Flight ↔ Companion Link | `pymavlink` / MAVSDK-Python |
| Backend | **FastAPI**, WebSockets |
| Frontend | **React** + Leaflet/Mapbox |
| Database | PostgreSQL / MongoDB |
| Ground Control | QGroundControl |

---

## 🗺️ Project Roadmap

- [x] **Phase 1 — Software** *(Month 1)*: Simulated flight + CV detection + live dashboard + report generation, fully working end-to-end in a "digital twin"
- [ ] **Phase 2 — Hardware Assembly** *(Month 2)*: Frame build, flight controller setup, first manual flights
- [ ] **Phase 3 — Integration** *(Month 3)*: Real Pixhawk + onboard CV + live dashboard, all working together
- [ ] **Phase 4 — Field Testing** *(Month 4)*: Real-site testing, documentation, demo-ready

---

## 👥 Team

| Member | Role |
|---|---|
| **Padmaja** | CV/ML Engineer |
| **Rashi** | Flight Software Engineer |
| **Rachna** | Backend + Dashboard Engineer |
| **Aarthi** | Ground Operations, Compliance & Documentation Lead |

---

## 📁 Repository Structure

```
skyguard-ai/
├── cv-model/          # dataset, training notebooks, weights, inference scripts
├── flight-software/    # PX4 SITL setup, mission scripts, MAVLink client
├── backend/            # FastAPI app — violations, telemetry, reports
├── frontend/           # React dashboard — live map, video, violation feed
├── docs/               # logbook, reports, compliance docs, architecture diagrams
└── hardware/           # BOM, wiring diagrams, build log
```

Each folder has its own README with setup instructions for that piece.

---

## 🚀 Getting Started

1. Clone the repo: `git clone https://github.com/<your-org>/skyguard-ai.git`
2. Pick a component to run — head into `/cv-model`, `/flight-software`, `/backend`, or `/frontend` and follow that folder's README
3. Check `/docs/architecture` for the full system design before diving into code

---

<div align="center">

*Built with curiosity, a lot of debugging, and zero patience for preventable accidents.*

</div>
