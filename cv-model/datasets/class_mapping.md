# Class Mapping — SkyGuard AI PPE Datasets → Locked Violation Classes

This table maps raw Roboflow dataset class names to the 5 locked violation classes
defined in §2.1 of the project spec. The YOLO model is trained on the "YOLO class" column.

## Locked Violation Classes (§2.1)
`no-helmet`, `no-vest`, `restricted-zone-entry`, `machinery-proximity`, `person-down`

> **Note:** `restricted-zone-entry` and `machinery-proximity` are **not** YOLO classes —
> they are computed geometrically by `geofence/restricted_zone.py` and
> `geofence/proximity_check.py` respectively. `person-down` is a heuristic applied
> on top of the `person` YOLO class in `inference/person_down.py`.

## YOLO Training Classes (what the model actually detects)

| YOLO ID | YOLO Class | Violation Event Emitted | Raw Dataset Names (merged from) |
|---------|------------|-------------------------|----------------------------------|
| 0 | `helmet` | *(presence — no violation)* | `hardhat`, `hard-hat`, `helmet`, `Hardhat` |
| 1 | `no-helmet` | `no-helmet` violation | `no-hardhat`, `no-helmet`, `NO-Hardhat` |
| 2 | `vest` | *(presence — no violation)* | `safety-vest`, `vest`, `Safety Vest` |
| 3 | `no-vest` | `no-vest` violation | `no-vest`, `no-safety-vest`, `NO-Safety Vest` |
| 4 | `person` | triggers `person-down` heuristic | `person`, `Person`, `worker` |
| 5 | `machinery` | triggers `machinery-proximity` geofence | `machinery`, `excavator`, `crane`, `forklift`, `vehicle` |

## Violation Class Mapping (what infer_video.py emits)

| Detection | Condition | Violation Type Emitted |
|-----------|-----------|------------------------|
| `no-helmet` bbox | confidence ≥ 0.5 | `no-helmet` |
| `no-vest` bbox | confidence ≥ 0.5 | `no-vest` |
| `person` bbox | width/height ratio ≥ 1.4 | `person-down` |
| `person` GPS point | inside Shapely polygon | `restricted-zone-entry` |
| `person` + `machinery` bbox pair | pixel distance < threshold (fallback) or haversine < 5 m (GPS) | `machinery-proximity` |

## Datasets Sourced

| Local folder | Roboflow slug | Version | Train images (raw) | Mapped unified classes |
|--------------|---------------|---------|--------------------|-------------------------|
| `raw/hard-hat-workers` | `joseph-nelson/hard-hat-workers` | 2 | ~5,628 | `head`→no-helmet, `helmet`, `person` |
| `raw/construction-site-safety` | `roboflow-universe-projects/construction-site-safety` | 30 | ~573 | PPE + Person + vehicles→machinery |
| `raw/ppe-detection` | `testcasque/ppe-detection-qlq3d` | 1 | ~4,112 | helmet, no-helmet, vest, no-vest only |

**Merged output (after `scripts/merge_datasets.py`):** 12,691 images · 70/20/10 split ·  
`datasets/merged/data.yaml` (6 classes) · `datasets/merged_ppe_v1/data.yaml` (Week 2 four-class MVP).

Remapping is **by class name** from each export's `data.yaml` (see `scripts/merge_datasets.py`).
