from abc import ABC, abstractmethod
from typing import Dict, Any


class RoutingAdapter(ABC):
    @abstractmethod
    def calculate_eta(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> Dict[str, Any]:
        """
        Calculates distance and estimated time of arrival.
        """
        pass


class BasicRoutingAdapter(RoutingAdapter):
    """
    Standard V1 straight-line distance & estimated city transit speed model (25 km/h avg).
    Clearly communicates approx ETA without external API billing/keys.
    """
    AVERAGE_CITY_SPEED_KMH = 25.0

    @classmethod
    def calculate_distance_km(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        import math
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    def calculate_eta(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> Dict[str, Any]:
        dist_km = self.calculate_distance_km(origin_lat, origin_lon, dest_lat, dest_lon)
        # Approximate travel time in minutes: (dist / speed) * 60 + 5 mins buffer
        approx_minutes = max(5, int(round((dist_km / self.AVERAGE_CITY_SPEED_KMH) * 60) + 5))

        return {
            "distance_km": dist_km,
            "estimated_duration_minutes": approx_minutes,
            "is_approximate": True,
            "provider": "Haazir V1 Basic Routing"
        }
