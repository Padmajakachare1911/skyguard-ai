"""
Compare clean vs hard-condition subsets on the test set (#39).

Hard subset: images with mean grayscale brightness below percentile threshold.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


def brightness(path: Path) -> float:
    img = cv2.imread(str(path))
    if img is None:
        return 255.0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(gray.mean())


def subset_metrics(model: YOLO, images: list[Path], labels_dir: Path) -> dict:
    if not images:
        return {"map50": 0.0, "count": 0}
    # Ultralytics val on explicit list via temporary yaml would be heavy; use predict+manual for speed on subset
    tp = fp = fn = 0
    for img in images[:200]:  # cap for runtime
        lbl = labels_dir / (img.stem + ".txt")
        if not lbl.exists():
            continue
        r = model.predict(str(img), conf=0.5, verbose=False)
        pred_n = len(r[0].boxes) if r else 0
        gt_n = len([ln for ln in lbl.read_text().splitlines() if ln.strip()])
        tp += min(pred_n, gt_n)
        fp += max(0, pred_n - gt_n)
        fn += max(0, gt_n - pred_n)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": p, "recall": r, "f1": f1, "count": len(images)}


def main() -> None:
    cv_model = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument(
        "--images",
        default=str(cv_model / "datasets" / "merged" / "test" / "images"),
    )
    ap.add_argument(
        "--labels",
        default=str(cv_model / "datasets" / "merged" / "test" / "labels"),
    )
    ap.add_argument("--percentile", type=float, default=35.0)
    ap.add_argument("--out", default="reports/week5_hard_conditions_metrics.md")
    args = ap.parse_args()

    img_dir = Path(args.images)
    imgs = sorted(img_dir.glob("*.jpg")) + sorted(img_dir.glob("*.png"))
    if not imgs:
        raise SystemExit(f"[ERROR] No images in {img_dir}")
    scores = [(p, brightness(p)) for p in imgs]
    thresh = float(np.percentile([s[1] for s in scores], args.percentile))
    hard = [p for p, b in scores if b <= thresh]
    clean = [p for p, b in scores if b > thresh]

    model = YOLO(args.model)
    clean_m = subset_metrics(model, clean, Path(args.labels))
    hard_m = subset_metrics(model, hard, Path(args.labels))

    out = Path(args.out)
    out.write_text(
        "# Week 5 — Hard vs Clean Conditions\n\n"
        f"**Model:** `{args.model}`\n\n"
        "| Subset | Images (sampled) | Precision | Recall | F1 |\n"
        "|---|---:|---:|---:|---:|\n"
        f"| Clean (brightness > p{args.percentile}) | {clean_m['count']} | "
        f"{clean_m['precision']:.3f} | {clean_m['recall']:.3f} | {clean_m['f1']:.3f} |\n"
        f"| Hard (brightness ≤ p{args.percentile}) | {hard_m['count']} | "
        f"{hard_m['precision']:.3f} | {hard_m['recall']:.3f} | {hard_m['f1']:.3f} |\n\n"
        "Hard subset uses darker test images as a proxy for low-light field conditions.\n",
        encoding="utf-8",
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
