"""
Routing service for Eco-Friendly Routes.
Interacts with the Open Source Routing Machine (OSRM) REST API to retrieve
driving route geometries, distances, and free-flow durations.

Features:
- Configurable base URL (points to public demo server or custom self-hosted instance)
- Supports alternative route discovery (?alternatives=true)
- Translates GeoJSON [longitude, latitude] into Leaflet standard [latitude, longitude]
- Converts meters to kilometers and seconds to minutes
- Documents public server limitations and usage policy
"""
import math
import urllib.request
import urllib.error
import json
from typing import List, Dict, Any, Tuple
from backend.core.config import settings


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two decimal degree points in km."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class RoutingService:
    def __init__(self):
        self.base_url = settings.OSRM_BASE_URL.rstrip("/")
        self.timeout = settings.ROUTING_TIMEOUT_SEC
        self.user_agent = settings.HTTP_USER_AGENT

    def get_driving_routes(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        alternatives: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Queries OSRM for driving routes between origin and destination.
        
        Args:
            origin: (latitude, longitude)
            destination: (latitude, longitude)
            alternatives: Request alternative paths if available in the graph
            
        Returns:
            List of route dicts containing:
            - distance_km (float)
            - duration_min (float)
            - coordinates (List[[lat, lon]])
            - summary (str)
        """
        lat1, lon1 = origin
        lat2, lon2 = destination

        # 1. Validate coordinate ranges and finitude
        if not (math.isfinite(lat1) and math.isfinite(lon1) and math.isfinite(lat2) and math.isfinite(lon2)):
            raise ValueError("Route coordinates must be finite numeric values.")
        if not (-90.0 <= lat1 <= 90.0 and -180.0 <= lon1 <= 180.0):
            raise ValueError(f"Origin coordinates ({lat1}, {lon1}) are out of valid range [-90, 90], [-180, 180].")
        if not (-90.0 <= lat2 <= 90.0 and -180.0 <= lon2 <= 180.0):
            raise ValueError(f"Destination coordinates ({lat2}, {lon2}) are out of valid range [-90, 90], [-180, 180].")

        # 2. Check straight-line distance plausibility
        straight_km = haversine_distance_km(lat1, lon1, lat2, lon2)
        if straight_km < 0.05:
            raise ValueError("Origin and destination are at the same location. Please provide distinct endpoints.")
        if straight_km > settings.MAX_ROUTE_DISTANCE_KM:
            raise ValueError(
                f"Journey straight-line distance ({straight_km:.1f} km) exceeds maximum supported limit "
                f"({settings.MAX_ROUTE_DISTANCE_KM:.0f} km). Please provide endpoints within a connected corridor."
            )

        # OSRM coordinate sequence format is {lon},{lat};{lon},{lat}
        coords_str = f"{lon1:.6f},{lat1:.6f};{lon2:.6f},{lat2:.6f}"
        alt_param = "true" if alternatives else "false"
        url = f"{self.base_url}/route/v1/driving/{coords_str}?overview=full&geometries=geojson&alternatives={alt_param}&steps=false"

        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw_data = resp.read().decode()
                data = json.loads(raw_data)
        except urllib.error.HTTPError as he:
            if he.code == 429:
                raise RuntimeError("OSRM routing service rate limit reached. Please retry in a few seconds.")
            raise RuntimeError(f"OSRM routing service returned HTTP error {he.code}: {he.reason}")
        except urllib.error.URLError as ue:
            raise RuntimeError(f"OSRM routing service connection failed ({self.base_url}): {ue.reason}")
        except json.JSONDecodeError as jde:
            raise RuntimeError(f"OSRM routing service returned malformed non-JSON response: {str(jde)}")
        except Exception as e:
            raise RuntimeError(f"Routing request to OSRM failed ({self.base_url}): {str(e)}")

        if not isinstance(data, dict):
            raise RuntimeError("OSRM routing service returned unexpected data structure (expected JSON object).")

        code = data.get("code")
        if code != "Ok":
            raise RuntimeError(f"OSRM routing engine returned error status: '{code}' (message: {data.get('message', 'No details')})")

        # 3. Validate waypoint snapping distance
        waypoints = data.get("waypoints", [])
        if waypoints and len(waypoints) >= 2:
            orig_snap_m = float(waypoints[0].get("distance", 0.0))
            dest_snap_m = float(waypoints[1].get("distance", 0.0))
            if orig_snap_m > settings.MAX_WAYPOINT_SNAPPING_METERS:
                raise RuntimeError(
                    f"OSRM could not find an accessible road network near origin: "
                    f"closest road is {orig_snap_m / 1000.0:.1f} km away (limit: {settings.MAX_WAYPOINT_SNAPPING_METERS / 1000.0:.1f} km)."
                )
            if dest_snap_m > settings.MAX_WAYPOINT_SNAPPING_METERS:
                raise RuntimeError(
                    f"OSRM could not find an accessible road network near destination: "
                    f"closest road is {dest_snap_m / 1000.0:.1f} km away (limit: {settings.MAX_WAYPOINT_SNAPPING_METERS / 1000.0:.1f} km)."
                )

        raw_routes = data.get("routes", [])
        if not raw_routes or not isinstance(raw_routes, list):
            raise RuntimeError("OSRM routing engine returned 0 routes for the given coordinates.")

        parsed_routes = []
        for idx, r in enumerate(raw_routes):
            meters = float(r.get("distance", 0.0))
            seconds = float(r.get("duration", 0.0))

            dist_km = round(meters / 1000.0, 2)
            dur_min = round(seconds / 60.0, 1)

            if dist_km <= 0.0 or dur_min <= 0.0:
                continue

            # Convert [lon, lat] from GeoJSON to [lat, lon] for Leaflet
            geojson_coords = r.get("geometry", {}).get("coordinates", [])
            leaflet_coords = []
            for pt in geojson_coords:
                if len(pt) >= 2:
                    p_lat = float(pt[1])
                    p_lon = float(pt[0])
                    if math.isfinite(p_lat) and math.isfinite(p_lon) and -90.0 <= p_lat <= 90.0 and -180.0 <= p_lon <= 180.0:
                        leaflet_coords.append([p_lat, p_lon])

            if len(leaflet_coords) < 2:
                continue

            # 4. Validate endpoint connectivity: route start/end must be close to requested coordinates
            start_detour = haversine_distance_km(leaflet_coords[0][0], leaflet_coords[0][1], lat1, lon1)
            end_detour = haversine_distance_km(leaflet_coords[-1][0], leaflet_coords[-1][1], lat2, lon2)
            if start_detour > settings.MAX_ENDPOINT_DETOUR_KM:
                raise RuntimeError(
                    f"Route start point does not reach requested origin "
                    f"({start_detour:.1f} km detour exceeds allowed {settings.MAX_ENDPOINT_DETOUR_KM} km limit)."
                )
            if end_detour > settings.MAX_ENDPOINT_DETOUR_KM:
                raise RuntimeError(
                    f"Route end point does not reach requested destination "
                    f"({end_detour:.1f} km detour exceeds allowed {settings.MAX_ENDPOINT_DETOUR_KM} km limit)."
                )

            summary = ""
            legs = r.get("legs", [])
            if legs and len(legs) > 0:
                summary = legs[0].get("summary", "")
            if not summary:
                summary = f"Corridor {idx + 1}"

            parsed_routes.append({
                "distance_km": dist_km,
                "duration_min": dur_min,
                "coordinates": leaflet_coords,
                "summary": summary,
            })

        if not parsed_routes:
            raise RuntimeError("OSRM returned routes with invalid coordinates or zero distance.")

        return parsed_routes


routing_service = RoutingService()
