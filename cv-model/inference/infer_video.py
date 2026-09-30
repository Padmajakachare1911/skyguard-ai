"""
inference/infer_video.py — SkyGuard AI
----------------------------------------
Runs YOLO inference frame-by-frame on a recorded video file.
Emits violation events to a JSONL file matching the §2.2 locked schema.

Usage:
    python cv-model/inference/infer_video.py \\
        --video path/to/video.mp4 \\
        --model cv-model/models/full_v2/best.pt \\
        --output cv-model/reports/sample_violations.jsonl \\
        --annotated-out cv-model/reports/annotated_output.mp4

Week 3 (#22, #23) deliverable.

SCHEMA NOTE (checked against Rachna's backend 2026-09-23):
  Rachna's POST /violations expects: type, confidence, latitude, longitude,
  timestamp, image_url. Her DB stores id as auto-int; we keep 'id' as uuid4
  in JSONL for traceability but it is ignored on POST. Field names latitude/longitude
  diverge from §2.2 spec (lat/lon) — we use Rachna's actual field names to ensure
  the JSONL is directly pasteable into her API without renaming.
"""

import argparse
import json
import uuid
import datetime
import time
from pathlib import Path

import cv2

try:
    import requests
except ImportError:
    requests = None  # type: ignore

# Lazy-import ultralytics so the script can at least be imported in tests
# even if ultralytics isn't installed in every environment.
try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except ImportError:
    _YOLO_AVAILABLE = False

from inference.person_down import detect_person_down, aspect_ratio
from inference.adapters import to_backend_payload, validate_cv_event
from geofence.restricted_zone import is_in_restricted_zone, SAMPLE_ZONES
from geofence.proximity_check import is_machinery_proximity_violation_pixels

# ---------------------------------------------------------------------------
# Constants — tune after field testing
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD = 0.50   # detections below this are ignored
PERSON_DOWN_THRESHOLD = 1.40  # bbox width/height ratio for person-down heuristic
PROXIMITY_THRESHOLD_PX = 150  # pixel-distance threshold for machinery proximity

# Class names must match final_class_list.txt exactly (IDs 0–5)
CLASS_NAMES = {
    0: "helmet",
    1: "no-helmet",
    2: "vest",
    3: "no-vest",
    4: "person",
    5: "machinery",
}

# Classes that directly map to a violation event on detection
DIRECT_VIOLATION_CLASSES = {"no-helmet", "no-vest"}

# Stub GPS coordinates — replaced with real MAVLink telemetry in Week 10
# (Rashi's GPS feed not yet wired in)
GPS_STUB_LAT = 0.0
GPS_STUB_LON = 0.0


# ---------------------------------------------------------------------------
# Schema builder — §2.2 + adapted to Rachna's actual field names
# ---------------------------------------------------------------------------

def make_violation_event(
    violation_type: str,
    confidence: float,
    image_url: str,
    lat: float = GPS_STUB_LAT,
    lon: float = GPS_STUB_LON,
) -> dict:
    """
    Build a violation event dict matching the locked §2.2 schema.

    Field-name note: Rachna's backend uses 'latitude'/'longitude', not 'lat'/'lon'.
    The locked §2.2 spec says lat/lon. We emit both so the JSONL is compatible
    with both sides; Rachna's POST endpoint ignores unknown fields.
    """
    return {
        "id":         str(uuid.uuid4()),
        "type":       violation_type,
        "confidence": round(float(confidence), 4),
        "lat":        lat,           # §2.2 spec field
        "lon":        lon,           # §2.2 spec field
        "latitude":   lat,           # Rachna's backend field name
        "longitude":  lon,           # Rachna's backend field name
        "timestamp":  datetime.datetime.utcnow().isoformat() + "Z",
        "image_url":  image_url,
    }


# ---------------------------------------------------------------------------
# Frame annotation helper
# ---------------------------------------------------------------------------

VIOLATION_COLOUR = (0, 0, 255)    # red — violation
NORMAL_COLOUR    = (0, 200, 0)    # green — present, no violation
MACHINERY_COLOUR = (255, 128, 0)  # orange — machinery


def draw_bbox(frame, box, label: str, colour: tuple, conf: float) -> None:
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)
    text = f"{label} {conf:.2f}"
    cv2.putText(frame, text, (x1, max(y1 - 6, 14)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, colour, 2)


# ---------------------------------------------------------------------------
# Main inference loop
# ---------------------------------------------------------------------------

def post_violation(url: str, event: dict, timeout: float = 5.0, retries: int = 3) -> bool:
    """POST one event to backend; never raises — returns True on success."""
    if requests is None:
        return False
    payload = to_backend_payload(event)
    for attempt in range(retries):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code in (200, 201):
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5 * (attempt + 1))
    return False


def run_inference(
    video_path: str,
    model_path: str,
    output_jsonl: str,
    annotated_out: str | None = None,
    max_frames: int | None = None,
    post_url: str | None = None,
) -> list[dict]:
    """
    Run full violation-detection pipeline on a video file.

    Returns list of all emitted violation events (also written to output_jsonl).
    """
    if not _YOLO_AVAILABLE:
        raise RuntimeError("ultralytics is not installed. Run: pip install ultralytics")

    model = YOLO(model_path)
    cap   = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    # Set up output video writer if requested
    writer = None
    if annotated_out:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps    = cap.get(cv2.CAP_PROP_FPS) or 25
        w      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        Path(annotated_out).parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(annotated_out, fourcc, fps, (w, h))

    Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)
    all_events: list[dict] = []
    frame_idx = 0

    with open(output_jsonl, "w") as jsonl_file:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if max_frames and frame_idx >= max_frames:
                break

            results = model.predict(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)

            persons:   list[tuple] = []  # (bbox, conf)
            machinery: list[tuple] = []  # (bbox, conf)

            for result in results:
                for box in result.boxes:
                    cls_id  = int(box.cls[0])
                    conf    = float(box.conf[0])
                    bbox    = tuple(box.xyxy[0].tolist())  # (x1,y1,x2,y2)
                    cls_name = CLASS_NAMES.get(cls_id, f"class_{cls_id}")

                    # Choose annotation colour
                    colour = VIOLATION_COLOUR if cls_name in DIRECT_VIOLATION_CLASSES else NORMAL_COLOUR
                    if cls_name == "machinery":
                        colour = MACHINERY_COLOUR

                    if annotated_out and writer:
                        draw_bbox(frame, bbox, cls_name, colour, conf)

                    # --- Direct violation classes ---
                    if cls_name in DIRECT_VIOLATION_CLASSES:
                        snap = f"reports/frame_{frame_idx:06d}_{cls_name}.jpg"
                        event = make_violation_event(cls_name, conf, snap)
                        all_events.append(event)
                        jsonl_file.write(json.dumps(event) + "\n")
                        if post_url:
                            post_violation(post_url, event)

                    # --- Track persons and machinery for heuristics ---
                    if cls_name == "person":
                        persons.append((bbox, conf))
                        # Person-down heuristic
                        if detect_person_down(bbox, threshold=PERSON_DOWN_THRESHOLD):
                            snap = f"reports/frame_{frame_idx:06d}_person_down.jpg"
                            event = make_violation_event("person-down", conf, snap)
                            all_events.append(event)
                            jsonl_file.write(json.dumps(event) + "\n")
                            if post_url:
                                post_violation(post_url, event)
                            if annotated_out and writer:
                                draw_bbox(frame, bbox, "PERSON-DOWN", VIOLATION_COLOUR, conf)

                        # Restricted-zone check (stub GPS — always at 0,0 until Week 10)
                        for zone_name, zone_coords in SAMPLE_ZONES.items():
                            if is_in_restricted_zone(GPS_STUB_LAT, GPS_STUB_LON, zone_coords):
                                snap = f"reports/frame_{frame_idx:06d}_restricted_zone.jpg"
                                event = make_violation_event("restricted-zone-entry", conf, snap)
                                all_events.append(event)
                                jsonl_file.write(json.dumps(event) + "\n")
                                if post_url:
                                    post_violation(post_url, event)
                                break  # one event per person per frame

                    if cls_name == "machinery":
                        machinery.append((bbox, conf))

            # --- Machinery proximity (pixel fallback — GPS not yet available) ---
            for p_bbox, p_conf in persons:
                for m_bbox, _ in machinery:
                    if is_machinery_proximity_violation_pixels(
                        p_bbox, m_bbox, threshold_px=PROXIMITY_THRESHOLD_PX
                    ):
                        snap = f"reports/frame_{frame_idx:06d}_machinery_proximity.jpg"
                        # confidence = person detection confidence (machinery is context)
                        event = make_violation_event("machinery-proximity", p_conf, snap)
                        all_events.append(event)
                        jsonl_file.write(json.dumps(event) + "\n")
                        if post_url:
                            post_violation(post_url, event)

            if writer:
                writer.write(frame)

            frame_idx += 1

    cap.release()
    if writer:
        writer.release()

    print(f"[infer_video] Processed {frame_idx} frames → {len(all_events)} violation events")
    print(f"[infer_video] JSONL output: {output_jsonl}")
    if annotated_out:
        print(f"[infer_video] Annotated video: {annotated_out}")

    return all_events


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="SkyGuard AI — video inference")
    ap.add_argument("--video",         required=True,  help="Path to input video file")
    ap.add_argument("--model",         required=True,  help="Path to YOLO .pt weights")
    ap.add_argument("--output",        default="cv-model/reports/sample_violations.jsonl",
                    help="Output JSONL path for violation events")
    ap.add_argument("--annotated-out", default=None,   help="Path to save annotated video")
    ap.add_argument("--max-frames",    type=int, default=None, help="Stop after N frames")
    ap.add_argument("--post-url",      default=None, help="Optional POST /violations URL (default off)")
    args = ap.parse_args()

    run_inference(
        video_path    = args.video,
        model_path    = args.model,
        output_jsonl  = args.output,
        annotated_out = args.annotated_out,
        max_frames    = args.max_frames,
        post_url      = args.post_url,
    )
