"""
cv-model/scripts/download_datasets.py — SkyGuard AI
-----------------------------------------------------
Downloads 3 PPE datasets from Roboflow Universe into cv-model/datasets/raw/.
Slugs and class lists verified 2026-09-23 by browsing universe.roboflow.com.

USAGE:
    python cv-model/scripts/download_datasets.py

API key is loaded from the .env file at the repo root (never hardcoded here).
"""

import os
import sys
import zipfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Load API key from .env (gitignored) — never hardcode in this file
# ---------------------------------------------------------------------------
def load_api_key() -> str:
    key = os.environ.get("ROBOFLOW_API_KEY", "")
    if key:
        return key

    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("ROBOFLOW_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    if key:
                        return key

    sys.exit(
        "[ERROR] No Roboflow API key found.\n"
        "  Add this line to your .env file at the repo root:\n"
        "  ROBOFLOW_API_KEY=your_key_here"
    )


# ---------------------------------------------------------------------------
# Datasets — verified 2026-09-23 from universe.roboflow.com
# ---------------------------------------------------------------------------
DATASETS = [
    # Dataset 1 — Hard Hat Workers (joseph-nelson)
    # 7,035 images | Classes (3): head, helmet, person
    # version 14 is the latest verified version
    ("joseph-nelson", "hard-hat-workers", 14, "hard-hat-workers"),

    # Dataset 2 — Construction Site Safety (roboflow-universe-projects)
    # 717 images | Classes (25): Hardhat, NO-Hardhat, Safety Vest, NO-Safety Vest,
    #              Person, Excavator, truck, bus, van, machinery, etc.
    ("roboflow-universe-projects", "construction-site-safety", 30, "construction-site-safety"),

    # Dataset 3 — PPE Detection (testcasque)
    # 5,140 images | Classes (10): helmet, vest, goggles, boots, gloves,
    #                no-boots, no-gloves, no-goggles, no-helmet, no-vest
    ("testcasque", "ppe-detection-qlq3d", 1, "ppe-detection"),
]

RAW_DIR = Path(__file__).resolve().parent.parent / "datasets" / "raw"

# ---------------------------------------------------------------------------
# Class remap — verified class names from each dataset's Roboflow page
# Locked IDs: 0=helmet  1=no-helmet  2=vest  3=no-vest  4=person  5=machinery
# -1 = skip (class not needed in final dataset)
# ---------------------------------------------------------------------------
DATASET_REMAPS = {
    "hard-hat-workers": {
        # Verified classes: 0=head  1=helmet  2=person
        # 'head' = bare head (no helmet) → conservative: map to no-helmet
        0: 1,   # head    → no-helmet
        1: 0,   # helmet  → helmet
        2: 4,   # person  → person
    },
    "construction-site-safety": {
        # Verified 25 classes (positional order from dataset page):
        # 0=truck  1=bus  2=Mask  3=vehicle  4=van  5=fire hydrant  6=SUV
        # 7=Person  8=Excavator  9=Hardhat  10=sedan  11=trailer  12=Ladder
        # 13=Safety Vest  14=dump truck  15=Gloves  16=machinery  17=mini-van
        # 18=NO-Hardhat  19=NO-Mask  20=NO-Safety Vest  21=Safety Cone
        # 22=semi  23=truck and trailer  24=wheel loader
        0:  5,   # truck           → machinery
        1:  5,   # bus             → machinery
        2:  -1,  # Mask            → skip
        3:  5,   # vehicle         → machinery
        4:  5,   # van             → machinery
        5:  -1,  # fire hydrant    → skip
        6:  5,   # SUV             → machinery
        7:  4,   # Person          → person
        8:  5,   # Excavator       → machinery
        9:  0,   # Hardhat         → helmet
        10: 5,   # sedan           → machinery
        11: 5,   # trailer         → machinery
        12: -1,  # Ladder          → skip
        13: 2,   # Safety Vest     → vest
        14: 5,   # dump truck      → machinery
        15: -1,  # Gloves          → skip
        16: 5,   # machinery       → machinery
        17: 5,   # mini-van        → machinery
        18: 1,   # NO-Hardhat      → no-helmet
        19: -1,  # NO-Mask         → skip
        20: 3,   # NO-Safety Vest  → no-vest
        21: -1,  # Safety Cone     → skip
        22: 5,   # semi            → machinery
        23: 5,   # truck+trailer   → machinery
        24: 5,   # wheel loader    → machinery
    },
    "ppe-detection": {
        # Verified 10 classes:
        # 0=helmet  1=vest  2=goggles  3=boots  4=gloves
        # 5=no-boots  6=no-gloves  7=no-goggles  8=no-helmet  9=no-vest
        0: 0,   # helmet     → helmet
        1: 2,   # vest       → vest
        2: -1,  # goggles    → skip
        3: -1,  # boots      → skip
        4: -1,  # gloves     → skip
        5: -1,  # no-boots   → skip
        6: -1,  # no-gloves  → skip
        7: -1,  # no-goggles → skip
        8: 1,   # no-helmet  → no-helmet
        9: 3,   # no-vest    → no-vest
    },
}


# ---------------------------------------------------------------------------
# Download + validate helpers
# ---------------------------------------------------------------------------
def download_dataset(rf, workspace: str, project: str, version: int, name: str) -> Path:
    """Download one dataset with clear error messages."""
    dst = RAW_DIR / name

    if dst.exists() and any(dst.iterdir()):
        print(f"[SKIP] {name} already downloaded at {dst}")
        return dst

    print(f"\n[DOWNLOADING] {workspace}/{project} v{version} → {dst.name}")

    try:
        ver     = rf.workspace(workspace).project(project).version(version)
        ver.download("yolov8", location=str(dst))
        print(f"[OK] {name} downloaded.")
        return dst

    except zipfile.BadZipFile:
        import shutil; shutil.rmtree(dst, ignore_errors=True)
        print(
            f"\n[ERROR] BadZipFile — Roboflow returned HTML instead of a zip.\n"
            f"  Workspace : {workspace}\n"
            f"  Project   : {project}\n"
            f"  Version   : {version}\n"
            f"  This means the slug or version is wrong. Go to:\n"
            f"  https://universe.roboflow.com/{workspace}/{project}\n"
            f"  → Download Dataset → YOLOv8 → copy the exact values.\n"
        )
        return None

    except Exception as e:
        print(f"[ERROR] {name}: {type(e).__name__}: {e}")
        return None


def validate_dataset(dst: Path) -> dict:
    """Read data.yaml and report class names and image counts."""
    import yaml
    yaml_files = list(dst.glob("*.yaml"))
    if not yaml_files:
        return {"ok": False, "reason": "No data.yaml"}

    with open(yaml_files[0]) as f:
        info = yaml.safe_load(f)

    names = info.get("names", {})
    train = list((dst / "train" / "images").glob("*")) if (dst / "train" / "images").exists() else []
    print(f"  Classes ({info.get('nc',0)}): {list(names.values()) if isinstance(names, dict) else names}")
    print(f"  Train images: {len(train)}")
    return {"ok": True, "nc": info.get("nc", 0), "names": names, "train": len(train)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    try:
        from roboflow import Roboflow
    except ImportError:
        sys.exit("[ERROR] roboflow not installed. Run: pip install roboflow")

    api_key = load_api_key()
    print(f"[KEY] Roboflow API key: {api_key[:6]}... (truncated)")

    rf = Roboflow(api_key=api_key)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for workspace, project, version, name in DATASETS:
        dst = download_dataset(rf, workspace, project, version, name)
        if dst and dst.exists():
            print(f"[VALIDATING] {name}")
            info = validate_dataset(dst)
            results.append((name, info))

    print("\n" + "=" * 55)
    print("  Download Summary")
    print("=" * 55)
    for name, info in results:
        tag = "OK" if info.get("ok") else f"WARN: {info.get('reason','?')}"
        print(f"  [{tag}] {name}  ({info.get('train', 0)} train images, {info.get('nc', 0)} classes)")

    print(f"\n  Raw datasets: {RAW_DIR}")
    print("  Next step  : run cv-model/scripts/merge_datasets.py")


if __name__ == "__main__":
    main()
