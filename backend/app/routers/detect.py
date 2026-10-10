import base64
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ultralytics import YOLO

from app import models
from app.database import get_db
from app.routers.violations import manager

router = APIRouter(prefix="/detect", tags=["detection"])

# Model paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
WEIGHTS_PATH = PROJECT_ROOT / "cv-model" / "weights" / "best_ppe_v1.pt"

_model = None
_last_violation_log_time: dict[str, float] = {}
COOLDOWN_SECONDS = 4.0


def get_model():
    global _model
    if _model is None:
        if not WEIGHTS_PATH.exists():
            raise RuntimeError(f"Weights file not found at {WEIGHTS_PATH}")
        _model = YOLO(str(WEIGHTS_PATH))
    return _model


class DetectRequest(BaseModel):
    image_base64: str
    conf: float = 0.35
    auto_log: bool = True


def get_class_meta(cls_name: str) -> dict:
    lower = cls_name.lower().replace("_", "-").replace(" ", "-")
    is_violation = any(k in lower for k in ["no-helmet", "no-hardhat", "no-vest", "no-safety-vest", "no-mask"])

    if is_violation:
        color = "#ef4444"  # Red
        if "no-helmet" in lower or "no-hardhat" in lower:
            v_type = "no-helmet"
        elif "no-vest" in lower or "no-safety-vest" in lower:
            v_type = "no-vest"
        elif "no-mask" in lower:
            v_type = "no-mask"
        else:
            v_type = "violation"
    elif any(k in lower for k in ["hardhat", "helmet", "safety-vest", "vest", "mask"]):
        color = "#22c55e"  # Green
        v_type = None
    elif "person" in lower:
        color = "#06b6d4"  # Cyan
        v_type = None
    elif any(k in lower for k in ["machinery", "vehicle"]):
        color = "#f97316"  # Orange
        v_type = None
    else:
        color = "#eab308"  # Yellow
        v_type = None

    return {
        "is_violation": is_violation,
        "violation_type": v_type,
        "color": color,
    }


@router.get("/status")
def detection_status():
    model = get_model()
    return {
        "model_loaded": True,
        "weights": str(WEIGHTS_PATH.name),
        "classes": model.names,
        "num_classes": len(model.names),
        "default_conf": 0.35,
    }


@router.post("/frame")
async def detect_frame(
    payload: DetectRequest,
    db: Session = Depends(get_db)
):
    start_t = time.time()
    model = get_model()

    # Decode image from base64
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("cv2.imdecode returned None")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")

    h, w, _ = frame.shape
    conf_thresh = max(0.1, min(0.95, payload.conf))

    # Run YOLO inference
    results = model.predict(frame, conf=conf_thresh, imgsz=640, verbose=False)

    detections = []
    has_violation = False
    violations_found = []

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            cls_name = model.names.get(cls_id, f"cls_{cls_id}")
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            meta = get_class_meta(cls_name)

            det_item = {
                "class": cls_name,
                "confidence": round(conf, 3),
                "box": [round(x1), round(y1), round(x2), round(y2)],
                "box_norm": [round(x1 / w, 4), round(y1 / h, 4), round(x2 / w, 4), round(y2 / h, 4)],
                "is_violation": meta["is_violation"],
                "violation_type": meta["violation_type"],
                "color": meta["color"],
            }
            detections.append(det_item)

            if meta["is_violation"]:
                has_violation = True
                violations_found.append((meta["violation_type"], conf))

    # Optional auto-logging to database & websocket
    logged_alert = None
    if payload.auto_log and has_violation:
        now = time.time()
        for v_type, v_conf in violations_found:
            last_time = _last_violation_log_time.get(v_type, 0.0)
            if now - last_time >= COOLDOWN_SECONDS:
                _last_violation_log_time[v_type] = now
                try:
                    db_violation = models.Violation(
                        type=v_type,
                        confidence=round(v_conf, 2),
                        latitude=19.033,
                        longitude=73.0297,
                        timestamp=datetime.now(timezone.utc),
                        image_url="live_cam_detection.jpg"
                    )
                    db.add(db_violation)
                    db.commit()
                    db.refresh(db_violation)

                    # Broadcast over websocket
                    alert_dict = {
                        "id": db_violation.id,
                        "type": db_violation.type,
                        "confidence": db_violation.confidence,
                        "latitude": db_violation.latitude,
                        "longitude": db_violation.longitude,
                        "timestamp": db_violation.timestamp.isoformat(),
                        "image_url": db_violation.image_url,
                    }
                    await manager.broadcast(alert_dict)
                    logged_alert = alert_dict
                except Exception as log_err:
                    print(f"[Detect Error] Failed to auto-log violation: {log_err}")

    elapsed_ms = round((time.time() - start_t) * 1000, 1)

    return {
        "num_detections": len(detections),
        "detections": detections,
        "has_violation": has_violation,
        "violations": [v[0] for v in violations_found],
        "logged_alert": logged_alert,
        "latency_ms": elapsed_ms,
        "frame_width": w,
        "frame_height": h,
    }
