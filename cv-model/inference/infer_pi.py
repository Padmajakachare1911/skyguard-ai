"""
Edge inference for Raspberry Pi 5 (#61 PARTIAL-SIM until real Pi camera + Pixhawk GPS).

Usage (on Pi or dev machine):
  python -m inference.infer_pi \\
    --video datasets/proxy/construction_sample.mp4 \\
    --model models/full_v2/best.pt \\
    --gps stub \\
    --imgsz 416 --frame-skip 1
"""

from __future__ import annotations

import argparse
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2

try:
    from ultralytics import YOLO
except ImportError as e:
    raise SystemExit("ultralytics required") from e

from inference.gps_provider import GpsProvider, MavlinkGps, StubGps
from inference.infer_video import (
    CLASS_NAMES,
    CONFIDENCE_THRESHOLD,
    DIRECT_VIOLATION_CLASSES,
    PERSON_DOWN_THRESHOLD,
    PROXIMITY_THRESHOLD_PX,
    draw_bbox,
    make_violation_event,
)
from inference.person_down import detect_person_down
from geofence.proximity_check import is_machinery_proximity_violation_pixels
from geofence.restricted_zone import SAMPLE_ZONES, is_in_restricted_zone


def build_gps(mode: str) -> GpsProvider:
    if mode == "mavlink":
        return MavlinkGps()
    return StubGps()


def run_pi_inference(
    video_path: str,
    model_path: str,
    output_jsonl: str,
    gps_mode: str = "stub",
    imgsz: int = 416,
    frame_skip: int = 1,
    max_frames: int | None = None,
) -> dict:
    model = YOLO(model_path)
    gps = build_gps(gps_mode)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(video_path)

    Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)
    events = []
    frame_idx = 0
    processed = 0
    t0 = time.time()

    with open(output_jsonl, "w") as jf:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if max_frames and frame_idx >= max_frames:
                break
            if frame_idx % frame_skip != 0:
                frame_idx += 1
                continue

            ts = datetime.now(timezone.utc)
            fix = gps.get_fix(ts)

            results = model.predict(frame, conf=CONFIDENCE_THRESHOLD, imgsz=imgsz, verbose=False)
            persons, machinery = [], []

            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    bbox = tuple(box.xyxy[0].tolist())
                    cls_name = CLASS_NAMES.get(cls_id, f"c{cls_id}")

                    if cls_name in DIRECT_VIOLATION_CLASSES:
                        ev = make_violation_event(cls_name, conf, f"pi/frame_{frame_idx}.jpg",
                                                  fix.lat, fix.lon)
                        jf.write(__import__("json").dumps(ev) + "\n")
                        events.append(ev)

                    if cls_name == "person":
                        persons.append((bbox, conf))
                        if detect_person_down(bbox, PERSON_DOWN_THRESHOLD):
                            ev = make_violation_event("person-down", conf, f"pi/frame_{frame_idx}.jpg",
                                                      fix.lat, fix.lon)
                            jf.write(__import__("json").dumps(ev) + "\n")
                            events.append(ev)
                        for _, zone in SAMPLE_ZONES.items():
                            if is_in_restricted_zone(fix.lat, fix.lon, zone):
                                ev = make_violation_event(
                                    "restricted-zone-entry", conf, f"pi/frame_{frame_idx}.jpg",
                                    fix.lat, fix.lon,
                                )
                                jf.write(__import__("json").dumps(ev) + "\n")
                                events.append(ev)
                                break

                    if cls_name == "machinery":
                        machinery.append((bbox, conf))

            for p_bbox, p_conf in persons:
                for m_bbox, _ in machinery:
                    if is_machinery_proximity_violation_pixels(
                        p_bbox, m_bbox, PROXIMITY_THRESHOLD_PX
                    ):
                        ev = make_violation_event(
                            "machinery-proximity", p_conf, f"pi/frame_{frame_idx}.jpg",
                            fix.lat, fix.lon,
                        )
                        jf.write(__import__("json").dumps(ev) + "\n")
                        events.append(ev)

            processed += 1
            frame_idx += 1

    cap.release()
    elapsed = time.time() - t0
    fps = processed / elapsed if elapsed > 0 else 0.0
    is_pi = "raspberry" in platform.platform().lower() or Path("/proc/device-tree/model").exists()
    label = "Raspberry Pi" if is_pi else "NOT PI 5 — indicative only"
    report = Path(output_jsonl).parent / "week10_pi_fps_benchmark.md"
    report.write_text(
        f"# Week 10 — Pi FPS Benchmark\n\n"
        f"**Device label:** {label}\n\n"
        f"| Metric | Value |\n|---|---|\n"
        f"| Model | `{model_path}` |\n"
        f"| imgsz | {imgsz} |\n"
        f"| frame_skip | {frame_skip} |\n"
        f"| Frames processed | {processed} |\n"
        f"| Elapsed (s) | {elapsed:.2f} |\n"
        f"| FPS | {fps:.2f} |\n"
        f"| GPS mode | {gps_mode} |\n"
        f"| Violation events | {len(events)} |\n\n"
        f"Re-run on Pi 5: `python -m inference.infer_pi --video <clip> --model models/full_v2/best.pt --gps mavlink`\n",
        encoding="utf-8",
    )
    print(f"[infer_pi] {processed} frames, {fps:.2f} FPS ({label})")
    return {"fps": fps, "events": len(events), "device_label": label}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--output", default="reports/pi_violations.jsonl")
    ap.add_argument("--gps", choices=("stub", "mavlink"), default="stub")
    ap.add_argument("--imgsz", type=int, default=416)
    ap.add_argument("--frame-skip", type=int, default=1)
    ap.add_argument("--max-frames", type=int, default=None)
    args = ap.parse_args()
    run_pi_inference(
        args.video, args.model, args.output, args.gps, args.imgsz, args.frame_skip, args.max_frames
    )
