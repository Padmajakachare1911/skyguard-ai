import math


class Geofence:
    """
    Circular geofence for GPS-based restricted-zone detection.

    The geofence is defined by:
        center_lat : Center latitude
        center_lon : Center longitude
        radius_m   : Radius of the restricted zone in meters
    """

    EARTH_RADIUS_M = 6371000.0

    def __init__(self, center_lat, center_lon, radius_m):
        self.center_lat = float(center_lat)
        self.center_lon = float(center_lon)
        self.radius_m = float(radius_m)

        # Previous state of the drone.
        # None means no GPS position has been processed yet.
        self.previous_inside = None

    def calculate_distance(self, latitude, longitude):
        """
        Calculate the distance between the drone's current
        GPS position and the center of the geofence.

        Uses the Haversine formula.

        Returns:
            Distance in meters.
        """

        latitude = float(latitude)
        longitude = float(longitude)

        lat1 = math.radians(self.center_lat)
        lat2 = math.radians(latitude)

        delta_lat = math.radians(
            latitude - self.center_lat
        )

        delta_lon = math.radians(
            longitude - self.center_lon
        )

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(delta_lon / 2) ** 2
        )

        # Protect against floating-point errors.
        a = max(0.0, min(1.0, a))

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        distance = self.EARTH_RADIUS_M * c

        return distance

    def check_position(self, latitude, longitude):
        """
        Check whether the drone is inside or outside
        the restricted zone.

        Returns:
            {
                "inside": True/False,
                "distance_m": distance,
                "event": None/"ZONE_ENTRY"/"ZONE_EXIT"
            }
        """

        # Calculate distance from geofence center.
        distance_m = self.calculate_distance(
            latitude,
            longitude
        )

        # Determine current zone status.
        current_inside = distance_m <= self.radius_m

        event = None

        # ----------------------------------------------------
        # First GPS reading
        # ----------------------------------------------------
        #
        # We establish the initial state but do NOT generate
        # an entry/exit alert on the first reading.
        #
        if self.previous_inside is None:

            self.previous_inside = current_inside

        else:

            # ------------------------------------------------
            # Outside -> Inside
            # ------------------------------------------------

            if (
                not self.previous_inside
                and current_inside
            ):
                event = "ZONE_ENTRY"


            # ------------------------------------------------
            # Inside -> Outside
            # ------------------------------------------------

            elif (
                self.previous_inside
                and not current_inside
            ):
                event = "ZONE_EXIT"


            # Update previous state.
            self.previous_inside = current_inside

        return {
            "inside": current_inside,
            "distance_m": distance_m,
            "event": event
        }