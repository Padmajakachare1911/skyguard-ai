"""
inference/person_down.py — SkyGuard AI
---------------------------------------
Person-down heuristic: flags a detected person as collapsed/unconscious
based on their bounding-box aspect ratio (width / height).

A standing person has a tall, narrow bbox (ratio < 1).
A lying-down person has a wide, flat bbox (ratio ≥ threshold).

This is deliberately a heuristic, not a trained class, at mini-project scope.
Threshold=1.4 is the starting value; tune upward if false positives occur
(e.g. person crouching), or downward if lying-down cases are missed.

Week 4 (#32) deliverable.
"""

# Aspect ratio at or above this value triggers a person-down flag.
# Rationale: a typical standing human bbox is ~0.4–0.7 wide/tall;
# lying flat is ~2.0–3.5. 1.4 sits conservatively between them.
DEFAULT_ASPECT_THRESHOLD: float = 1.4


def detect_person_down(
    bbox: tuple[float, float, float, float],
    threshold: float = DEFAULT_ASPECT_THRESHOLD,
) -> bool:
    """
    Return True if the bounding box indicates a person lying down.

    Args:
        bbox: (x1, y1, x2, y2) bounding box in pixel coordinates (or normalised 0–1).
              The coordinate system doesn't matter — only the ratio is used.
        threshold: width/height ratio above which the person is flagged as down.
                   Default 1.4. Tune this after field testing.

    Returns:
        True if width/height >= threshold (person likely horizontal).

    Raises:
        ValueError: if bbox has zero height (degenerate box).
    """
    x1, y1, x2, y2 = bbox
    width  = abs(x2 - x1)
    height = abs(y2 - y1)

    if height == 0:
        raise ValueError(f"Degenerate bbox with zero height: {bbox}")

    ratio = width / height
    return ratio >= threshold


def aspect_ratio(bbox: tuple[float, float, float, float]) -> float:
    """Return the width/height ratio of a bounding box (useful for logging)."""
    x1, y1, x2, y2 = bbox
    height = abs(y2 - y1)
    if height == 0:
        return float("inf")
    return abs(x2 - x1) / height


if __name__ == "__main__":
    # Smoke test with example bboxes
    cases = [
        ((100, 50, 160, 250), False, "standing person (ratio≈0.3)"),
        ((100, 200, 300, 250), True,  "lying person (ratio=4.0)"),
        ((100, 100, 240, 200), True,  "crouching/lying (ratio=1.4 — boundary)"),
        ((100, 100, 230, 200), False, "crouching below threshold (ratio=1.3)"),
    ]
    for bbox, expected, label in cases:
        result = detect_person_down(bbox)
        ratio  = aspect_ratio(bbox)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] {label}: ratio={ratio:.2f} → person_down={result}")
