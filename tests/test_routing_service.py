"""
Automated test suite for real routing service, geocoding, distance conversion,
ML emissions integration, and route ranking.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app
from backend.services.geocoding_service import geocoding_service, GeocodingService
from backend.services.routing_service import routing_service, RoutingService
from backend.services.route_service import route_service, RouteService
from backend.models.schemas import RouteRequest, Coordinates


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestGeocodingService:
    """Verifies coordinate parsing, caching, and Nominatim fallbacks."""

    def test_direct_coordinate_parsing(self):
        coords = geocoding_service._parse_direct_coordinates("28.6315, 77.2167")
        assert coords == (28.6315, 77.2167)

        coords_neg = geocoding_service._parse_direct_coordinates("-12.0464, -77.0428")
        assert coords_neg == (-12.0464, -77.0428)

        invalid = geocoding_service._parse_direct_coordinates("Not a coordinate")
        assert invalid is None

    def test_known_landmarks_cache(self):
        cp = geocoding_service.geocode("Connaught Place, Central City")
        assert abs(cp[0] - 28.6315) < 0.01
        assert abs(cp[1] - 77.2167) < 0.01

        ch = geocoding_service.geocode("Cyber Hub, Tech Corridor")
        assert abs(ch[0] - 28.4940) < 0.01
        assert abs(ch[1] - 77.0880) < 0.01

    def test_empty_location_raises_value_error(self):
        with pytest.raises(ValueError):
            geocoding_service.geocode("")

        with pytest.raises(ValueError):
            geocoding_service.geocode("   ")

    def test_unknown_location_never_falls_back_to_unrelated_landmarks(self):
        """Unknown location queries must raise ValueError, NEVER returning unrelated landmarks."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            import io, json
            mock_resp = io.BytesIO(json.dumps([]).encode())
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            svc = GeocodingService()
            with pytest.raises(ValueError, match="Could not find coordinates"):
                svc.geocode("Nonexistent City 987654")

    def test_loose_substring_does_not_hijack_unrelated_query(self):
        """A query containing a word like 'hub' or 'port' must NOT match 'cyber hub' or 'delhi airport'."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            import io, json
            mock_resp = io.BytesIO(json.dumps([]).encode())
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            svc = GeocodingService()
            with pytest.raises(ValueError, match="Could not find coordinates"):
                svc.geocode("Unknown Hub Colony")

    def test_nominatim_rate_limit_and_http_error(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
            url="http://mock", code=429, msg="Too Many Requests", hdrs=None, fp=None
        )):
            svc = GeocodingService()
            with pytest.raises(RuntimeError, match="rate limit"):
                svc.geocode("Some New City")

    def test_nominatim_timeout(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError(reason="timed out")):
            svc = GeocodingService()
            with pytest.raises(RuntimeError, match="connection failed"):
                svc.geocode("Some New City")


class TestRoutingServiceUnitsAndCoordinates:
    """Verifies unit conversions and coordinate translation."""

    def test_coordinate_translation_geojson_to_leaflet(self):
        """OSRM returns [lon, lat] in GeoJSON; Leaflet requires [lat, lon]."""
        mock_osrm_response = {
            "code": "Ok",
            "routes": [
                {
                    "distance": 15450.0,  # meters
                    "duration": 1820.0,   # seconds
                    "geometry": {
                        "coordinates": [
                            [77.2167, 28.6315],
                            [77.1500, 28.5500],
                            [77.0880, 28.4940],
                        ]
                    },
                    "legs": [{"summary": "Ring Road"}]
                }
            ]
        }

        with patch("urllib.request.urlopen") as mock_urlopen:
            import io
            import json
            mock_resp = io.BytesIO(json.dumps(mock_osrm_response).encode())
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            svc = RoutingService()
            routes = svc.get_driving_routes((28.6315, 77.2167), (28.4940, 77.0880))

            assert len(routes) == 1
            r = routes[0]
            assert r["distance_km"] == 15.45  # 15450 / 1000
            assert r["duration_min"] == 30.3   # 1820 / 60 = 30.33 -> 30.3
            assert r["summary"] == "Ring Road"

            # Check Leaflet [lat, lon] order
            assert r["coordinates"][0] == [28.6315, 77.2167]
            assert r["coordinates"][-1] == [28.4940, 77.0880]

    def test_osrm_timeout_handling(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError(reason="Connection timed out")):
            svc = RoutingService()
            with pytest.raises(RuntimeError, match="connection failed"):
                svc.get_driving_routes((28.6315, 77.2167), (28.4940, 77.0880))

    def test_osrm_rate_limit_429(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
            url="http://mock", code=429, msg="Too Many Requests", hdrs=None, fp=None
        )):
            svc = RoutingService()
            with pytest.raises(RuntimeError, match="rate limit"):
                svc.get_driving_routes((28.6315, 77.2167), (28.4940, 77.0880))

    def test_osrm_malformed_json_response(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            import io
            mock_resp = io.BytesIO(b"<!DOCTYPE html><html>502 Bad Gateway</html>")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            svc = RoutingService()
            with pytest.raises(RuntimeError, match="malformed non-JSON"):
                svc.get_driving_routes((28.6315, 77.2167), (28.4940, 77.0880))

    def test_osrm_error_code_response(self):
        mock_err = {"code": "NoRoute", "message": "No route found between points"}
        with patch("urllib.request.urlopen") as mock_urlopen:
            import io, json
            mock_resp = io.BytesIO(json.dumps(mock_err).encode())
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            svc = RoutingService()
            with pytest.raises(RuntimeError, match="error status: 'NoRoute'"):
                svc.get_driving_routes((28.6315, 77.2167), (28.4940, 77.0880))

    def test_osrm_empty_routes_list(self):
        mock_empty = {"code": "Ok", "routes": []}
        with patch("urllib.request.urlopen") as mock_urlopen:
            import io, json
            mock_resp = io.BytesIO(json.dumps(mock_empty).encode())
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            svc = RoutingService()
            with pytest.raises(RuntimeError, match="returned 0 routes"):
                svc.get_driving_routes((28.6315, 77.2167), (28.4940, 77.0880))


import asyncio


class TestRouteServiceEmissionsAndRanking:
    """Verifies emissions calculation, ranking, and alternative route comparison."""

    def test_route_comparison_calculation_gasoline(self):
        req = RouteRequest(
            origin_name="Connaught Place, Central City",
            destination_name="Cyber Hub, Tech Corridor",
            origin_coords=Coordinates(latitude=28.6315, longitude=77.2167),
            destination_coords=Coordinates(latitude=28.4940, longitude=77.0880),
            vehicle_type="gasoline"
        )

        res = asyncio.run(route_service.get_route_comparison(req))
        assert len(res.routes) >= 1
        assert res.routing_provider == "OSRM (Open Source Routing Machine)"
        assert res.recommended_route_id is not None
        assert res.fastest_route_id is not None

        # Verify recommended route has lowest emissions
        recommended = next(r for r in res.routes if r.is_recommended)
        assert recommended.rank == 1
        assert recommended.emission_estimate.co2_grams > 0

        # Verify formula: co2_grams == round(rate * distance, 2)
        rate = recommended.emission_estimate.co2_grams / recommended.distance_km
        assert rate > 150.0  # Certified mid-size car rate is ~195-205 g/km

    def test_route_comparison_ev_zero_tailpipe(self):
        req = RouteRequest(
            origin_name="Connaught Place, Central City",
            destination_name="Cyber Hub, Tech Corridor",
            origin_coords=Coordinates(latitude=28.6315, longitude=77.2167),
            destination_coords=Coordinates(latitude=28.4940, longitude=77.0880),
            vehicle_type="ev"
        )

        res = asyncio.run(route_service.get_route_comparison(req))
        for r in res.routes:
            assert r.emission_estimate.co2_grams == 0.0
            assert r.eco_score == 100
            assert r.eco_score_grade == "A+"
            assert r.emission_estimate.energy_kwh is not None

    def test_multi_route_ranking_and_savings(self):
        """Simulates 2 OSRM routes where Route 1 is faster but longer, and Route 2 is shorter/greener."""
        mock_routes = [
            {
                "distance_km": 25.0,
                "duration_min": 25.0,  # Faster
                "coordinates": [[28.63, 77.21], [28.49, 77.08]],
                "summary": "Expressway",
            },
            {
                "distance_km": 20.0,  # Shorter -> Less CO2
                "duration_min": 30.0,
                "coordinates": [[28.63, 77.21], [28.49, 77.08]],
                "summary": "Direct Arterial",
            }
        ]

        with patch.object(routing_service, "get_driving_routes", return_value=mock_routes):
            req = RouteRequest(
                origin_name="Test Origin",
                destination_name="Test Dest",
                origin_coords=Coordinates(latitude=28.63, longitude=77.21),
                destination_coords=Coordinates(latitude=28.49, longitude=77.08),
                vehicle_type="gasoline"
            )

            res = asyncio.run(route_service.get_route_comparison(req))
            assert len(res.routes) == 2

            # Route 2 (20 km) should be recommended because it has lower emissions
            rec = next(r for r in res.routes if r.is_recommended)
            assert rec.distance_km == 20.0
            assert rec.rank == 1

            # Route 1 (25 min) should be marked fastest
            fast = next(r for r in res.routes if r.is_fastest)
            assert fast.distance_km == 25.0
            assert fast.duration_min == 25.0

            # Saving percent: (25km - 20km) / 25km = 20%
            assert res.eco_saving_percent == 20.0

    def test_single_route_returned_handles_transparently(self):
        mock_single_route = [
            {
                "distance_km": 15.0,
                "duration_min": 25.0,
                "coordinates": [[28.63, 77.21], [28.49, 77.08]],
                "summary": "Sole Highway",
            }
        ]

        with patch.object(routing_service, "get_driving_routes", return_value=mock_single_route):
            req = RouteRequest(
                origin_name="Connaught Place, Central City",
                destination_name="Cyber Hub, Tech Corridor",
                vehicle_type="gasoline"
            )
            res = asyncio.run(route_service.get_route_comparison(req))
            assert len(res.routes) == 1
            assert res.routes[0].is_recommended is True
            assert res.routes[0].is_fastest is True
            assert res.eco_saving_percent == 0.0
            assert "1 optimal path" in res.notice

    def test_ev_route_energy_savings_and_zero_division_protection(self):
        mock_routes = [
            {
                "distance_km": 30.0,
                "duration_min": 20.0,
                "coordinates": [[28.63, 77.21], [28.49, 77.08]],
                "summary": "Expressway",
            },
            {
                "distance_km": 20.0,
                "duration_min": 28.0,
                "coordinates": [[28.63, 77.21], [28.49, 77.08]],
                "summary": "Direct Shorter Corridor",
            }
        ]

        with patch.object(routing_service, "get_driving_routes", return_value=mock_routes):
            req = RouteRequest(
                origin_name="Connaught Place, Central City",
                destination_name="Cyber Hub, Tech Corridor",
                vehicle_type="ev"
            )
            res = asyncio.run(route_service.get_route_comparison(req))
            assert len(res.routes) == 2
            # EV direct tailpipe emissions must be 0 for both routes
            for r in res.routes:
                assert r.emission_estimate.co2_grams == 0.0
                assert r.emission_estimate.energy_kwh is not None
            # Shorter corridor should be recommended
            rec = next(r for r in res.routes if r.is_recommended)
            assert rec.distance_km == 20.0
            assert rec.emission_estimate.energy_kwh == 3.6  # 20 * 0.18

            # Energy saving: (30 - 20) / 30 = 33.3%
            assert res.eco_saving_percent == 33.3

    def test_ev_identical_distance_zero_division_guard(self):
        mock_routes = [
            {
                "distance_km": 20.0,
                "duration_min": 20.0,
                "coordinates": [[28.63, 77.21], [28.49, 77.08]],
                "summary": "Route A",
            },
            {
                "distance_km": 20.0,
                "duration_min": 25.0,
                "coordinates": [[28.63, 77.21], [28.49, 77.08]],
                "summary": "Route B",
            }
        ]

        with patch.object(routing_service, "get_driving_routes", return_value=mock_routes):
            req = RouteRequest(
                origin_name="Connaught Place, Central City",
                destination_name="Cyber Hub, Tech Corridor",
                vehicle_type="ev"
            )
            res = asyncio.run(route_service.get_route_comparison(req))
            assert res.eco_saving_percent == 0.0


class TestRoutesFastAPIEndpoint:
    """Verifies the /api/v1/routes/compare HTTP endpoint."""

    def test_compare_endpoint_success(self, client):
        payload = {
            "origin_name": "Connaught Place, Central City",
            "destination_name": "Cyber Hub, Tech Corridor",
            "vehicle_type": "gasoline"
        }
        resp = client.post("/api/v1/routes/compare", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "routes" in data
        assert len(data["routes"]) >= 1
        assert "routing_provider" in data
        assert "limitations_note" in data
        assert data["routes"][0]["distance_km"] > 0
        assert data["routes"][0]["duration_min"] > 0
        assert data["routes"][0]["emission_estimate"]["co2_grams"] > 0

    def test_compare_endpoint_invalid_location(self, client):
        payload = {
            "origin_name": "ZZZZZZZZ_NonExistent_Invalid_City_12345",
            "destination_name": "Cyber Hub, Tech Corridor",
            "vehicle_type": "gasoline"
        }
        resp = client.post("/api/v1/routes/compare", json=payload)
        assert resp.status_code == 422

    def test_compare_endpoint_handles_osrm_service_unavailable(self, client):
        with patch.object(routing_service, "get_driving_routes", side_effect=RuntimeError("OSRM connection timeout")):
            payload = {
                "origin_name": "Connaught Place, Central City",
                "destination_name": "Cyber Hub, Tech Corridor",
                "vehicle_type": "gasoline"
            }
            resp = client.post("/api/v1/routes/compare", json=payload)
            assert resp.status_code == 503
            assert "OSRM connection timeout" in resp.json()["detail"]


class TestRoutingIntegrityAndRegression:
    """
    Regression test suite ensuring:
    - Inputs 'g' and 'test address 999' are strictly rejected with 422/ValidationError.
    - No silent fallbacks to benchmark landmarks or default coordinates.
    - Swapped, out-of-bounds, and excessive detour routes are blocked.
    - Failed queries never return stale or demo routes.
    - Emissions calculations follow exact distance * ML rate formula.
    """

    def test_single_letter_g_rejected(self, client):
        # 1. Direct geocoding rejection
        with pytest.raises(ValueError, match="too short or ambiguous"):
            geocoding_service.geocode("g")

        # 2. Schema rejection
        with pytest.raises(Exception):
            RouteRequest(origin_name="g", destination_name="Cyber Hub, Tech Corridor")

        # 3. HTTP endpoint rejection (HTTP 422)
        resp = client.post("/api/v1/routes/compare", json={
            "origin_name": "g",
            "destination_name": "Cyber Hub, Tech Corridor",
            "vehicle_type": "gasoline"
        })
        assert resp.status_code == 422
        err_msg = str(resp.json())
        assert "too short or ambiguous" in err_msg

    def test_test_address_999_rejected(self, client):
        # 1. Direct geocoding rejection
        with pytest.raises(ValueError, match="test or placeholder string"):
            geocoding_service.geocode("test address 999")

        # 2. Schema rejection
        with pytest.raises(Exception):
            RouteRequest(origin_name="Connaught Place, Central City", destination_name="test address 999")

        # 3. HTTP endpoint rejection (HTTP 422)
        resp = client.post("/api/v1/routes/compare", json={
            "origin_name": "Connaught Place, Central City",
            "destination_name": "test address 999",
            "vehicle_type": "gasoline"
        })
        assert resp.status_code == 422
        err_msg = str(resp.json())
        assert "placeholder or test string" in err_msg

    def test_unknown_destination_raises_422_without_fallback(self, client):
        with patch("urllib.request.urlopen") as mock_urlopen:
            import io, json
            mock_resp = io.BytesIO(json.dumps([]).encode())
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            resp = client.post("/api/v1/routes/compare", json={
                "origin_name": "Connaught Place, Central City",
                "destination_name": "Unknown Nowhere Lost Colony 77777",
                "vehicle_type": "gasoline"
            })
            assert resp.status_code == 422
            data = resp.json()
            assert "Could not find coordinates" in data["detail"]
            # Ensure no routes array is present in error response
            assert "routes" not in data

    def test_out_of_bounds_coordinates_rejected(self):
        # Latitude > 90
        with pytest.raises(ValueError, match="exceeds latitude range|out of valid range"):
            geocoding_service._parse_direct_coordinates("95.0, 77.0")

        # Longitude > 180
        with pytest.raises(ValueError, match="out of valid range"):
            geocoding_service._parse_direct_coordinates("28.6, 185.0")

        # Pydantic schema rejection
        with pytest.raises(Exception):
            Coordinates(latitude=95.0, longitude=77.0)

    def test_swapped_coordinates_detected(self):
        # 120.5 is latitude > 90, 28.6 is longitude <= 90
        with pytest.raises(ValueError, match="Coordinates appear swapped"):
            geocoding_service._parse_direct_coordinates("120.5, 28.6")

    def test_identical_origin_and_destination_rejected(self, client):
        resp = client.post("/api/v1/routes/compare", json={
            "origin_name": "Connaught Place, Central City",
            "destination_name": "Connaught Place, Central City",
            "vehicle_type": "gasoline"
        })
        assert resp.status_code == 422
        assert "cannot be the same" in str(resp.json())

    def test_excessive_straight_line_distance_safeguard(self):
        """Straight-line distance exceeding 3,000 km (e.g. Poland to Nigeria 5,468 km) is rejected immediately."""
        svc = RoutingService()
        with pytest.raises(ValueError, match="exceeds maximum supported limit"):
            svc.get_driving_routes((54.2455, 18.1099), (6.5244, 3.3792))

    def test_osrm_endpoint_detour_safeguard(self):
        """Simulates OSRM snapping to a distant road or returning endpoints detouring far from queried location."""
        origin = (28.6315, 77.2167)
        destination = (28.4940, 77.0880)

        mock_distant_osrm_route = {
            "code": "Ok",
            "routes": [
                {
                    "distance": 85000.0,
                    "duration": 5400.0,
                    "geometry": {
                        "coordinates": [
                            [77.2167, 28.6315],  # Origin
                            [77.8000, 29.2000],  # Detoured 80 km away from destination!
                        ]
                    },
                    "legs": [{"summary": "Detoured Out of Corridor Way"}]
                }
            ],
            "waypoints": [
                {"location": [77.2167, 28.6315], "distance": 12.0},
                {"location": [77.8000, 29.2000], "distance": 85000.0}  # 85 km snap!
            ]
        }

        with patch("urllib.request.urlopen") as mock_urlopen:
            import io, json
            mock_resp = io.BytesIO(json.dumps(mock_distant_osrm_route).encode())
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            svc = RoutingService()
            with pytest.raises(RuntimeError, match="closest road is|snapping distance|detour"):
                svc.get_driving_routes(origin, destination)

    def test_stale_results_not_returned_on_failure(self, client):
        # 1. Successful request
        valid_payload = {
            "origin_name": "Connaught Place, Central City",
            "destination_name": "Cyber Hub, Tech Corridor",
            "vehicle_type": "gasoline"
        }
        resp1 = client.post("/api/v1/routes/compare", json=valid_payload)
        assert resp1.status_code == 200
        assert len(resp1.json()["routes"]) >= 1

        # 2. Failed request with invalid address
        invalid_payload = {
            "origin_name": "g",
            "destination_name": "Cyber Hub, Tech Corridor",
            "vehicle_type": "gasoline"
        }
        resp2 = client.post("/api/v1/routes/compare", json=invalid_payload)
        assert resp2.status_code == 422
        # Verify resp2 has no routes or fallback
        assert "routes" not in resp2.json()

    def test_valid_response_emissions_formula(self, client):
        payload = {
            "origin_name": "Connaught Place, Central City",
            "destination_name": "Cyber Hub, Tech Corridor",
            "vehicle_type": "gasoline"
        }
        resp = client.post("/api/v1/routes/compare", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["routes"]) >= 1

        from ml.predict import emissions_predictor
        pred_meta = emissions_predictor.predict({"vehicle_type": "gasoline"}, distance_km=1.0)
        rate_g_per_km = pred_meta["predicted_co2_g_per_km"]

        for r in data["routes"]:
            dist = r["distance_km"]
            expected_co2 = round(dist * rate_g_per_km, 2)
            actual_co2 = r["emission_estimate"]["co2_grams"]
            assert abs(actual_co2 - expected_co2) < 0.1

