# Week 2 — PPE v1 Model Metrics

**Issue:** #14 — Train first-pass YOLO PPE detection model  
**Date:** 2026-09-29  
**Model:** `cv-model/models/ppe_v1/best.pt` (YOLOv8n fine-tuned)  
**Dataset:** `datasets/merged_ppe_v1` (4 classes: helmet, no-helmet, vest, no-vest)  
**Training:** 100 epochs, imgsz=640, batch=16, CPU (see `runs/detect/ppe_v1/`)  
**Validation command:** `yolo detect val model=models/ppe_v1/best.pt data=datasets/merged_ppe_v1/data.yaml`

## Overall Metrics (val set, 2504 images, 8384 instances)

| Metric | Value |
|--------|-------|
| mAP@0.5 | **0.816** |
| mAP@0.5:0.95 | **0.556** |
| Precision | **0.842** |
| Recall | **0.794** |

## Per-Class Metrics

| Class | Images | Instances | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|-------|--------|-----------|-----------|--------|---------|--------------|
| helmet | 2130 | 5052 | 0.927 | 0.936 | 0.956 | 0.644 |
| no-helmet | 414 | 1621 | 0.890 | 0.829 | 0.886 | 0.598 |
| vest | 902 | 1356 | 0.914 | 0.896 | 0.941 | 0.731 |
| no-vest | 188 | 355 | 0.638 | 0.515 | 0.480 | 0.249 |

## Notes

- `no-vest` is the weakest class (mAP@0.5 = 0.48); targeted augmentation in #15 expanded the merged dataset.
- Inference speed on CPU: ~45 ms/image (validation run, batch=16).
- Weights saved at `models/ppe_v1/best.pt` (6.2 MB).

## Definition of Done

- [x] Trained checkpoint exists at `models/ppe_v1/best.pt`
- [x] mAP/precision/recall recorded with real validation run numbers
- [x] Dataset includes non-ideal lighting/clutter (Roboflow construction-site exports)
