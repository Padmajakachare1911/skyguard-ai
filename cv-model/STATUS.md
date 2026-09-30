# SkyGuard AI — CV/ML Track Status

**Last audit:** 2026-09-30  
**Track owner:** Padmaja

---

## Assumptions

- Training epochs reduced to 40 (from 80–100) with `patience=10` due to compressed 3–4 day timeline; logged per execution prompt §4.
- Local RTX 3050 GPU (`.venv-gpu`); `full_v1` / `full_v2` trained locally (40 epochs, patience=10).
- Rachna's backend uses `latitude`/`longitude` (not `lat`/`lon`) and auto-int `id`; CV pipeline emits both field sets plus uuid4 `id` for traceability.
- Live FPS (#44): `--source datasets/proxy/construction_sample.mp4 --no-display --max-seconds 30` when no webcam.

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
| #32 | DONE | `models/full_v1/best.pt`, `inference/person_down.py`, `reports/week4_full_v1_metrics.md` | mAP50=0.694; person-down in live/video pipeline |
| #39 | DONE | `models/full_v2/best.pt`, `reports/week5_full_v2_metrics.md`, `reports/week5_hard_conditions_metrics.md` | mAP50=0.687; hard/clean proxy eval |
| #44 | DONE | `inference/infer_live.py`, `reports/week6_live_fps_log.md` | ~32 FPS avg on proxy video (GPU dev machine) |
| #49 | DONE | `geofence/proximity_check.py`, `tests/test_geofence.py`, `reports/week7_geofence_test_results.md` | 25/25 pytest pass |
| #55 | PARTIAL-SIM | `inference/eval_footage.py`, `reports/week9_fp_fn_summary.md` | Proxy test-set eval; re-run on `datasets/flight_raw/` |
| #58 | PARTIAL-SIM | `reports/week9_fp_fn.csv`, `reports/fp_fn_crops/` | Same proxy run; needs real flight labels |
| #61 | PARTIAL-SIM | `inference/infer_pi.py`, `reports/week10_pi_fps_benchmark.md` | Dev-machine proxy; re-benchmark on Pi 5 + MAVLink |
| #65 | BLOCKED | `scripts/merge_field_data.py` | No real failure crops yet |
| #66 | PARTIAL-SIM | `inference/run_matrix.py`, `reports/week12_multi_condition_matrix.md` | Proxy matrix; dusk clip NOT TESTED |

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

- [x] Proxy #55/#58/#66: `eval_footage`, `run_matrix` on merged test + `construction_sample.mp4` (2026-09-30)
- [x] Proxy #61: `infer_pi.py` on dev GPU (2026-09-30)
- [ ] #55/#58: Re-run `eval_footage` on `datasets/flight_raw/` when Rashi/Aarthi upload it
- [ ] #61: Re-benchmark `infer_pi.py` on Pi 5 with real MAVLink GPS
- [ ] #65: Retrain `field_v1` on real flight failure crops
- [ ] #66: Replace NOT TESTED matrix cells with real multi-flight clips
- [ ] #23: Test `--post-url` against Rachna's live backend (core JSONL path is independent)
