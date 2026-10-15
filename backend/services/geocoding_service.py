"""
Geocoding service for Eco-Friendly Routes.
Resolves human-readable addresses or city names to geographic coordinates [latitude, longitude].

Supports:
- Direct coordinate string parsing (e.g. "28.6315, 77.2167")
- In-memory LRU cache to respect OpenStreetMap Nominatim 1 req/sec policy
- Built-in location registry for common benchmark corridors
- OpenStreetMap Nominatim HTTP lookup with custom User-Agent and timeout
"""
import math
import re
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Tuple, Optional, Dict
from backend.core.config import settings

# Pre-populated cache of known demonstration and benchmark landmarks
KNOWN_LOCATIONS: Dict[str, Tuple[float, float]] = {
    "connaught place": (28.6315, 77.2167),
    "connaught place, central city": (28.6315, 77.2167),
    "connaught place, new delhi": (28.6318, 77.2194),
    "cyber hub": (28.4940, 77.0880),
    "cyber hub, tech corridor": (28.4940, 77.0880),
    "cyber hub, gurugram": (28.4951, 77.0885),
    "dlf cyber hub": (28.4951, 77.0885),
    "india gate": (28.6129, 77.2295),
    "qutub minar": (28.5244, 77.1855),
    "red fort": (28.6562, 77.2410),
    "delhi airport": (28.5562, 77.1000),
    "noida sector 18": (28.5708, 77.3260),
    "paris": (48.8566, 2.3522),
    "versailles": (48.8049, 2.1301),
    "london": (51.5074, -0.1278),
    "greenwich": (51.4826, 0.0000),
}


class GeocodingService:
    def __init__(self):
        self.cache: Dict[str, Tuple[float, float]] = dict(KNOWN_LOCATIONS)
        self.base_url = settings.NOMINATIM_BASE_URL
        self.timeout = settings.ROUTING_TIMEOUT_SEC
        self.user_agent = settings.HTTP_USER_AGENT

    def _parse_direct_coordinates(self, text: str) -> Optional[Tuple[float, float]]:
        """Parses direct 'lat, lon' or 'lat lon' strings, detecting swapped or invalid coordinates."""
        clean = text.strip()
        num_pattern = r"^[-+]?\d+(\.\d+)?[,\s]+[-+]?\d+(\.\d+)?$"
        if re.match(num_pattern, clean):
            parts = re.split(r"[,\s]+", clean)
            if len(parts) >= 2:
                try:
                    p1 = float(parts[0])
                    p2 = float(parts[1])
                    if not (math.isfinite(p1) and math.isfinite(p2)):
                        raise ValueError("Coordinate values must be finite numbers.")
                    
                    # Detect swapped coordinates (latitude outside [-90, 90] but valid longitude)
                    if (abs(p1) > 90.0 and abs(p1) <= 180.0) and abs(p2) <= 90.0:
                        raise ValueError(
                            f"Invalid coordinate: first value {p1} exceeds latitude range [-90, 90]. "
                            f"Coordinates appear swapped (did you mean latitude {p2}, longitude {p1}?)"
                        )
                    
                    # Out of bounds check
                    if abs(p1) > 90.0 or abs(p2) > 180.0:
                        raise ValueError(
                            f"Coordinates ({p1}, {p2}) out of valid range: latitude must be [-90, 90], longitude [-180, 180]."
                        )
                    
                    return (p1, p2)
                except ValueError as ve:
                    if "exceeds latitude range" in str(ve) or "out of valid range" in str(ve) or "must be finite" in str(ve):
                        raise
                    return None
        return None

    @staticmethod
    def _normalize_key(text: str) -> str:
        """Normalizes a location name for exact dictionary lookup."""
        return re.sub(r"\s+", " ", text.lower().strip().strip(".,;:"))

    def geocode(self, location_name: str) -> Tuple[float, float]:
        """
        Resolves location name to (latitude, longitude).
        Raises ValueError if location cannot be resolved.
        """
        if not location_name or not location_name.strip():
            raise ValueError("Location name cannot be empty.")

        query = location_name.strip()

        # 1. Reject inputs that are too short, empty, or pure symbols
        alnum_chars = re.findall(r"[a-zA-Z0-9]", query)
        if len(alnum_chars) < 2:
            raise ValueError(
                f"Location query '{query}' is too short or ambiguous. "
                "Please enter at least 2 alphanumeric characters representing a recognized place."
            )

        # 2. Reject obvious test or placeholder queries
        dummy_patterns = [
            r"\btest\s+address\b",
            r"\bfake\s+address\b",
            r"\bdummy\s+address\b",
            r"\bsample\s+address\b",
            r"\bplaceholder\b",
            r"\btest\s*\d+\b",
        ]
        if any(re.search(pat, query, re.IGNORECASE) for pat in dummy_patterns):
            raise ValueError(f"Location query '{query}' is a test or placeholder string, not a valid real-world location.")

        # 3. Direct coordinate parsing (detects swapped/invalid coordinates)
        direct = self._parse_direct_coordinates(query)
        if direct:
            return direct

        norm_key = self._normalize_key(query)

        # 4. Check explicit documented landmark shortcuts & in-memory cache (exact match only)
        if norm_key in self.cache:
            return self.cache[norm_key]

        # 5. Remote Nominatim Query
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"{self.base_url}/search?q={encoded_query}&format=json&limit=1&addressdetails=1"
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw_data = resp.read().decode()
                data = json.loads(raw_data)
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    # Validate that the geocoded result actually matches the query
                    result_text = (data[0].get("display_name", "") + " " + data[0].get("name", "")).lower()
                    query_tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9]+", query) if len(t) >= 2]
                    if query_tokens and not any(token in result_text for token in query_tokens):
                        raise ValueError(
                            f"Could not reliably verify location for '{query}'. "
                            f"Geocoding matched unrelated location '{data[0].get('display_name', '')}'. "
                            "Please provide a more specific address or exact coordinates (lat, lon)."
                        )

                    lat = float(data[0].get("lat"))
                    lon = float(data[0].get("lon"))
                    if not (math.isfinite(lat) and math.isfinite(lon) and -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                        raise ValueError(f"Geocoding returned invalid coordinate values ({lat}, {lon}) for '{query}'.")

                    coords = (lat, lon)
                    self.cache[norm_key] = coords
                    return coords
        except urllib.error.HTTPError as he:
            if he.code == 429:
                raise RuntimeError("Geocoding rate limit reached (OSM Nominatim 1 req/sec policy). Please retry shortly.")
            raise RuntimeError(f"Geocoding service HTTP error {he.code}: {he.reason}")
        except urllib.error.URLError as ue:
            raise RuntimeError(f"Geocoding service connection failed: {ue.reason}")
        except Exception as e:
            if isinstance(e, (RuntimeError, ValueError)):
                raise
            raise RuntimeError(f"Geocoding request failed for '{query}': {str(e)}")

        raise ValueError(
            f"Could not find coordinates for location '{query}'. "
            "Please provide a more specific address or exact coordinates (lat, lon)."
        )


geocoding_service = GeocodingService()
