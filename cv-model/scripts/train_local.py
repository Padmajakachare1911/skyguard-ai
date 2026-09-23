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

PHASES = {
    "ppe_v1": {
        "data": CV_MODEL / "datasets" / "merged_ppe_v1" / "data.yaml",
        "model": "yolov8n.pt",
        "epochs": 100,
        "name": "ppe_v1",
        "expected_classes": {"helmet", "no-helmet", "vest", "no-vest"},
    },
    "full_v1": {
        "data": CV_MODEL / "datasets" / "merged" / "data.yaml",
        "model": str(CV_MODEL / "models" / "ppe_v1" / "best.pt"),
        "epochs": 80,
        "name": "full_v1",
        "expected_classes": {"helmet", "no-helmet", "vest", "no-vest", "person", "machinery"},
    },
    "full_v2": {
        "data": CV_MODEL / "datasets" / "merged" / "data.yaml",
        "model": str(CV_MODEL / "models" / "full_v1" / "best.pt"),
        "epochs": 60,
        "name": "full_v2",
        "expected_classes": {"helmet", "no-helmet", "vest", "no-vest", "person", "machinery"},
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
    parser.add_argument("--batch", type=int, default=16)
    args = parser.parse_args()

    cfg = PHASES[args.phase]
    data_yaml = cfg["data"]
    if not data_yaml.exists():
        sys.exit(f"[ERROR] Missing {data_yaml}. Run merge_datasets.py first.")

    validate_data_yaml(data_yaml, cfg["expected_classes"])

    out_dir = CV_MODEL / "models" / cfg["name"]
    out_dir.mkdir(parents=True, exist_ok=True)

    from ultralytics import YOLO

    model = YOLO(cfg["model"])
    results = model.train(
        data=str(data_yaml),
        epochs=cfg["epochs"],
        imgsz=args.imgsz,
        batch=args.batch,
        name=cfg["name"],
        project=str(CV_MODEL / "runs" / "detect"),
        exist_ok=True,
    )

    best = Path(results.save_dir) / "weights" / "best.pt"
    if best.exists():
        import shutil

        shutil.copy2(best, out_dir / "best.pt")
        print(f"[OK] Copied weights to {out_dir / 'best.pt'}")


if __name__ == "__main__":
    main()
