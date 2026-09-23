"""
geofence/proximity_check.py — SkyGuard AI
-------------------------------------------
Determines whether a person is within a dangerous proximity threshold of machinery.

Two distance modes:
  1. GPS mode (primary): haversine distance in metres between two GPS coordinates.
  2. Pixel-distance fallback: Euclidean distance between bounding-box centres in
     the same frame, used when GPS is unavailable (Weeks 3–9 before MAVLink wired in).

Week 7 (#49) deliverable.
"""

import math
from shapely.geometry import Point


# ---------------------------------------------------------------------------
# GPS mode — haversine distance
# ---------------------------------------------------------------------------

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Return the great-circle distance in metres between two GPS coordinates.

    Accuracy is sufficient for distances < 1 km (mini-project scope).
    For production over longer ranges, use a proper geodetic library (pyproj).
    """
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def is_machinery_proximity_violation(
    person_lat: float,
    person_lon: float,
    machinery_lat: float,
    machinery_lon: float,
    threshold_m: float = 5.0,
) -> bool:
    """
    Return True if the person is within threshold_m metres of machinery (GPS mode).

    Args:
        person_lat, person_lon: GPS coordinates of the detected person.
        machinery_lat, machinery_lon: GPS coordinates of the detected machinery.
        threshold_m: Safety exclusion radius in metres (default 5 m).

    Note:
        For production, the GPS coords come from Rashi's MAVLink feed.
        Until Week 10, use the pixel-distance fallback below.
    """
    distance = haversine_distance_m(person_lat, person_lon, machinery_lat, machinery_lon)
    return distance < threshold_m


# ---------------------------------------------------------------------------
# Pixel-distance fallback (used when GPS is not yet available)
# ---------------------------------------------------------------------------

def bbox_centre(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    """
    Return (cx, cy) centre of a bounding box given as (x1, y1, x2, y2).
    Works with pixel coordinates from YOLO output.
    """
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def is_machinery_proximity_violation_pixels(
    person_bbox: tuple[float, float, float, float],
    machinery_bbox: tuple[float, float, float, float],
    threshold_px: float = 150.0,
) -> bool:
    """
    Pixel-distance fallback for machinery proximity detection.

    FALLBACK PATH — not geographically accurate; used only until real GPS
    telemetry from Rashi's MAVLink feed replaces this (Week 10).

    Args:
        person_bbox: (x1, y1, x2, y2) bounding box of detected person in pixels.
        machinery_bbox: (x1, y1, x2, y2) bounding box of detected machinery.
        threshold_px: Pixel distance threshold (default 150 px at 640px width).

    Returns:
        True if bbox centres are within threshold_px pixels of each other.
    """
    cx1, cy1 = bbox_centre(person_bbox)
    cx2, cy2 = bbox_centre(machinery_bbox)
    pixel_dist = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
    return pixel_dist < threshold_px


if __name__ == "__main__":
    # Smoke test
    print("=== GPS mode ===")
    # Person and machinery 3 m apart — should be True (< 5 m threshold)
    d = haversine_distance_m(19.0330, 73.0297, 19.0330269, 73.0297)
    print(f"  Distance: {d:.2f} m  (expect ~3 m)")
    print(f"  Violation: {is_machinery_proximity_violation(19.0330, 73.0297, 19.0330269, 73.0297)}")

    print("\n=== Pixel fallback mode ===")
    person_box = (100, 200, 200, 400)
    mach_near  = (220, 210, 400, 450)  # close
    mach_far   = (500, 200, 700, 450)  # far
    print(f"  Near machinery violation: {is_machinery_proximity_violation_pixels(person_box, mach_near)}")
    print(f"  Far machinery violation:  {is_machinery_proximity_violation_pixels(person_box, mach_far)}")
