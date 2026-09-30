# Week 10 — Pi FPS Benchmark

**Device label:** NOT PI 5 — indicative only

| Metric | Value |
|---|---|
| Model | `models/full_v2/best.pt` |
| imgsz | 416 |
| frame_skip | 1 |
| Frames processed | 60 |
| Elapsed (s) | 5.25 |
| FPS | 11.44 |
| GPS mode | stub |
| Violation events | 38 |

Re-run on Pi 5: `python -m inference.infer_pi --video <clip> --model models/full_v2/best.pt --gps mavlink`
