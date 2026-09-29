"""
Build a short MP4 from test-set images for infer_video.py smoke tests.
Uses construction-site safety images from datasets/merged/test/images.
"""

import argparse
import random
from pathlib import Path

import cv2


def make_video(image_dir: Path, output: Path, fps: int = 5, max_frames: int = 60) -> None:
    images = sorted(image_dir.glob("*.jpg"))
    if not images:
        raise FileNotFoundError(f"No .jpg images in {image_dir}")
    random.seed(42)
    if len(images) > max_frames:
        images = random.sample(images, max_frames)
        images.sort()

    first = cv2.imread(str(images[0]))
    if first is None:
        raise RuntimeError(f"Cannot read {images[0]}")
    h, w = first.shape[:2]
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for img_path in images:
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue
        if frame.shape[:2] != (h, w):
            frame = cv2.resize(frame, (w, h))
        writer.write(frame)
    writer.release()
    print(f"Wrote {len(images)} frames to {output}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", default=str(root / "datasets" / "merged" / "test" / "images"))
    ap.add_argument("--output", default=str(root / "datasets" / "proxy" / "construction_sample.mp4"))
    ap.add_argument("--fps", type=int, default=5)
    ap.add_argument("--max-frames", type=int, default=60)
    args = ap.parse_args()
    make_video(Path(args.images), Path(args.output), args.fps, args.max_frames)
