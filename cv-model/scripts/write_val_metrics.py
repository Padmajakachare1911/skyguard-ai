"""Run YOLO val and write a markdown metrics report (Week 2/4/5 reports)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import yaml

CV_MODEL = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--title", default="Validation metrics")
    args = parser.parse_args()

    from ultralytics import YOLO

    model = YOLO(str(args.weights))
    metrics = model.val(data=str(args.data))

    box = metrics.box
    lines = [
        f"# {args.title}",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        f"- **Weights:** `{args.weights}`",
        f"- **Data:** `{args.data}`",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| mAP50 | {box.map50:.4f} |",
        f"| mAP50-95 | {box.map:.4f} |",
        f"| Precision (mean) | {box.mp:.4f} |",
        f"| Recall (mean) | {box.mr:.4f} |",
        "",
    ]

    with open(args.data, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    names = data.get("names", {})
    if isinstance(names, dict):
        name_list = [names[i] for i in sorted(names.keys(), key=int)]
    else:
        name_list = list(names)

    if hasattr(box, "maps") and box.maps is not None and len(box.maps) == len(name_list):
        lines.append("## Per-class mAP50-95")
        lines.append("")
        for n, m in zip(name_list, box.maps):
            lines.append(f"- `{n}`: {float(m):.4f}")
        lines.append("")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Wrote {args.report}")


if __name__ == "__main__":
    main()
