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
    # v2 has helmet/head/person; v14 export only exposes class "head" in data.yaml
    ("joseph-nelson", "hard-hat-workers", 2, "hard-hat-workers"),

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

# Class remapping is done by name in scripts/merge_datasets.py (not here).

# ---------------------------------------------------------------------------
# Download + validate helpers
# ---------------------------------------------------------------------------
def download_dataset(rf, workspace: str, project: str, version: int, name: str) -> Path:
    """Download one dataset with clear error messages."""
    dst = RAW_DIR / name

    if dst.exists() and any(dst.iterdir()):
        print(f"[SKIP] {name} already downloaded at {dst}")
        return dst

    print(f"\n[DOWNLOADING] {workspace}/{project} v{version} -> {dst.name}")

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
