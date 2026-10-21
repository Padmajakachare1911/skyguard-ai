"""
SkyGuard AI — Interactive Live Webcam PPE Detector
==================================================
Runs real-time PPE detection via your laptop webcam.
Forces window to top, displays prominent camera status,
centering reticle, live detection banners, and capture flash.

Controls:
  [m]       Cycle through models (10-class best_ppe_v1 <-> 4-class ppe_v1 <-> 6-class full_v2)
  [+] / [=] Increase confidence threshold
  [-]       Decrease confidence threshold
  [s]       Save screenshot to cv-model/reports/webcam_captures/
  [q] / ESC Quit
"""

import os
import sys
import time
from pathlib import Path

# Add project root and cv-model to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
CV_MODEL_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = CV_MODEL_DIR.parent
for p in (str(CV_MODEL_DIR), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import cv2
import numpy as np
import datetime
import threading

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

try:
    import winsound
    _WINSOUND = True
except ImportError:
    _WINSOUND = False

try:
    from ultralytics import YOLO
except ImportError:
    print("[ERROR] ultralytics is not installed. Run: pip install ultralytics")
    sys.exit(1)


# Dashboard connection & rate-limiting cooldown
BACKEND_API = os.environ.get("SKYGUARD_BACKEND_URL", "http://127.0.0.1:8000/violations")
_LAST_TRIGGER_TIMES = {}
TRIGGER_COOLDOWN_SECONDS = 3.0


def send_dashboard_alert_async(violation_type: str, confidence: float, snapshot_path: str = ""):
    """Dispatches a violation alert asynchronously without blocking the camera loop."""
    if not _REQUESTS_AVAILABLE:
        return

    def _worker():
        payload = {
            "person_id": "WORKER-LIVE",
            "type": violation_type,
            "confidence": round(float(confidence), 2),
            "latitude": 19.0332,
            "longitude": 73.0299,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "image_url": snapshot_path or f"{violation_type}.jpg"
        }
        try:
            requests.post(BACKEND_API, json=payload, timeout=1.0)
            print(f"  [DASHBOARD ALERT] Dispatched '{violation_type}' ({int(confidence * 100)}%) to {BACKEND_API}")
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


# Models available for cycling
MODEL_CANDIDATES = [
    {
        "name": "10-class PPE (best_ppe_v1.pt)",
        "path": PROJECT_ROOT / "cv-model" / "weights" / "best_ppe_v1.pt",
        "description": "Hardhat, Safety Vest, NO-Hardhat, NO-Safety Vest, Person...",
    },
    {
        "name": "4-class PPE (models/ppe_v1/best.pt)",
        "path": PROJECT_ROOT / "cv-model" / "models" / "ppe_v1" / "best.pt",
        "description": "helmet, no-helmet, vest, no-vest",
    },
    {
        "name": "6-class Full v2 (models/full_v2/best.pt)",
        "path": PROJECT_ROOT / "cv-model" / "models" / "full_v2" / "best.pt",
        "description": "helmet, vest, person, machinery, + violations",
    },
]


def get_class_color(class_name: str) -> tuple[int, int, int]:
    name_lower = class_name.lower().replace("_", "-").replace(" ", "-")
    # Red for violations
    if any(k in name_lower for k in ["no-helmet", "no-hardhat", "no-vest", "no-safety-vest", "no-mask"]):
        return (40, 40, 235)  # Crimson Red
    # Green for compliance
    if any(k in name_lower for k in ["hardhat", "helmet", "safety-vest", "vest", "mask"]):
        return (40, 210, 50)  # Bright Green
    # Cyan for persons
    if "person" in name_lower:
        return (235, 180, 20)  # Bright Cyan
    # Orange for machinery & vehicles
    if any(k in name_lower for k in ["machinery", "vehicle"]):
        return (20, 140, 240)  # Orange
    return (200, 200, 200)


def draw_styled_box(
    frame: np.ndarray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    label: str,
    color: tuple[int, int, int],
) -> None:
    # Outer box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

    # Corner brackets for HUD feel
    d = min(16, max(6, (x2 - x1) // 5), max(6, (y2 - y1) // 5))
    cv2.line(frame, (x1, y1), (x1 + d, y1), color, 3)
    cv2.line(frame, (x1, y1), (x1, y1 + d), color, 3)
    cv2.line(frame, (x2, y1), (x2 - d, y1), color, 3)
    cv2.line(frame, (x2, y1), (x2, y1 + d), color, 3)
    cv2.line(frame, (x1, y2), (x1 + d, y2), color, 3)
    cv2.line(frame, (x1, y2), (x1, y2 - d), color, 3)
    cv2.line(frame, (x2, y2), (x2 - d, y2), color, 3)
    cv2.line(frame, (x2, y2), (x2, y2 - d), color, 3)

    # Label badge
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness = 1
    (text_w, text_h), _ = cv2.getTextSize(label, font, font_scale, thickness)

    badge_y1 = max(0, y1 - text_h - 10)
    badge_y2 = y1
    badge_x2 = min(frame.shape[1], x1 + text_w + 14)

    cv2.rectangle(frame, (x1, badge_y1), (badge_x2, badge_y2), color, -1)
    text_color = (0, 0, 0) if (color[0] + color[1] + color[2]) > 380 else (255, 255, 255)
    cv2.putText(
        frame,
        label,
        (x1 + 6, badge_y2 - 5),
        font,
        font_scale,
        text_color,
        thickness,
        cv2.LINE_AA,
    )


def draw_viewfinder_guide(frame: np.ndarray, w: int, h: int) -> None:
    """Draw subtle centering reticle to guide user where to hold phone or image"""
    box_w, box_h = int(w * 0.65), int(h * 0.65)
    cx, cy = w // 2, h // 2
    x1, y1 = cx - box_w // 2, cy - box_h // 2
    x2, y2 = cx + box_w // 2, cy + box_h // 2

    guide_color = (80, 80, 80)
    d = 24
    # Corner ticks
    cv2.line(frame, (x1, y1), (x1 + d, y1), guide_color, 2)
    cv2.line(frame, (x1, y1), (x1, y1 + d), guide_color, 2)
    cv2.line(frame, (x2, y1), (x2 - d, y1), guide_color, 2)
    cv2.line(frame, (x2, y1), (x2, y1 + d), guide_color, 2)
    cv2.line(frame, (x1, y2), (x1 + d, y2), guide_color, 2)
    cv2.line(frame, (x1, y2), (x1, y2 - d), guide_color, 2)
    cv2.line(frame, (x2, y2), (x2 - d, y2), guide_color, 2)
    cv2.line(frame, (x2, y2), (x2, y2 - d), guide_color, 2)

    # Subtle prompt text
    cv2.putText(
        frame,
        "Align site photo / phone here",
        (cx - 105, y2 + 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (130, 130, 130),
        1,
        cv2.LINE_AA,
    )


def main():
    available_models = [m for m in MODEL_CANDIDATES if Path(m["path"]).exists()]
    if not available_models:
        print("[ERROR] No model weights found in cv-model/weights or cv-model/models!")
        sys.exit(1)

    model_idx = 0
    model_spec = available_models[model_idx]
    print(f"\n[SkyGuard AI] Loading YOLO model: {model_spec['name']}...")
    model = YOLO(str(model_spec["path"]))

    print("[SkyGuard AI] Connecting to laptop webcam (index 0)...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot access webcam (index 0).")
        print("Please ensure no other app is currently using the camera.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    conf_threshold = 0.35
    capture_dir = PROJECT_ROOT / "cv-model" / "reports" / "webcam_captures"
    capture_dir.mkdir(parents=True, exist_ok=True)

    window_name = "SkyGuard AI — Live PPE Detection (Laptop Camera)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1024, 768)

    # Bring window to front and keep on top
    try:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
    except Exception:
        pass

    print("\n" + "=" * 65)
    print("  🟢 CAMERA STARTED & ACTIVE!")
    print(f"  Window: '{window_name}' is open on your desktop.")
    print("  (If behind VS Code, look at your Windows taskbar or press Alt+Tab)")
    print("=" * 65)
    print("  CONTROLS:")
    print("    [m]       : Switch Model (10-class <-> 4-class <-> 6-class)")
    print("    [+] / [=] : Increase Confidence (strict)")
    print("    [-]       : Decrease Confidence (sensitive, for phone glare)")
    print("    [s]       : Capture & Save Snapshot")
    print("    [q] / ESC : Exit Camera")
    print("=" * 65 + "\n")

    start_time = time.time()
    prev_time = time.time()
    fps = 0.0

    last_snap_path = None
    snap_flash_time = 0.0

    status_msg = "Camera Active — Hold image/phone in front of camera"
    status_time = time.time()
    last_logged_detections = ""

    frame_num = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Failed to read frame from webcam.")
                time.sleep(0.05)
                continue

            frame_num += 1
            h, w, _ = frame.shape
            now = time.time()

            # Run inference
            results = model.predict(frame, conf=conf_threshold, verbose=False)

            num_detections = 0
            detections_list = []
            has_violation = False
            has_compliant = False

            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = model.names.get(cls_id, f"cls_{cls_id}")
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    color = get_class_color(cls_name)
                    label = f"{cls_name} {int(conf * 100)}%"
                    draw_styled_box(frame, x1, y1, x2, y2, label, color)

                    num_detections += 1
                    detections_list.append(f"{cls_name} ({int(conf * 100)}%)")

                    lower_name = cls_name.lower()
                    if any(k in lower_name for k in ["no-helmet", "no-hardhat"]):
                        has_violation = True
                        now_t = time.time()
                        if now_t - _LAST_TRIGGER_TIMES.get("no-helmet", 0) > TRIGGER_COOLDOWN_SECONDS:
                            _LAST_TRIGGER_TIMES["no-helmet"] = now_t
                            send_dashboard_alert_async("no-helmet", conf)
                    elif any(k in lower_name for k in ["no-vest", "no-safety-vest"]):
                        has_violation = True
                        now_t = time.time()
                        if now_t - _LAST_TRIGGER_TIMES.get("no-vest", 0) > TRIGGER_COOLDOWN_SECONDS:
                            _LAST_TRIGGER_TIMES["no-vest"] = now_t
                            send_dashboard_alert_async("no-vest", conf)
                    elif any(k in lower_name for k in ["hardhat", "helmet", "safety-vest", "vest"]):
                        has_compliant = True

            # Periodic console logging so user sees progress in terminal
            if num_detections > 0:
                det_summary = ", ".join(detections_list)
                if det_summary != last_logged_detections and frame_num % 15 == 0:
                    print(f"[LIVE DETECTED] {det_summary}")
                    last_logged_detections = det_summary

            # FPS calculation
            dt = now - prev_time
            prev_time = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt) if fps > 0 else 1.0 / dt

            # Draw framing guide if no detections currently active
            if num_detections == 0:
                draw_viewfinder_guide(frame, w, h)

            # ----------------- TOP BANNER (STATUS & HUD) -----------------
            banner_h = 50
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, banner_h), (15, 15, 18), -1)
            cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

            # Pulsing Red/Green Live Indicator
            pulse = int((now * 2) % 2)
            dot_color = (0, 0, 240) if pulse else (0, 180, 0)
            cv2.circle(frame, (20, 25), 8, dot_color, -1)
            cv2.circle(frame, (20, 25), 11, dot_color, 1)

            elapsed_sec = int(now - start_time)
            timer_str = f"{elapsed_sec // 60:02d}:{elapsed_sec % 60:02d}"

            cv2.putText(
                frame,
                f"LIVE CAMERA  [{timer_str}]",
                (36, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # Active model + sensitivity badge
            active_short = available_models[model_idx]["name"].split("(")[0].strip()
            hud_info = f"{active_short}  |  FPS: {fps:.1f}  |  Conf: {int(conf_threshold*100)}%"
            cv2.putText(
                frame,
                hud_info,
                (w - 380, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (0, 230, 255),
                1,
                cv2.LINE_AA,
            )

            # ----------------- DETECTION ALERT STRIP -----------------
            if has_violation:
                # Red violation alert banner below top bar
                alert_bar = frame.copy()
                cv2.rectangle(alert_bar, (0, banner_h), (w, banner_h + 32), (0, 0, 180), -1)
                cv2.addWeighted(alert_bar, 0.85, frame, 0.15, 0, frame)
                cv2.putText(
                    frame,
                    f"!! SAFETY VIOLATION DETECTED !!  ({num_detections} objects in frame)",
                    (20, banner_h + 22),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                # Red border pulse
                cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 0, 230), 4)

            elif has_compliant:
                # Green compliance banner
                alert_bar = frame.copy()
                cv2.rectangle(alert_bar, (0, banner_h), (w, banner_h + 30), (0, 140, 0), -1)
                cv2.addWeighted(alert_bar, 0.85, frame, 0.15, 0, frame)
                cv2.putText(
                    frame,
                    f"OK PPE COMPLIANT DETECTED  ({num_detections} objects)",
                    (20, banner_h + 21),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

            # ----------------- SNAPSHOT FLASH -----------------
            if now - snap_flash_time < 2.0:
                flash_overlay = frame.copy()
                cv2.rectangle(flash_overlay, (0, h // 2 - 40), (w, h // 2 + 40), (20, 20, 20), -1)
                cv2.addWeighted(flash_overlay, 0.85, frame, 0.15, 0, frame)
                cv2.putText(
                    frame,
                    f"PHOTO CAPTURED: {last_snap_path}",
                    (w // 2 - 250, h // 2 + 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 120),
                    2,
                    cv2.LINE_AA,
                )
                # Flash white border
                cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (255, 255, 255), 6)

            # ----------------- BOTTOM CONTROLS BAR -----------------
            bot_h = 32
            bot_overlay = frame.copy()
            cv2.rectangle(bot_overlay, (0, h - bot_h), (w, h), (12, 12, 15), -1)
            cv2.addWeighted(bot_overlay, 0.85, frame, 0.15, 0, frame)

            controls_text = (
                "[m] Switch Model   [+/-] Adjust Sensitivity   [s] Save Photo   [q] Exit"
            )
            cv2.putText(
                frame,
                controls_text,
                (16, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.46,
                (210, 210, 210),
                1,
                cv2.LINE_AA,
            )

            cv2.imshow(window_name, frame)

            # Check if user clicked the window close button (X)
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("\n[SkyGuard AI] Window closed by user.")
                break

            # Keyboard controls
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):  # 'q' or ESC
                print("\n[SkyGuard AI] Stopping webcam detector. Goodbye!")
                break
            elif key == ord("m"):
                model_idx = (model_idx + 1) % len(available_models)
                model_spec = available_models[model_idx]
                print(f"\n[SkyGuard AI] Switched model to: {model_spec['name']}")
                model = YOLO(str(model_spec["path"]))
            elif key in (ord("+"), ord("=")):
                conf_threshold = min(0.90, conf_threshold + 0.05)
                print(f"[SkyGuard AI] Sensitivity: confidence >= {int(conf_threshold * 100)}%")
            elif key in (ord("-"), ord("_")):
                conf_threshold = max(0.10, conf_threshold - 0.05)
                print(f"[SkyGuard AI] Sensitivity: confidence >= {int(conf_threshold * 100)}%")
            elif key == ord("s"):
                snap_filename = f"capture_{int(time.time())}.jpg"
                snap_file = capture_dir / snap_filename
                cv2.imwrite(str(snap_file), frame)
                last_snap_path = snap_filename
                snap_flash_time = now
                if _WINSOUND:
                    try:
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)
                    except Exception:
                        pass
                print(f"\n[PHOTO CAPTURED] Saved to: {snap_file}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[SkyGuard AI] Camera released and windows closed cleanly.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SkyGuard AI] Stopped by user (Ctrl+C).")
    except SystemExit:
        pass
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
    # Exit with code 0 for clean termination
    import sys
    sys.exit(0)



