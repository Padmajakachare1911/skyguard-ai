"""
tests/test_geofence.py — SkyGuard AI CV-Model pytest suite
------------------------------------------------------------
Tests for restricted_zone.py and proximity_check.py.

Run with:  pytest cv-model/tests/ -v

Week 7 (#49) deliverable.
"""

import math
import sys
from pathlib import Path

# Allow imports from cv-model/ without installing as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from geofence.restricted_zone import is_in_restricted_zone
from geofence.proximity_check import (
    haversine_distance_m,
    is_machinery_proximity_violation,
    is_machinery_proximity_violation_pixels,
    bbox_centre,
)


# ===========================================================================
# Shared test fixtures
# ===========================================================================

# A simple square zone: roughly 100m × 100m at a Mumbai test coordinate
SQUARE_ZONE = [
    (19.0325, 73.0290),  # bottom-left
    (19.0325, 73.0300),  # bottom-right
    (19.0335, 73.0300),  # top-right
    (19.0335, 73.0290),  # top-left
]


# ===========================================================================
# restricted_zone.py tests
# ===========================================================================

class TestRestrictedZone:

    def test_point_clearly_inside(self):
        """Point at the centre of the square — must return True."""
        lat, lon = 19.0330, 73.0295  # centre of SQUARE_ZONE
        assert is_in_restricted_zone(lat, lon, SQUARE_ZONE) is True

    def test_point_clearly_outside(self):
        """Point far from the zone — must return False."""
        lat, lon = 19.0100, 73.0100  # several km away
        assert is_in_restricted_zone(lat, lon, SQUARE_ZONE) is False

    def test_point_on_boundary_edge(self):
        """
        Point on the bottom edge of the zone.
        Conservative safety choice: boundary counts as inside.
        """
        lat, lon = 19.0325, 73.0295  # on the bottom edge, not a corner
        result = is_in_restricted_zone(lat, lon, SQUARE_ZONE)
        assert result is True

    def test_point_on_boundary_corner(self):
        """Point exactly on a corner vertex."""
        lat, lon = SQUARE_ZONE[0]  # exact corner
        result = is_in_restricted_zone(lat, lon, SQUARE_ZONE)
        assert result is True

    def test_point_just_outside_edge(self):
        """Point just 1 mm south of the bottom edge — must return False."""
        lat = 19.0325 - 0.000001  # ~0.1 m south
        lon = 73.0295
        assert is_in_restricted_zone(lat, lon, SQUARE_ZONE) is False

    def test_invalid_zone_too_few_points(self):
        """Fewer than 3 points must raise ValueError."""
        with pytest.raises(ValueError, match="at least 3 points"):
            is_in_restricted_zone(19.0330, 73.0295, [(19.0, 73.0), (19.1, 73.1)])

    def test_non_convex_zone(self):
        """
        L-shaped (non-convex) zone.
        The L opens to the bottom-right: the cut-out corner (top-right) is outside.
        Polygon vertices listed counter-clockwise to form a valid L:

             lon→  0.000   0.010   0.020
        lat  0.020  ┌───┐
          ↓  0.010  │   └───┐
             0.000  └───────┘
        """
        l_zone = [
            (19.0000, 73.0000),  # bottom-left
            (19.0000, 73.0020),  # bottom-right
            (19.0010, 73.0020),  # middle-right
            (19.0010, 73.0010),  # inner corner
            (19.0020, 73.0010),  # top-right of left arm
            (19.0020, 73.0000),  # top-left
        ]
        # Point in the cut-out (top-right quadrant): lat=19.0015, lon=73.0015
        # This is east of the inner corner and above the bottom of the right arm
        # — outside the L polygon.
        assert is_in_restricted_zone(19.0015, 73.0015, l_zone) is False
        # Point clearly inside the left arm of the L
        assert is_in_restricted_zone(19.0015, 73.0005, l_zone) is True


# ===========================================================================
# proximity_check.py tests — haversine
# ===========================================================================

class TestHaversineDistance:

    def test_same_point_is_zero(self):
        d = haversine_distance_m(19.0330, 73.0297, 19.0330, 73.0297)
        assert d == pytest.approx(0.0, abs=1e-6)

    def test_known_distance_north_south(self):
        """1 degree of latitude ≈ 111 km."""
        d = haversine_distance_m(0.0, 0.0, 1.0, 0.0)
        assert d == pytest.approx(111_195, rel=0.01)

    def test_short_distance_accuracy(self):
        """3 m north: 0.000027 degrees latitude ≈ 3 m."""
        d = haversine_distance_m(19.0330, 73.0297, 19.0330270, 73.0297)
        assert d == pytest.approx(3.0, abs=0.5)


class TestMachineryProximityGPS:

    def test_clearly_within_threshold(self):
        """Person 3 m from machinery, threshold 5 m → violation."""
        assert is_machinery_proximity_violation(
            19.0330, 73.0297,
            19.0330270, 73.0297,
            threshold_m=5.0,
        ) is True

    def test_clearly_beyond_threshold(self):
        """Person 20 m from machinery, threshold 5 m → no violation."""
        assert is_machinery_proximity_violation(
            19.0330, 73.0297,
            19.0332, 73.0297,  # ~22 m north
            threshold_m=5.0,
        ) is False

    def test_distance_greater_than_threshold_no_violation(self):
        """
        Person is further from machinery than the threshold → no violation.
        Set threshold 1 m BELOW the actual distance → distance > threshold → False.
        """
        d = haversine_distance_m(19.0330, 73.0297, 19.0330450, 73.0297)
        # threshold is 1 m less than the actual distance → person is too far → False
        result = is_machinery_proximity_violation(
            19.0330, 73.0297, 19.0330450, 73.0297, threshold_m=d - 1.0
        )
        assert result is False

    def test_distance_less_than_threshold_is_violation(self):
        """
        Person is closer to machinery than the threshold → violation.
        Set threshold 1 m ABOVE the actual distance → distance < threshold → True.
        """
        d = haversine_distance_m(19.0330, 73.0297, 19.0330450, 73.0297)
        # threshold is 1 m more than the actual distance → person is within zone → True
        result = is_machinery_proximity_violation(
            19.0330, 73.0297, 19.0330450, 73.0297, threshold_m=d + 1.0
        )
        assert result is True


# ===========================================================================
# proximity_check.py tests — pixel fallback
# ===========================================================================

class TestMachineryProximityPixels:

    def test_bbox_centre(self):
        assert bbox_centre((100, 200, 200, 400)) == (150.0, 300.0)

    def test_nearby_machinery_is_violation(self):
        person   = (100, 100, 200, 300)   # centre (150, 200)
        machinery = (210, 100, 350, 300)  # centre (280, 200) → dist = 130 px
        assert is_machinery_proximity_violation_pixels(person, machinery, threshold_px=150.0) is True

    def test_far_machinery_is_not_violation(self):
        person   = (100, 100, 200, 300)   # centre (150, 200)
        machinery = (500, 100, 700, 300)  # centre (600, 200) → dist = 450 px
        assert is_machinery_proximity_violation_pixels(person, machinery, threshold_px=150.0) is False

    def test_overlapping_bboxes_is_violation(self):
        """
        Overlapping boxes: centres are (200,250) and (250,300) → dist ≈ 70 px.
        Use threshold_px=200 to confirm the violation fires.
        """
        person    = (100, 100, 300, 400)   # centre (200, 250)
        machinery = (150, 150, 350, 450)   # centre (250, 300) → dist ≈ 70 px
        assert is_machinery_proximity_violation_pixels(person, machinery, threshold_px=200.0) is True

    def test_identical_bboxes_always_violation(self):
        """
        Identical boxes → distance = 0 → 0 < any positive threshold → always a violation.
        A threshold_px of 0.0 would not trigger (0 is not < 0), but any positive value does.
        """
        box = (100, 100, 300, 400)
        # distance = 0, threshold = 0.001 → 0 < 0.001 → True
        assert is_machinery_proximity_violation_pixels(box, box, threshold_px=0.001) is True
        assert is_machinery_proximity_violation_pixels(box, box, threshold_px=1.0) is True
