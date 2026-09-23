"""
Merge raw Roboflow exports into unified YOLO datasets for SkyGuard AI training.

Outputs:
  cv-model/datasets/merged/          — 6 classes (helmet … machinery), 70/20/10 split
  cv-model/datasets/merged_ppe_v1/   — Week 2 MVP: 4 PPE classes only, same split seed

Class IDs are remapped by **name** from each dataset's data.yaml (Roboflow sorts names
alphabetically — positional remaps break silently).
"""

from __future__ import annotations

import hashlib
import random
import shutil
import sys
from pathlib import Path

import yaml

CV_MODEL = Path(__file__).resolve().parent.parent
RAW_DIR = CV_MODEL / "datasets" / "raw"
MERGED_FULL = CV_MODEL / "datasets" / "merged"
MERGED_PPE = CV_MODEL / "datasets" / "merged_ppe_v1"

FULL_NAMES = ["helmet", "no-helmet", "vest", "no-vest", "person", "machinery"]
PPE_NAMES = ["helmet", "no-helmet", "vest", "no-vest"]

SPLIT_SEED = 42
SPLIT_RATIOS = (0.7, 0.2, 0.1)

# Raw class name (exact string from data.yaml) -> unified class id, or None to skip
RAW_CLASS_TO_UNIFIED: dict[str, dict[str, int | None]] = {
    "hard-hat-workers": {
        "head": 1,  # bare head treated as no-helmet for safety auditing
        "helmet": 0,
        "person": 4,
    },
    "construction-site-safety": {
        "Hardhat": 0,
        "NO-Hardhat": 1,
        "Safety Vest": 2,
        "NO-Safety Vest": 3,
        "Person": 4,
        "Excavator": 5,
        "machinery": 5,
        "wheel loader": 5,
        "dump truck": 5,
        "truck and trailer": 5,
        "truck": 5,
        "trailer": 5,
        "semi": 5,
        "sedan": 5,
        "SUV": 5,
        "van": 5,
        "mini-van": 5,
        "bus": 5,
        "vehicle": 5,
    },
    "ppe-detection": {
        "helmet": 0,
        "no-helmet": 1,
        "vest": 2,
        "no-vest": 3,
    },
}


def load_yaml_names(data_yaml: Path) -> list[str]:
    with open(data_yaml, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    names = data.get("names", [])
    if isinstance(names, dict):
        return [names[i] for i in sorted(names.keys(), key=int)]
    return list(names)


def remap_label_line(line: str, id_map: dict[int, int]) -> str | None:
    parts = line.strip().split()
    if len(parts) < 5:
        return None
    old_id = int(float(parts[0]))
    new_id = id_map.get(old_id)
    if new_id is None:
        return None
    parts[0] = str(new_id)
    return " ".join(parts)


def build_id_map(dataset_key: str, class_names: list[str]) -> dict[int, int | None]:
    name_table = RAW_CLASS_TO_UNIFIED.get(dataset_key)
    if not name_table:
        raise KeyError(f"No RAW_CLASS_TO_UNIFIED entry for {dataset_key}")
    id_map: dict[int, int | None] = {}
    for idx, name in enumerate(class_names):
        unified = name_table.get(name)
        id_map[idx] = unified  # None means skip
    return id_map


def collect_labeled_images(dataset_dir: Path, dataset_key: str) -> list[tuple[Path, Path, list[str]]]:
    """Returns (image_path, label_path, remapped_label_lines)."""
    yaml_path = dataset_dir / "data.yaml"
    if not yaml_path.exists():
        yaml_path = next(dataset_dir.glob("*.yaml"), None)
    if not yaml_path:
        raise FileNotFoundError(f"No data.yaml in {dataset_dir}")

    class_names = load_yaml_names(yaml_path)
    id_map = build_id_map(dataset_key, class_names)

    items: list[tuple[Path, Path, list[str]]] = []
    for split in ("train", "valid", "test"):
        img_dir = dataset_dir / split / "images"
        lbl_dir = dataset_dir / split / "labels"
        if not img_dir.exists():
            continue
        for img_path in img_dir.iterdir():
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            lbl_path = lbl_dir / (img_path.stem + ".txt")
            if not lbl_path.exists():
                continue
            new_lines: list[str] = []
            with open(lbl_path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    old_id = int(float(line.split()[0]))
                    unified_id = id_map.get(old_id)
                    if unified_id is None:
                        continue
                    parts = line.strip().split()
                    parts[0] = str(unified_id)
                    new_lines.append(" ".join(parts))
            if not new_lines:
                continue
            items.append((img_path, lbl_path, new_lines))
    return items


def stable_key(dataset_key: str, img_path: Path) -> str:
    h = hashlib.sha1(f"{dataset_key}/{img_path.name}".encode()).hexdigest()[:12]
    return f"{dataset_key}_{img_path.stem}_{h}"


def split_items(items: list[tuple[str, Path, list[str]]]) -> dict[str, list]:
    random.seed(SPLIT_SEED)
    shuffled = items[:]
    random.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * SPLIT_RATIOS[0])
    n_val = int(n * SPLIT_RATIOS[1])
    return {
        "train": shuffled[:n_train],
        "val": shuffled[n_train : n_train + n_val],
        "test": shuffled[n_train + n_val :],
    }


def write_dataset(
    out_root: Path,
    class_names: list[str],
    splits: dict[str, list[tuple[str, Path, list[str]]]],
) -> None:
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)

    counts = {c: 0 for c in class_names}
    for split_name, split_items_list in splits.items():
        yolo_split = "val" if split_name == "val" else split_name
        img_out = out_root / yolo_split / "images"
        lbl_out = out_root / yolo_split / "labels"
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        for prefix, src_img, lines in split_items_list:
            dst_stem = prefix
            dst_img = img_out / f"{dst_stem}{src_img.suffix.lower()}"
            shutil.copy2(src_img, dst_img)
            with open(lbl_out / f"{dst_stem}.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            for line in lines:
                cls_id = int(line.split()[0])
                counts[class_names[cls_id]] += 1

    data = {
        "path": str(out_root.resolve()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": len(class_names),
        "names": {i: n for i, n in enumerate(class_names)},
    }
    with open(out_root / "data.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    print(f"  Wrote {out_root.name}: {sum(len(v) for v in splits.values())} images")
    print(f"  Label instances per class: {counts}")


def filter_to_ppe(items: list[tuple[str, Path, list[str]]]) -> list[tuple[str, Path, list[str]]]:
    """Keep only helmet/vest classes; remap IDs 0-3 -> 0-3."""
    ppe_ids = {0, 1, 2, 3}
    out: list[tuple[str, Path, list[str]]] = []
    for prefix, img, lines in items:
        filtered = [ln for ln in lines if int(ln.split()[0]) in ppe_ids]
        if not filtered:
            continue
        out.append((prefix, img, filtered))
    return out


def assert_expected_classes(yaml_path: Path, expected: set[str]) -> None:
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    names = data.get("names", {})
    if isinstance(names, dict):
        found = set(names.values())
    else:
        found = set(names)
    if found != expected:
        raise AssertionError(f"{yaml_path}: expected classes {expected}, got {found}")


def main() -> None:
    if not RAW_DIR.exists():
        sys.exit(f"[ERROR] Raw datasets missing: {RAW_DIR}\n  Run download_datasets.py first.")

    all_items: list[tuple[str, Path, list[str]]] = []
    for dataset_key in RAW_CLASS_TO_UNIFIED:
        ds_dir = RAW_DIR / dataset_key
        if not ds_dir.exists():
            sys.exit(f"[ERROR] Missing dataset folder: {ds_dir}")
        print(f"[MERGE] Reading {dataset_key} ...")
        for img_path, _lbl, lines in collect_labeled_images(ds_dir, dataset_key):
            prefix = stable_key(dataset_key, img_path)
            all_items.append((prefix, img_path, lines))
        print(f"  usable images so far: {len(all_items)}")

    if len(all_items) < 100:
        sys.exit("[ERROR] Too few labeled images after remap — check raw downloads and class names.")

    splits = split_items(all_items)
    print(f"[SPLIT] train={len(splits['train'])} val={len(splits['val'])} test={len(splits['test'])}")

    write_dataset(MERGED_FULL, FULL_NAMES, splits)

    ppe_pool = filter_to_ppe(all_items)
    ppe_splits = split_items(ppe_pool)
    write_dataset(MERGED_PPE, PPE_NAMES, ppe_splits)

    assert_expected_classes(MERGED_FULL / "data.yaml", set(FULL_NAMES))
    assert_expected_classes(MERGED_PPE / "data.yaml", set(PPE_NAMES))

    print("\n[OK] Merge complete.")
    print(f"  Full (6-class): {MERGED_FULL / 'data.yaml'}")
    print(f"  PPE v1 (4-class): {MERGED_PPE / 'data.yaml'}")


if __name__ == "__main__":
    main()
