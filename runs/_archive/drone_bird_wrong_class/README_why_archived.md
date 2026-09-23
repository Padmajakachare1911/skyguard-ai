# Archived: drone/bird wrong-class model (skyguard_real)

**Archived:** 2026-09-23  
**Do not use these weights for inference or deployment.**

## What happened

`train_real.py` pointed at `cv-model/datasets/data/data.yaml`, which contained an aerial
object-detection dataset (drone, bird, and 9 unnamed classes — IDs 0–10).  
This was **not** the SkyGuard PPE dataset. The model trained 50 epochs on the wrong data.

## Root cause

- The `datasets/data/` folder was populated locally (never committed to git) with a
  Roboflow aerial-object dataset, not the required PPE/construction dataset.
- `train_real.py` had no class-name assertion guard — it trained whatever `data.yaml`
  pointed at without validating the class names.

## What was trained (wrong)

- Classes: `drone, bird, class_2 … class_10` (11 classes)
- Images: 1132 train / 143 val / 141 test
- Epochs: 50 | Final mAP50: 0.567

## What should have been trained

Classes: `helmet, no-helmet, vest, no-vest, person, machinery`  
See `cv-model/datasets/final_class_list.txt` for the locked list.

## Fix applied going forward

All training scripts now assert class names against `final_class_list.txt` before
calling `model.train()`.
