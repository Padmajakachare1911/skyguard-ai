"""
geofence/restricted_zone.py — SkyGuard AI
------------------------------------------
Determines whether a GPS coordinate is inside a defined restricted zone polygon.
Uses Shapely for all geometry — deliberately kept independent of model accuracy.

Week 3 (#22) deliverable.
"""

from shapely.geometry import Point, Polygon


def is_in_restricted_zone(
    lat: float,
    lon: float,
    zone_coords: list[tuple[float, float]],
) -> bool:
    """
    Return True if the point (lat, lon) is inside the restricted zone polygon.

    Args:
        lat: Latitude of the point to test.
        lon: Longitude of the point to test.
        zone_coords: List of (lat, lon) tuples defining the polygon boundary
                     in order (clockwise or counter-clockwise). Minimum 3 points.

    Returns:
        True if inside or on the boundary, False otherwise.

    Note:
        Shapely's contains() returns False for boundary points; contains_properly()
        is stricter. We use `contains` OR `touches` to treat boundary as "inside"
        which is the conservative (safer) choice for a safety-enforcement context.
    """
    if len(zone_coords) < 3:
        raise ValueError("zone_coords must have at least 3 points to form a polygon.")

    # Shapely uses (x=lon, y=lat) ordering — convert here
    polygon = Polygon([(lon_c, lat_c) for lat_c, lon_c in zone_coords])
    point = Point(lon, lat)  # (x=lon, y=lat)

    return polygon.contains(point) or polygon.boundary.contains(point)


# ---------------------------------------------------------------------------
# Sample restricted zones for prototyping (arbitrary test coordinates).
# Replace with live GPS polygon data from Rashi's MAVLink feed in Week 10.
# ---------------------------------------------------------------------------

SAMPLE_ZONES: dict[str, list[tuple[float, float]]] = {
    "zone_A_storage": [
        # Roughly a 50m × 50m square near test site (placeholder coords)
        (19.0328, 73.0295),
        (19.0328, 73.0300),
        (19.0333, 73.0300),
        (19.0333, 73.0295),
    ],
    "zone_B_machinery_park": [
        (19.0320, 73.0285),
        (19.0320, 73.0292),
        (19.0325, 73.0292),
        (19.0325, 73.0285),
    ],
}


if __name__ == "__main__":
    # Quick smoke test — run python -m cv-model.geofence.restricted_zone
    zone = SAMPLE_ZONES["zone_A_storage"]
    tests = [
        ((19.0330, 73.0297), True,  "inside zone_A"),
        ((19.0310, 73.0270), False, "clearly outside"),
        ((19.0328, 73.0295), True,  "on boundary corner"),
    ]
    for (lat, lon), expected, label in tests:
        result = is_in_restricted_zone(lat, lon, zone)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] {label}: is_in_restricted_zone({lat}, {lon}) = {result}")
