# Week 6 — Live Camera FPS Log

**Date:** 2026-09-30 14:21 UTC

| Parameter | Value |
|---|---|
| Model | `models/full_v2/best.pt` |
| Source | `datasets/proxy/construction_sample.mp4` |
| Frames processed | 60 |
| Total runtime (s) | 6.1 |
| Average FPS | 31.92 |
| Min FPS | 0.24 |
| Max FPS | 53.96 |

**Adequate for real-time use (>= 15 FPS):** Yes

## Mitigation if FPS is insufficient

1. Lower `imgsz` to 320
2. Add frame-skipping (process every 2nd frame)
3. Export to ONNX or NCNN format for faster CPU inference
4. If Pi 5 CPU still insufficient: flag Hailo-8 AI HAT to Aarthi for procurement
