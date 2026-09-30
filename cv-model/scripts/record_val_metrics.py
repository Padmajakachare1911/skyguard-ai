"""
Run `yolo detect val` and write a markdown metrics report from JSON results.

Usage:
  python scripts/record_val_metrics.py \\
    --model models/full_v1/best.pt \\
    --data datasets/merged/data.yaml \\
    --title "Week 4 — full_v1" \\
    --out reports/week4_full_v1_metrics.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--issue", default="")
    ap.add_argument("--device", default="0", help="Ultralytics device (use 'cpu' while GPU is training)")
    args = ap.parse_args()

    from ultralytics import YOLO

    metrics = YOLO(args.model).val(
        data=args.data, split="test", verbose=False, device=args.device
    )
    box = metrics.box
    report = Path(args.out)
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {args.title}\n\n",
        f"**Issue:** {args.issue}\n\n" if args.issue else "",
        f"**Model:** `{args.model}`\n",
        f"**Dataset:** `{args.data}` (test split)\n\n",
        "| Metric | Value |\n|---|---|\n",
        f"| mAP@0.5 | **{box.map50:.3f}** |\n",
        f"| mAP@0.5:0.95 | **{box.map:.3f}** |\n",
        f"| Precision | **{box.mp:.3f}** |\n",
        f"| Recall | **{box.mr:.3f}** |\n",
    ]
    report.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {report}")


if __name__ == "__main__":
    main()
