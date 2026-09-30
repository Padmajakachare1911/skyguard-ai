"""
Local / CI training helper with class-name guard (prevents drone/bird mistake).

Usage (GPU recommended):
  python cv-model/scripts/train_local.py --phase ppe_v1
  python cv-model/scripts/train_local.py --phase full_v1
  python cv-model/scripts/train_local.py --phase full_v2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

CV_MODEL = Path(__file__).resolve().parent.parent

# Compressed timeline: 40 epochs, patience=10 (see STATUS.md assumptions).
PHASES = {
    "ppe_v1": {
        "data": CV_MODEL / "datasets" / "merged_ppe_v1" / "data.yaml",
        "model": "yolov8n.pt",
        "epochs": 40,
        "name": "ppe_v1",
        "expected_classes": {"helmet", "no-helmet", "vest", "no-vest"},
        "train_kwargs": {},
    },
    "full_v1": {
        "data": CV_MODEL / "datasets" / "merged" / "data.yaml",
        "model": str(CV_MODEL / "models" / "ppe_v1" / "best.pt"),
        "epochs": 40,
        "name": "full_v1",
        "expected_classes": {"helmet", "no-helmet", "vest", "no-vest", "person", "machinery"},
        "train_kwargs": {},
    },
    "full_v2": {
        "data": CV_MODEL / "datasets" / "merged" / "data.yaml",
        "model": str(CV_MODEL / "models" / "full_v1" / "best.pt"),
        "epochs": 40,
        "name": "full_v2",
        "expected_classes": {"helmet", "no-helmet", "vest", "no-vest", "person", "machinery"},
        "train_kwargs": {
            "hsv_h": 0.02,
            "hsv_s": 0.9,
            "hsv_v": 0.6,
            "degrees": 5.0,
            "translate": 0.1,
            "scale": 0.6,
            "mosaic": 1.0,
            "erasing": 0.5,
            "mixup": 0.1,
        },
    },
}


def validate_data_yaml(yaml_path: Path, expected: set[str]) -> None:
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    names = data.get("names", {})
    found = set(names.values()) if isinstance(names, dict) else set(names)
    if found != expected:
        raise SystemExit(
            f"[ABORT] Wrong classes in {yaml_path}.\n"
            f"  Expected: {sorted(expected)}\n"
            f"  Found:    {sorted(found)}\n"
            f"  Re-run merge_datasets.py — do not train on the wrong dataset."
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=PHASES.keys(), required=True)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8, help="Default 8 for 4GB GPU / Windows paging")
    parser.add_argument("--workers", type=int, default=0, help="DataLoader workers (0 avoids spawn OOM on Windows)")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from runs/detect/<phase>/weights/last.pt if present",
    )
    args = parser.parse_args()

    cfg = PHASES[args.phase]
    data_yaml = cfg["data"]
    if not data_yaml.exists():
        sys.exit(f"[ERROR] Missing {data_yaml}. Run merge_datasets.py first.")

    validate_data_yaml(data_yaml, cfg["expected_classes"])

    out_dir = CV_MODEL / "models" / cfg["name"]
    out_dir.mkdir(parents=True, exist_ok=True)

    from ultralytics import YOLO

    weights = CV_MODEL / "runs" / "detect" / cfg["name"] / "weights" / "last.pt"
    init = str(weights) if args.resume and weights.exists() else cfg["model"]
    if args.resume and weights.exists():
        print(f"[resume] Continuing from {weights}")

    model = YOLO(init)
    train_kw = dict(cfg.get("train_kwargs", {}))
    results = model.train(
        resume=args.resume and weights.exists(),
        data=str(data_yaml),
        epochs=cfg["epochs"],
        imgsz=args.imgsz,
        batch=args.batch,
        name=cfg["name"],
        project=str(CV_MODEL / "runs" / "detect"),
        exist_ok=True,
        patience=10,
        device=0,
        workers=args.workers,
        **train_kw,
    )

    best = Path(results.save_dir) / "weights" / "best.pt"
    if best.exists():
        import shutil

        shutil.copy2(best, out_dir / "best.pt")
        print(f"[OK] Copied weights to {out_dir / 'best.pt'}")


if __name__ == "__main__":
    main()
