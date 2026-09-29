# SkyGuard AI — CV/ML Track Status

**Last audit:** 2026-09-29  
**Track owner:** Padmaja

---

## Assumptions

- Training epochs reduced to 40 (from 80–100) with `patience=10` due to compressed 3–4 day timeline; logged per execution prompt §4.
- No local GPU (CUDA unavailable); all training runs on CPU unless Colab is used manually.
- Rachna's backend uses `latitude`/`longitude` (not `lat`/`lon`) and auto-int `id`; CV pipeline emits both field sets plus uuid4 `id` for traceability.
- Live webcam FPS test (#44) may use `--max-seconds` fallback if no camera is attached in CI/agent environment.

---

## Issue Status Table

| Issue | Status | Evidence | Notes |
|-------|--------|----------|-------|
| #1 | DONE | `requirements.txt`, ultralytics 8.4.165 installs | Environment verified 2026-09-29 |
| #2 | DONE | `notebooks/train_template.ipynb` | Colab scaffold present |
| #3 | DONE | `datasets/raw/*`, `class_mapping.md`, `final_class_list.txt`, merged 12k+ images | 3 Roboflow datasets merged |
| #14 | DONE | `models/ppe_v1/best.pt`, `reports/week2_ppe_v1_metrics.md` | mAP50=0.816 from real val run |
| #15 | DONE | `datasets/merged/` 8883 train / 2538 val / 1270 test | Augmented via Roboflow exports |
| #22 | DONE | `geofence/restricted_zone.py`, 7 pytest cases pass | |
| #23 | DONE | `reports/sample_violations.jsonl`, `inference/mock_backend.py`, push test in `tests/test_infer_push.py` | Live push to Rachna's API not yet exercised in prod |
| #32 | TODO-INDEP | `inference/person_down.py` | `full_v1/best.pt` + metrics pending |
| #39 | TODO-INDEP | — | `full_v2/best.pt` + hard-conditions report pending |
| #44 | TODO-INDEP | `inference/infer_live.py` | FPS log pending |
| #49 | DONE | `geofence/proximity_check.py`, `tests/test_geofence.py`, `reports/week7_geofence_test_results.md` | 19/19 pytest pass |
| #55 | BLOCKED | — | No real flight footage in repo |
| #58 | BLOCKED | — | No real flight footage + labels |
| #61 | BLOCKED | — | No Pi 5 + Pixhawk GPS + mounted camera |
| #65 | BLOCKED | — | Depends on #55/#58 real failure patterns |
| #66 | BLOCKED | — | No multi-condition real flights |

---

## Dependency Status Table

| Dependency | Owner | Evidence found (file/commit) | Status |
|------------|-------|------------------------------|--------|
| POST /violations API | Rachna | `backend/app/routers/violations.py`, commit `27eaa82` | AVAILABLE |
| WebSocket live feed | Rachna | No WebSocket in `backend/` | MISSING |
| MAVLink GPS client (lat/lon/timestamp) | Rashi | `flight-software/telemetry_reader.py`, `issue 24/telemetry_geofence.py` — SITL only, prints lat/lon | PARTIAL |
| Real Pixhawk GPS (#43/#48) | Rashi | No commits matching #43/#48; SITL telemetry only | MISSING |
| Real flight logs / video (#52) | Rashi/Aarthi | No `.mp4`/footage in repo; no #52 commit | MISSING |
| Assembled drone + Pi camera (#37/#42) | Aarthi | `hardware/` empty | MISSING |
| Field testing checklist (#53) | Aarthi | Not found in `docs/` | MISSING |
| Live CV pipeline (#50/#56) | Rachna | Backend GET/POST only; no WS or live ingest | PARTIAL |

---

## Schema Mismatch Flag

| Field | CV §2.2 spec | Rachna backend (`ViolationCreate`) |
|-------|-------------|-------------------------------------|
| id | uuid4 string | auto-int (server-generated) |
| lat/lon | required | uses `latitude`/`longitude` instead |
| timestamp | ISO-8601 Z string | datetime |

Adapter in `inference/adapters.py` strips uuid/id and maps lat/lon → latitude/longitude for POST.

---

## Git Commits (CV track)

| Commit | Issues |
|--------|--------|
| `cd81b55` | #14 ppe_v1 metrics + STATUS |
| `ff276b6` | #3 #15 dataset merge |
| `ebbc838` | #1 #2 #3 #14 #22 #23 #32 #39 #44 #49 bulk scaffold |

---

## Pending Real-Data Re-runs

- [ ] #55/#58: Re-run `inference/eval_footage.py` on footage in `datasets/flight_raw/` when Rashi/Aarthi upload it
- [ ] #61: Re-benchmark `infer_pi.py` on Pi 5 with real MAVLink GPS
- [ ] #65: Retrain `field_v1` on real flight failure crops
- [ ] #66: Fill matrix cells marked NOT TESTED with real multi-flight data
- [ ] #23: Test `--post-url` against Rachna's live backend (core JSONL path is independent)
