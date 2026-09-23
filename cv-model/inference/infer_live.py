"""
inference/infer_live.py — SkyGuard AI
---------------------------------------
Live-camera inference via webcam (or any cv2.VideoCapture index/URL).
Displays annotated feed in a window, logs FPS, and emits violation events
using the same schema as infer_video.py.

Usage:
    python cv-model/inference/infer_live.py \\
        --model cv-model/models/full_v2/best.pt \\
        --camera 0 \\
        --output cv-model/reports/live_violations.jsonl

Press 'q' to quit the live window.

Week 6 (#44) deliverable.
"""

import argparse
import json
import time
from pathlib import Path

import cv2

try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except ImportError:
    _YOLO_AVAILABLE = False

# Reuse schema builder and helpers from infer_video
from inference.infer_video import (
    make_violation_event,
    draw_bbox,
    CLASS_NAMES,
    DIRECT_VIOLATION_CLASSES,
    CONFIDENCE_THRESHOLD,
    PERSON_DOWN_THRESHOLD,
    PROXIMITY_THRESHOLD_PX,
    GPS_STUB_LAT,
    GPS_STUB_LON,
)
from inference.person_down import detect_person_down
from geofence.restricted_zone import is_in_restricted_zone, SAMPLE_ZONES
from geofence.proximity_check import is_machinery_proximity_violation_pixels


def run_live(
    model_path: str,
    camera_index: int = 0,
    output_jsonl: str = "cv-model/reports/live_violations.jsonl",
    display: bool = True,
) -> None:
    """
    Run full violation-detection pipeline on a live camera feed.

    Args:
        model_path:   Path to YOLO .pt weights.
        camera_index: cv2.VideoCapture source (0 = default webcam).
        output_jsonl: Path to write violation events.
        display:      If True, show annotated video in a window.
    """
    if not _YOLO_AVAILABLE:
        raise RuntimeError("ultralytics is not installed. Run: pip install ultralytics")

    model = YOLO(model_path)
    cap   = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {camera_index}. "
                           "Try a different --camera value or check camera permissions.")

    Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)

    frame_count  = 0
    total_events = 0
    fps_history  = []
    start_time   = time.time()

    print(f"[infer_live] Camera {camera_index} opened. Press 'q' to quit.")

    with open(output_jsonl, "w") as jsonl_file:
        while True:
            t_frame = time.time()
            ret, frame = cap.read()
            if not ret:
                print("[infer_live] Frame read failed — camera disconnected?")
                break

            results = model.predict(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)

            persons:   list[tuple] = []
            machinery: list[tuple] = []

            for result in results:
                for box in result.boxes:
                    cls_id   = int(box.cls[0])
                    conf     = float(box.conf[0])
                    bbox     = tuple(box.xyxy[0].tolist())
                    cls_name = CLASS_NAMES.get(cls_id, f"class_{cls_id}")

                    colour = (0, 200, 0)
                    if cls_name in DIRECT_VIOLATION_CLASSES:
                        colour = (0, 0, 255)
                    elif cls_name == "machinery":
                        colour = (255, 128, 0)

                    if display:
                        draw_bbox(frame, bbox, cls_name, colour, conf)

                    if cls_name in DIRECT_VIOLATION_CLASSES:
                        snap = f"live_frame_{frame_count:06d}_{cls_name}.jpg"
                        event = make_violation_event(cls_name, conf, snap)
                        jsonl_file.write(json.dumps(event) + "\n")
                        total_events += 1

                    if cls_name == "person":
                        persons.append((bbox, conf))
                        if detect_person_down(bbox, threshold=PERSON_DOWN_THRESHOLD):
                            snap = f"live_frame_{frame_count:06d}_person_down.jpg"
                            event = make_violation_event("person-down", conf, snap)
                            jsonl_file.write(json.dumps(event) + "\n")
                            total_events += 1
                            if display:
                                draw_bbox(frame, bbox, "PERSON-DOWN", (0, 0, 255), conf)

                        for zone_name, zone_coords in SAMPLE_ZONES.items():
                            if is_in_restricted_zone(GPS_STUB_LAT, GPS_STUB_LON, zone_coords):
                                snap = f"live_frame_{frame_count:06d}_restricted_zone.jpg"
                                event = make_violation_event("restricted-zone-entry", conf, snap)
                                jsonl_file.write(json.dumps(event) + "\n")
                                total_events += 1
                                break

                    if cls_name == "machinery":
                        machinery.append((bbox, conf))

            for p_bbox, p_conf in persons:
                for m_bbox, _ in machinery:
                    if is_machinery_proximity_violation_pixels(
                        p_bbox, m_bbox, threshold_px=PROXIMITY_THRESHOLD_PX
                    ):
                        snap = f"live_frame_{frame_count:06d}_machinery_proximity.jpg"
                        event = make_violation_event("machinery-proximity", p_conf, snap)
                        jsonl_file.write(json.dumps(event) + "\n")
                        total_events += 1

            # FPS calculation
            elapsed = time.time() - t_frame
            fps = 1.0 / elapsed if elapsed > 0 else 0.0
            fps_history.append(fps)

            if display:
                fps_text = f"FPS: {fps:.1f}  Events: {total_events}"
                cv2.putText(frame, fps_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
                cv2.imshow("SkyGuard AI — Live Inference", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("[infer_live] 'q' pressed — stopping.")
                    break

            frame_count += 1

    cap.release()
    if display:
        cv2.destroyAllWindows()

    total_elapsed = time.time() - start_time
    avg_fps = sum(fps_history) / len(fps_history) if fps_history else 0.0
    min_fps = min(fps_history) if fps_history else 0.0
    max_fps = max(fps_history) if fps_history else 0.0

    print(f"\n[infer_live] Session summary")
    print(f"  Frames processed : {frame_count}")
    print(f"  Total runtime    : {total_elapsed:.1f} s")
    print(f"  Avg FPS          : {avg_fps:.2f}")
    print(f"  Min / Max FPS    : {min_fps:.2f} / {max_fps:.2f}")
    print(f"  Violation events : {total_events}")
    print(f"  JSONL output     : {output_jsonl}")

    # Write FPS summary to reports — Week 6 deliverable
    fps_report_path = Path(output_jsonl).parent / "week6_live_fps_log.md"
    _write_fps_report(fps_report_path, frame_count, total_elapsed, avg_fps, min_fps, max_fps,
                      model_path, camera_index)


def _write_fps_report(
    path: Path,
    frames: int,
    runtime: float,
    avg: float,
    lo: float,
    hi: float,
    model_path: str,
    camera: int,
) -> None:
    """Write Week 6 FPS log report."""
    import datetime
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(f"# Week 6 — Live Camera FPS Log\n\n")
        f.write(f"**Date:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write(f"| Parameter | Value |\n|---|---|\n")
        f.write(f"| Model | `{model_path}` |\n")
        f.write(f"| Camera index | {camera} |\n")
        f.write(f"| Frames processed | {frames} |\n")
        f.write(f"| Total runtime (s) | {runtime:.1f} |\n")
        f.write(f"| Average FPS | {avg:.2f} |\n")
        f.write(f"| Min FPS | {lo:.2f} |\n")
        f.write(f"| Max FPS | {hi:.2f} |\n\n")
        f.write(f"**Adequate for real-time use (≥ 15 FPS):** {'Yes' if avg >= 15 else 'No — see mitigation options'}\n\n")
        f.write("## Mitigation if FPS is insufficient\n\n")
        f.write("1. Lower `imgsz` to 320\n")
        f.write("2. Add frame-skipping (process every 2nd frame)\n")
        f.write("3. Export to ONNX or NCNN format for faster CPU inference\n")
        f.write("4. If Pi 5 CPU still insufficient: flag Hailo-8 AI HAT to Aarthi for procurement\n")
    print(f"[infer_live] FPS report written to {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="SkyGuard AI — live camera inference")
    ap.add_argument("--model",  required=True, help="Path to YOLO .pt weights")
    ap.add_argument("--camera", type=int, default=0, help="cv2.VideoCapture source index")
    ap.add_argument("--output", default="cv-model/reports/live_violations.jsonl",
                    help="JSONL output path for violation events")
    ap.add_argument("--no-display", action="store_true", help="Suppress video window (headless)")
    args = ap.parse_args()

    run_live(
        model_path   = args.model,
        camera_index = args.camera,
        output_jsonl = args.output,
        display      = not args.no_display,
    )
