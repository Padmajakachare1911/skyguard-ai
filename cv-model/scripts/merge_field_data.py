"""
Merge new field footage labels into merged dataset for field_v1 retrain (#65).

Usage:
  python scripts/merge_field_data.py --new-data datasets/field_raw --out datasets/merged_field
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def merge(new_data: Path, out: Path, base: Path) -> None:
    """Copy base merged YOLO tree then append images/labels from new_data."""
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(base, out)
    for split in ("train", "val", "test"):
        img_dst = out / split / "images"
        lbl_dst = out / split / "labels"
        img_dst.mkdir(parents=True, exist_ok=True)
        lbl_dst.mkdir(parents=True, exist_ok=True)
        src_img = new_data / split / "images"
        src_lbl = new_data / split / "labels"
        if src_img.exists():
            for f in src_img.glob("*"):
                shutil.copy2(f, img_dst / f.name)
        if src_lbl.exists():
            for f in src_lbl.glob("*.txt"):
                shutil.copy2(f, lbl_dst / f.name)
    print(f"Merged field data into {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("datasets/merged_field"))
    ap.add_argument("--base", type=Path, default=Path("datasets/merged"))
    args = ap.parse_args()
    merge(args.new_data, args.out, args.base)
