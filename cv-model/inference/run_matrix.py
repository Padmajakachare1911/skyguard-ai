"""
Multi-condition test matrix (#66). Tags clips via JSON config; unfilled cells stay NOT TESTED.

Usage:
  python -m inference.run_matrix --config datasets/proxy/matrix_config.json --model models/field_v1/best.pt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

try:
    from ultralytics import YOLO
except ImportError as e:
    raise SystemExit("ultralytics required") from e

VIOLATIONS = [
    "no-helmet",
    "no-vest",
    "restricted-zone-entry",
    "machinery-proximity",
    "person-down",
]


def score_clip(model: YOLO, clip: Path, violation: str, conf: float = 0.5) -> str:
    cap = cv2.VideoCapture(str(clip))
    if not cap.isOpened():
        return "NOT TESTED — no footage"
    hits = 0
    frames = 0
    while frames < 60:
        ret, frame = cap.read()
        if not ret:
            break
        r = model.predict(frame, conf=conf, verbose=False)
        for res in r:
            for box in res.boxes:
                cls = int(box.cls[0])
                name = model.names.get(cls, str(cls))
                if violation in ("no-helmet", "no-vest") and name == violation:
                    hits += 1
                elif violation == "person-down" and name == "person":
                    from inference.person_down import detect_person_down

                    if detect_person_down(tuple(box.xyxy[0].tolist())):
                        hits += 1
                elif violation == "machinery-proximity" and name == "machinery":
                    hits += 1
        frames += 1
    cap.release()
    if frames == 0:
        return "NOT TESTED — no footage"
    return "PASS" if hits > 0 else "FAIL (no detection)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="JSON: {cells: [{time,light,alt,occlusion,violation,clip}]")
    ap.add_argument("--model", required=True)
    ap.add_argument("--report", default="reports/week12_multi_condition_matrix.md")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    model = YOLO(args.model)
    lines = [
        "# SIMULATED/PROXY — not real flight data\n",
        "## Multi-condition matrix\n\n",
        "| Time | Lighting | Altitude | Occlusion | Violation | Clip | Result |\n",
        "|---|---|---|---|---|---|---|\n",
    ]
    for cell in cfg.get("cells", []):
        clip = Path(cell.get("clip", ""))
        if clip.exists():
            result = score_clip(model, clip, cell["violation"])
        else:
            result = "NOT TESTED — no footage"
        lines.append(
            f"| {cell.get('time','?')} | {cell.get('light','?')} | {cell.get('alt','?')} | "
            f"{cell.get('occlusion','?')} | {cell['violation']} | `{clip}` | {result} |\n"
        )

    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
