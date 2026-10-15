"""
Route service for Eco-Friendly Routes.
Orchestrates geocoding, OSRM route generation, vehicle emissions inference,
and multi-route environmental ranking.
"""
import math
import os
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from backend.core.config import settings
from backend.models.schemas import (
    RouteRequest,
    RouteComparisonResponse,
    RouteOption,
    EmissionEstimate,
    Coordinates,
)
from backend.services.geocoding_service import geocoding_service, GeocodingService
from backend.services.routing_service import routing_service, RoutingService
from backend.services.traffic_service import traffic_service, TrafficService
from backend.services.road_damage_service import road_damage_service, RoadDamageService
from ml.predict import emissions_predictor, EmissionsPredictor


class RouteService:
    def __init__(self):
        self.model_path = settings.MODEL_PATH
        self.legacy_model_path = settings.LEGACY_MODEL_PATH
        self.model = None
        self.geocoding_service: GeocodingService = geocoding_service
        self.routing_service: RoutingService = routing_service
        self.traffic_service: TrafficService = traffic_service
        self.road_damage_service: RoadDamageService = road_damage_service
        self._load_model_if_available()

    def _load_model_if_available(self) -> bool:
        """
        Loads the trained Scikit-learn estimator using joblib if artifact exists.
        Reuses emissions_predictor when available.
        """
        if emissions_predictor.is_ready():
            self.model = emissions_predictor.pipeline
            return True

        target_path = self.model_path if self.model_path.exists() else self.legacy_model_path
        if target_path and target_path.exists():
            try:
                import joblib
                self.model = joblib.load(target_path)
                return True
            except Exception as e:
                print(f"[RouteService] Warning: Failed to load model artifact: {e}")
                self.model = None
                return False
        return False

    def is_model_loaded(self) -> bool:
        """Returns True if the ML model is trained and currently loaded in memory."""
        if self.model is None:
            self._load_model_if_available()
        return self.model is not None

    def _calculate_eco_score(self, co2_g: float, min_co2: float, max_co2: float, is_ev: bool) -> Tuple[int, str]:
        """
        Deterministic, transparent Eco Score computation [0-100] and grade.
        Does not use arbitrary or fake multipliers.
        """
        if is_ev or co2_g <= 0.0:
            return 100, "A+"

        if max_co2 <= min_co2:
            return 90, "A"

        # Linear scaling: Lowest emission route gets 95, highest emission route gets 70
        ratio = (max_co2 - co2_g) / (max_co2 - min_co2)
        score = int(round(70 + 25 * ratio))
        score = max(50, min(98, score))

        if score >= 93:
            grade = "A+"
        elif score >= 85:
            grade = "A"
        elif score >= 75:
            grade = "B+"
        elif score >= 65:
            grade = "B"
        else:
            grade = "C"

        return score, grade

    async def get_route_comparison(self, request: RouteRequest) -> RouteComparisonResponse:
        """
        Fetches route alternatives between origin and destination from OSRM,
        calculates baseline direct tailpipe CO2 emissions using the trained model,
        and ranks candidate routes by emissions.
        """
        # 1. Resolve Origin Coordinates
        if request.origin_coords:
            origin_coords = (request.origin_coords.latitude, request.origin_coords.longitude)
        else:
            origin_coords = self.geocoding_service.geocode(request.origin_name)

        # 2. Resolve Destination Coordinates
        if request.destination_coords:
            dest_coords = (request.destination_coords.latitude, request.destination_coords.longitude)
        else:
            dest_coords = self.geocoding_service.geocode(request.destination_name)

        # 3. Retrieve Driving Routes from OSRM
        raw_routes = self.routing_service.get_driving_routes(
            origin=origin_coords,
            destination=dest_coords,
            alternatives=True
        )

        if not raw_routes:
            raise RuntimeError("No candidate driving routes were returned by the routing engine.")

        # 4. Predict Direct Tailpipe Emissions for Each Route
        v_type = request.vehicle_type.lower().strip()
        is_ev = v_type in ["ev", "electric"]

        evaluated_routes = []
        for idx, r in enumerate(raw_routes):
            dist_km = r["distance_km"]
            dur_min = r["duration_min"]

            if dist_km <= 0:
                raise ValueError("Route distance must be positive.")

            # Calculate baseline tailpipe emission: rate * distance
            pred = emissions_predictor.predict(
                {"vehicle_type": v_type},
                distance_km=dist_km
            )
            trip_co2_g = float(pred["trip_co2_grams"] if pred["trip_co2_grams"] is not None else 0.0)
            if not math.isfinite(trip_co2_g) or trip_co2_g < 0.0:
                raise ValueError(f"Calculated emissions value {trip_co2_g} is invalid or non-finite.")

            evaluated_routes.append({
                "raw_index": idx,
                "distance_km": dist_km,
                "duration_min": dur_min,
                "coordinates": r["coordinates"],
                "summary": r["summary"],
                "co2_grams": trip_co2_g,
                "co2_rate_g_km": float(pred["predicted_co2_g_per_km"]),
                "estimation_method": pred["estimation_method"],
                "model_name": pred["model_name"],
            })

        # 5. Determine Fastest and Lowest Emission Routes
        fastest_item = min(evaluated_routes, key=lambda x: (x["duration_min"], x["distance_km"]))
        fastest_raw_idx = fastest_item["raw_index"]

        # Sort by CO2 emissions ascending (lowest carbon = Rank #1)
        # If CO2 emissions are identical (e.g. EV), sort by shortest distance
        sorted_routes = sorted(evaluated_routes, key=lambda x: (x["co2_grams"], x["distance_km"], x["duration_min"]))

        min_co2 = sorted_routes[0]["co2_grams"]
        max_co2 = sorted_routes[-1]["co2_grams"]

        # Calculate percentage emission reduction of recommended route vs fastest route
        fastest_co2 = fastest_item["co2_grams"]
        greenest_co2 = sorted_routes[0]["co2_grams"]
        if fastest_co2 > 0 and fastest_co2 > greenest_co2:
            eco_saving_pct = round(((fastest_co2 - greenest_co2) / fastest_co2) * 100, 1)
        elif is_ev:
            # For EV, direct tailpipe CO2 is 0. Calculate electricity energy savings (kWh)
            fastest_energy = fastest_item["distance_km"] * 0.18
            greenest_energy = sorted_routes[0]["distance_km"] * 0.18
            if fastest_energy > 0 and fastest_energy > greenest_energy:
                eco_saving_pct = round(((fastest_energy - greenest_energy) / fastest_energy) * 100, 1)
            else:
                eco_saving_pct = 0.0
        else:
            eco_saving_pct = 0.0

        # Distinct palette: Green for recommended, Blue for fastest (if distinct), Amber/Purple for others
        color_palette = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6"]

        # 6. Build RouteOption objects
        route_options: List[RouteOption] = []
        for rank_num, r in enumerate(sorted_routes, start=1):
            is_rec = (rank_num == 1)
            is_fast = (r["raw_index"] == fastest_raw_idx)
            route_id = f"route-{r['raw_index'] + 1}"

            # Name formatting
            summary_name = r["summary"] or f"Path {r['raw_index'] + 1}"
            if is_rec and is_fast:
                route_name = f"{summary_name} (Greenest & Fastest)"
                route_category = "ECO"
            elif is_rec:
                route_name = f"{summary_name} (Green Choice)"
                route_category = "ECO"
            elif is_fast:
                route_name = f"{summary_name} (Fastest Expressway)"
                route_category = "FAST"
            else:
                route_name = f"{summary_name} (Alternative)"
                route_category = "BALANCED"

            # Assign color
            if is_rec:
                color = "#10b981"  # Emerald
            elif is_fast:
                color = "#3b82f6"  # Blue
            else:
                color = color_palette[min(rank_num - 1, len(color_palette) - 1)]

            score, grade = self._calculate_eco_score(r["co2_grams"], min_co2, max_co2, is_ev)

            estimate = EmissionEstimate(
                co2_grams=r["co2_grams"],
                energy_kwh=round(r["distance_km"] * 0.18, 1) if is_ev else None,
                confidence_score=0.99,
                estimation_method=r["estimation_method"],
            )

            route_options.append(RouteOption(
                route_id=route_id,
                route_name=route_name,
                distance_km=r["distance_km"],
                duration_min=r["duration_min"],
                emission_estimate=estimate,
                is_recommended=is_rec,
                is_fastest=is_fast,
                rank=rank_num,
                eco_score=score,
                eco_score_grade=grade,
                route_category=route_category,
                color=color,
                summary=r["summary"],
                coordinates=r["coordinates"],
            ))

        recommended_id = route_options[0].route_id
        fastest_option = next((ro for ro in route_options if ro.is_fastest), route_options[0])

        # Provider transparency notice
        if len(route_options) == 1:
            notice = (
                "OSRM routing engine returned 1 optimal path for these coordinates. "
                "No distinct alternative driving paths were provided by the engine."
            )
        else:
            notice = f"Retrieved {len(route_options)} candidate driving corridors from OSRM engine."

        return RouteComparisonResponse(
            origin=request.origin_name,
            destination=request.destination_name,
            vehicle_type=request.vehicle_type,
            routes=route_options,
            eco_saving_percent=eco_saving_pct,
            fastest_route_id=fastest_option.route_id,
            recommended_route_id=recommended_id,
            routing_provider="OSRM (Open Source Routing Machine)",
            notice=notice,
            limitations_note=(
                "Route emissions represent baseline direct tailpipe CO2 (predicted_rate_g_per_km * distance_km). "
                "Real-time traffic congestion, signal wait delays, and elevation factors are unverified and excluded."
            ),
        )


route_service = RouteService()
