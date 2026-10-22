# SkyGuard AI — CV/ML Track

**Track owner:** Padmaja  
**Stack:** YOLOv8n · OpenCV · Shapely · Roboflow · Google Colab

---

## Workflow

1. **Roboflow:** upload PPE images, annotate helmets/vests, create dataset versions.
2. **Train** with Ultralytics (Colab/local) on the Roboflow export, then export the weights (`best.pt`, or NCNN/ONNX for faster Raspberry Pi 4 CPU inference) and copy them to the Pi.
3. **Raspberry Pi 4:** run local YOLO inference on the CSI camera feed. No cloud request for any frame.
4. **Violation detected:** the Pi sends ONLY the violation snapshot image and its metadata to the laptop over Wi-Fi (`inference/laptop_client.py`).
5. **Laptop FastAPI backend:** saves the evidence in `backend/snapshots`, stores the violation in the DB, and broadcasts it on `/ws/violations`.
6. **Dashboard:** shows the alert with timestamp, violation type, and GPS coordinates if available.

### Run on Pi

```bash
python -m inference.infer_pi --source csi --model weights/best.pt --gps stub --send --backend http://<LAPTOP_IP>:8000
```

- `--backend` defaults to the `SKYGUARD_BACKEND` env var. `--gps mavlink` uses the Pixhawk fix; with `stub`/no fix, `0.0` is sent and the backend uses telemetry when available.
- Per violation: JPEG is saved to `reports/pi_snapshots/`, uploaded to `POST /violations/upload-snapshot`, then metadata is POSTed to `POST /violations` with `image_url` set to the returned bare filename. Same-type violations are throttled (5 s cooldown); unreachable-laptop sends are queued and retried, never blocking inference.
- Laptop checklist: `run_backend.bat` binds `0.0.0.0:8000` (CORS open); allow inbound TCP 8000 in Windows Firewall; Pi and laptop on the same Wi-Fi.

---

## Quick Start — Run Inference

### On a recorded video file
```bash
cd skyguard-ai
pip install -r cv-model/requirements.txt

python -m cv-model.inference.infer_video \
  --video  path/to/construction_site.mp4 \
  --model  cv-model/models/full_v2/best.pt \
  --output cv-model/reports/sample_violations.jsonl \
  --annotated-out cv-model/reports/annotated_output.mp4
```

### On a live webcam
```bash
python -m cv-model.inference.infer_live \
  --model  cv-model/models/full_v2/best.pt \
  --camera 0
# Press 'q' to quit. FPS log auto-written to cv-model/reports/week6_live_fps_log.md
```

---

## Final Model Location

| Model | Path | Trained on | Use |
|---|---|---|---|
| `ppe_v1` | `cv-model/models/ppe_v1/best.pt` | Merged PPE datasets, 100 epochs | Helmet + vest detection only |
| `full_v1` | `cv-model/models/full_v1/best.pt` | + machinery class, 80 epochs fine-tune | Full detection incl. machinery |
| `full_v2` | `cv-model/models/full_v2/best.pt` | + hard-conditions augmentation, 60 epochs | **Primary inference model** |
| `field_v1` | `cv-model/models/field_v1/best.pt` | + field-failure fixes, Week 11 | Post-flight-test refinement |

> **Note:** Model weights are not committed to git (too large). Download from Google Drive after Colab training. See `notebooks/train_template.ipynb` Cell 11 for the Drive path.

---

## Final Class List

The YOLO model detects these 6 classes (see `datasets/final_class_list.txt`):

| YOLO ID | Class | Produces violation event |
|---|---|---|
| 0 | `helmet` | No — presence only |
| 1 | `no-helmet` | ✅ `no-helmet` |
| 2 | `vest` | No — presence only |
| 3 | `no-vest` | ✅ `no-vest` |
| 4 | `person` | ✅ `person-down` (heuristic) · `restricted-zone-entry` (geofence) · `machinery-proximity` (geofence) |
| 5 | `machinery` | Context for proximity check |

### 5 locked violation types (§2.2 schema)
`no-helmet` · `no-vest` · `person-down` · `restricted-zone-entry` · `machinery-proximity`

---

## Violation Event Schema

Every event emitted by the inference pipeline matches this shape:

```json
{
  "id":        "uuid4-string",
  "type":      "no-helmet",
  "confidence": 0.87,
  "lat":        0.0,
  "lon":        0.0,
  "latitude":   0.0,
  "longitude":  0.0,
  "timestamp":  "2026-08-05T10:32:11Z",
  "image_url":  "relative/path/to/snapshot.jpg"
}
```

> `lat`/`lon` come from the GPS provider (`--gps stub` gives `0.0`; `--gps mavlink` uses the live fix).  
> `latitude`/`longitude` are duplicate fields matching Rachna's backend schema (`POST /violations`).

---

## Folder Structure

```
cv-model/
  datasets/
    raw/                  # Downloaded Roboflow datasets (not committed)
    merged/               # Unified training dataset (not committed — large)
    class_mapping.md      # Maps raw class names to locked violation classes
    final_class_list.txt  # 6 YOLO training classes, one per line
  notebooks/
    train_template.ipynb  # Colab notebook — run this to train all phases
  models/
    ppe_v1/best.pt        # Week 2 checkpoint (not committed — download from Drive)
    full_v1/best.pt       # Week 4 checkpoint
    full_v2/best.pt       # Week 5 checkpoint (primary)
    field_v1/best.pt      # Week 11 checkpoint
  inference/
    infer_video.py        # Run on a recorded video file
    infer_live.py         # Run on live webcam
    person_down.py        # Person-down aspect-ratio heuristic
  geofence/
    restricted_zone.py    # Shapely polygon check for restricted zones
    proximity_check.py    # Haversine GPS + pixel-distance proximity check
  tests/
    test_geofence.py      # pytest suite (25 tests, all passing)
  reports/                # Metrics, JSONL events, test results
  requirements.txt        # Pinned dependencies
```

---

## Running Tests

```bash
pytest cv-model/tests/ -v
# Expected: 25 passed, 0 failed
```

---

## Training (Colab — requires GPU)

1. Open `cv-model/notebooks/train_template.ipynb` in Google Colab
2. Runtime → Change runtime type → **T4 GPU**
3. Fill in `ROBOFLOW_API_KEY` in Cell 3
4. Run all cells top-to-bottom
5. Weights auto-saved to Google Drive; download to `cv-model/models/`

---

## Known Limitations (as of Week 9)

| Limitation | Impact | Mitigation |
|---|---|---|
| GPS stub is the default | `restricted-zone-entry` compares stub position | Use `--gps mavlink` on the Pi for real fixes |
| Pixel-distance fallback for proximity | Not geographically calibrated | GPS proximity replaces this in Week 10 |
| No real flight footage yet | Weeks 8–9 reports use proxy aerial video (Pexels CC0) | Replace with Rashi's footage when available |
| Model not yet benchmarked on Raspberry Pi 4 | FPS on Pi unknown | ONNX/NCNN export ready; benchmark on the Pi |
| `full_v2` trained on simulated data only | May miss altitude/blur patterns from real flight | Field fine-tuning in Week 11 |

---

## Progress Log

- `[#1 #2 #3]` Setup: venv, Colab notebook scaffold, Roboflow dataset sourcing plan
- `[#14]` Training notebook complete — run on Colab to produce `ppe_v1/best.pt`
- `[#22 #23]` `geofence/restricted_zone.py` + `inference/infer_video.py` written; JSONL schema verified
- `[#32]` `inference/person_down.py` (aspect-ratio heuristic) written
- `[#39]` Hard-conditions augmentation baked into `full_v2` training phase in Colab notebook
- `[#44]` `inference/infer_live.py` written; auto-writes FPS report on exit
- `[#49]` `geofence/proximity_check.py` + `tests/test_geofence.py` written; **25/25 pytest passing**
- `[#14]` `ppe_v1/best.pt` validated; metrics in `reports/week2_ppe_v1_metrics.md` (mAP50=0.816)
- `[#23]` End-to-end video inference → `reports/sample_violations.jsonl` + annotated clip; mock POST tested via pytest
- `[#32]` `full_v1/best.pt` + `reports/week4_full_v1_metrics.md` (mAP50=0.694)
- `[#39]` `full_v2/best.pt` + hard-conditions report (`reports/week5_hard_conditions_metrics.md`)
- `[#44]` Live/proxy FPS log in `reports/week6_live_fps_log.md`
- `[#55/#58/#61/#66]` Proxy reports: week9 FP/FN, week10 Pi benchmark, week12 matrix (SIMULATED until flight hardware)
