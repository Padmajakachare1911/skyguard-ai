# Week 7 — Geofence & Proximity Pytest Results

**Date:** 2026-09-23  
**Issue:** #49 — Test machinery proximity and restricted-zone detection  
**Run command:** `pytest cv-model/tests/test_geofence.py -v`

## Result: 19 passed, 0 failed ✅

```
platform win32 -- Python 3.11.9, pytest-8.2.0
rootdir: C:\Users\Padmaja Kachare\skyguard-ai

collected 19 items

TestRestrictedZone::test_point_clearly_inside                          PASSED
TestRestrictedZone::test_point_clearly_outside                         PASSED
TestRestrictedZone::test_point_on_boundary_edge                        PASSED
TestRestrictedZone::test_point_on_boundary_corner                      PASSED
TestRestrictedZone::test_point_just_outside_edge                       PASSED
TestRestrictedZone::test_invalid_zone_too_few_points                   PASSED
TestRestrictedZone::test_non_convex_zone                               PASSED
TestHaversineDistance::test_same_point_is_zero                         PASSED
TestHaversineDistance::test_known_distance_north_south                 PASSED
TestHaversineDistance::test_short_distance_accuracy                    PASSED
TestMachineryProximityGPS::test_clearly_within_threshold               PASSED
TestMachineryProximityGPS::test_clearly_beyond_threshold               PASSED
TestMachineryProximityGPS::test_distance_greater_than_threshold_no_violation PASSED
TestMachineryProximityGPS::test_distance_less_than_threshold_is_violation    PASSED
TestMachineryProximityPixels::test_bbox_centre                         PASSED
TestMachineryProximityPixels::test_nearby_machinery_is_violation       PASSED
TestMachineryProximityPixels::test_far_machinery_is_not_violation      PASSED
TestMachineryProximityPixels::test_overlapping_bboxes_is_violation     PASSED
TestMachineryProximityPixels::test_identical_bboxes_always_violation   PASSED

19 passed in 0.36s
```

## Coverage

| Module | Tests | Cases Covered |
|---|---|---|
| `geofence/restricted_zone.py` | 7 | Inside, outside, boundary edge, boundary corner, just-outside, invalid input, non-convex polygon |
| `geofence/proximity_check.py` (GPS) | 4 | Clearly within threshold, clearly beyond, distance > threshold, distance < threshold |
| `geofence/proximity_check.py` (haversine) | 3 | Same point = 0, 1° latitude ≈ 111 km, short distance accuracy (3 m ± 0.5 m) |
| `geofence/proximity_check.py` (pixels) | 4 | bbox_centre utility, nearby violation, far no-violation, overlapping, identical |

## Notes

- GPS proximity tests use haversine distance, which is accurate to < 1% for distances under 1 km.
- Pixel-distance fallback is used until Rashi's MAVLink GPS feed is wired in (Week 10).
- Boundary condition for `is_in_restricted_zone`: points on the polygon boundary are treated as **inside** (conservative/safe for enforcement context).
- Boundary condition for `is_machinery_proximity_violation`: strict `<` (not `<=`), so distance exactly equal to threshold is **not** a violation.
