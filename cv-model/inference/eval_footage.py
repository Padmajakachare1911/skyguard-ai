"""
SIMULATED/PROXY — not real flight data

Evaluate full_v2 (or any .pt) on a folder of footage + YOLO-format labels.
Produces confusion-style counts, per-class P/R/F1, FP/FN crop logs, and .md/.csv reports.

Usage:
  python -m inference.eval_footage \\
    --footage datasets/proxy/construction_sample.mp4 \\
    --labels datasets/merged/test/labels \\
    --images datasets/merged/test/images \\
    --model models/full_v2/best.pt \\
    --report reports/week9_fp_fn_summary.md \\
    --csv reports/week9_fp_fn.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError as e:
    raise SystemExit("ultralytics required") from e

# YOLO class id -> violation type for evaluation (presence classes map to violation negatives)
YOLO_TO_VIOLATION = {
    1: "no-helmet",
    3: "no-vest",
    4: "person",
    5: "machinery",
}

VIOLATION_CLASSES = [
    "no-helmet",
    "no-vest",
    "person",
    "machinery",
]


@dataclass
class Box:
    cls: int
    xyxy: tuple[float, float, float, float]


def load_yolo_labels(label_path: Path, w: int, h: int) -> list[Box]:
    if not label_path.exists():
        return []
    boxes: list[Box] = []
    for line in label_path.read_text().strip().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        cls = int(parts[0])
        cx, cy, bw, bh = map(float, parts[1:5])
        x1 = (cx - bw / 2) * w
        y1 = (cy - bh / 2) * h
        x2 = (cx + bw / 2) * w
        y2 = (cy + bh / 2) * h
        boxes.append(Box(cls, (x1, y1, x2, y2)))
    return boxes


def iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter <= 0:
        return 0.0
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return inter / (area_a + area_b - inter + 1e-9)


def match_boxes(gt: list[Box], pred: list[Box], iou_thr: float = 0.5) -> tuple[int, int, int]:
    """Return tp, fp, fn counts for one class on one image."""
    used_pred: set[int] = set()
    tp = 0
    for g in gt:
        best_j, best_iou = -1, 0.0
        for j, p in enumerate(pred):
            if j in used_pred:
                continue
            v = iou(g.xyxy, p.xyxy)
            if v > best_iou:
                best_iou, best_j = v, j
        if best_j >= 0 and best_iou >= iou_thr:
            used_pred.add(best_j)
            tp += 1
    fn = len(gt) - tp
    fp = len(pred) - len(used_pred)
    return tp, fp, fn


def eval_image_folder(
    model: YOLO,
    images_dir: Path,
    labels_dir: Path,
    conf: float,
    crops_dir: Path,
) -> dict:
    stats = {c: {"tp": 0, "fp": 0, "fn": 0} for c in range(6)}
    failure_log: list[dict] = []

    images = sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.png"))
    for img_path in images:
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue
        h, w = frame.shape[:2]
        gt = load_yolo_labels(labels_dir / (img_path.stem + ".txt"), w, h)

        results = model.predict(frame, conf=conf, verbose=False)
        pred: list[Box] = []
        for r in results:
            for box in r.boxes:
                pred.append(
                    Box(
                        int(box.cls[0]),
                        tuple(box.xyxy[0].tolist()),
                    )
                )

        for cls_id in range(6):
            gt_c = [b for b in gt if b.cls == cls_id]
            pr_c = [b for b in pred if b.cls == cls_id]
            tp, fp, fn = match_boxes(gt_c, pr_c)
            stats[cls_id]["tp"] += tp
            stats[cls_id]["fn"] += fn
            stats[cls_id]["fp"] += fp

            if fn > 0:
                failure_log.append({"file": img_path.name, "kind": "FN", "cls": cls_id, "count": fn})
            for b in pr_c:
                if fp <= 0:
                    break
                crops_dir.mkdir(parents=True, exist_ok=True)
                x1, y1, x2, y2 = map(int, b.xyxy)
                crop = frame[max(0, y1) : y2, max(0, x1) : x2]
                out = crops_dir / f"fp_{img_path.stem}_c{cls_id}.jpg"
                cv2.imwrite(str(out), crop)
                failure_log.append({"file": img_path.name, "kind": "FP", "cls": cls_id, "crop": str(out)})
                break

    return {"per_class": stats, "failures": failure_log}


def prf1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f1


def write_reports(result: dict, report_path: Path, csv_path: Path, model_path: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with report_path.open("w") as md:
        md.write("# SIMULATED/PROXY — not real flight data\n\n")
        md.write("## Footage evaluation summary\n\n")
        md.write(f"**Model:** `{model_path}`\n\n")
        md.write("| Class ID | TP | FP | FN | Precision | Recall | F1 |\n")
        md.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for cls_id, s in result["per_class"].items():
            p, r, f1 = prf1(s["tp"], s["fp"], s["fn"])
            md.write(
                f"| {cls_id} | {s['tp']} | {s['fp']} | {s['fn']} | {p:.3f} | {r:.3f} | {f1:.3f} |\n"
            )
            rows.append({"class_id": cls_id, "tp": s["tp"], "fp": s["fp"], "fn": s["fn"],
                         "precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)})

    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["class_id"])
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--images", required=True, help="Folder of evaluation images")
    ap.add_argument("--labels", required=True, help="YOLO labels folder")
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--report", default="reports/week9_fp_fn_summary.md")
    ap.add_argument("--csv", default="reports/week9_fp_fn.csv")
    ap.add_argument("--crops-dir", default="reports/fp_fn_crops")
    args = ap.parse_args()

    model = YOLO(args.model)
    result = eval_image_folder(
        model,
        Path(args.images),
        Path(args.labels),
        args.conf,
        Path(args.crops_dir),
    )
    write_reports(result, Path(args.report), Path(args.csv), args.model)
    print(f"Wrote {args.report} and {args.csv}")


if __name__ == "__main__":
    main()
