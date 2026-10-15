import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")


class RouteRequest(BaseModel):
    origin_name: str = Field(..., description="Human readable name or address of origin")
    destination_name: str = Field(..., description="Human readable name or address of destination")
    origin_coords: Optional[Coordinates] = None
    destination_coords: Optional[Coordinates] = None
    vehicle_type: str = Field(
        default="gasoline",
        description="Vehicle category: gasoline, diesel, hybrid, or ev"
    )

    @field_validator("origin_name", "destination_name")
    @classmethod
    def validate_location_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2 or len(re.findall(r"[a-zA-Z0-9]", clean)) < 2:
            raise ValueError(f"Location '{v}' is too short or ambiguous (minimum 2 alphanumeric characters required).")
        
        dummy_patterns = [
            r"\btest\s+address\b",
            r"\bfake\s+address\b",
            r"\bdummy\s+address\b",
            r"\bsample\s+address\b",
            r"\bplaceholder\b",
            r"\btest\s*\d+\b",
        ]
        if any(re.search(pat, clean, re.IGNORECASE) for pat in dummy_patterns):
            raise ValueError(f"Location '{v}' is a placeholder or test string, not a recognized address.")
        return clean

    @model_validator(mode="after")
    def validate_endpoints_distinct(self):
        if self.origin_name.strip().lower() == self.destination_name.strip().lower():
            raise ValueError("Origin and destination cannot be the same location.")
        if self.origin_coords and self.destination_coords:
            if (abs(self.origin_coords.latitude - self.destination_coords.latitude) < 0.0001 and
                abs(self.origin_coords.longitude - self.destination_coords.longitude) < 0.0001):
                raise ValueError("Origin and destination coordinates are identical.")
        return self


class EmissionEstimate(BaseModel):
    co2_grams: float = Field(..., description="Estimated CO2 emissions in grams")
    energy_kwh: Optional[float] = Field(None, description="Estimated energy consumption in kWh")
    confidence_score: Optional[float] = Field(None, description="Model prediction confidence [0.0 - 1.0]")
    estimation_method: str = Field(..., description="'ml_regressor' or 'baseline_physics'")


class RouteOption(BaseModel):
    route_id: str
    route_name: str
    distance_km: float
    duration_min: float
    emission_estimate: EmissionEstimate
    is_recommended: bool = False
    is_fastest: bool = False
    rank: int = 1
    eco_score: int = 85
    eco_score_grade: str = "A"
    route_category: str = "ECO"
    color: str = "#10b981"
    summary: Optional[str] = None
    coordinates: List[List[float]] = Field(
        default_factory=list,
        description="List of [latitude, longitude] pairs representing route geometry"
    )


class RouteComparisonResponse(BaseModel):
    origin: str
    destination: str
    vehicle_type: str
    routes: List[RouteOption]
    eco_saving_percent: float = Field(
        default=0.0,
        description="Percentage emission reduction of recommended route vs default fastest route"
    )
    fastest_route_id: Optional[str] = None
    recommended_route_id: Optional[str] = None
    routing_provider: Optional[str] = "OSRM (Open Source Routing Machine)"
    notice: Optional[str] = None
    limitations_note: Optional[str] = (
        "Route emissions represent baseline direct tailpipe CO2 (predicted_rate_g_per_km * distance_km). "
        "Real-time traffic congestion, signal wait delays, and elevation factors are not applied."
    )



class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    model_loaded: bool
    database_connected: bool


class EmissionsPredictionRequest(BaseModel):
    make: Optional[str] = Field(None, description="Vehicle manufacturer (e.g. TOYOTA, HONDA, FORD)")
    model_name: Optional[str] = Field(None, description="Vehicle model name")
    vehicle_class: Optional[str] = Field(None, description="Vehicle class (e.g. COMPACT, MID-SIZE, SUV - SMALL)")
    engine_size_l: Optional[float] = Field(None, ge=0.0, description="Engine displacement in liters")
    cylinders: Optional[int] = Field(None, ge=1, le=16, description="Number of engine cylinders")
    transmission: Optional[str] = Field(None, description="Transmission code (e.g. AS6, M6, AV)")
    fuel_type: Optional[str] = Field(None, description="Fuel type (gasoline/X, diesel/D, premium/Z, ethanol/E, ev)")
    fuel_consumption_comb: Optional[float] = Field(None, ge=0.0, description="Combined fuel consumption (L/100 km)")
    fuel_consumption_city: Optional[float] = Field(None, ge=0.0, description="City fuel consumption (L/100 km)")
    fuel_consumption_hwy: Optional[float] = Field(None, ge=0.0, description="Highway fuel consumption (L/100 km)")
    vehicle_type: Optional[str] = Field("gasoline", description="Convenience vehicle category: compact, mid-size, suv, truck, ev")
    distance_km: Optional[float] = Field(None, ge=0.0, description="Route distance in kilometers for trip total CO2 estimation")


class EmissionsPredictionResponse(BaseModel):
    predicted_co2_g_per_km: float = Field(..., description="Estimated direct tailpipe CO2 emission rate (g/km)")
    distance_km: Optional[float] = Field(None, description="Trip distance in km (if provided)")
    trip_co2_grams: Optional[float] = Field(None, description="Total journey direct CO2 in grams (rate * distance_km)")
    model_name: str = Field(..., description="Active ML model or estimation rule")
    estimation_method: str = Field(..., description="Prediction pipeline identifier")
    standardized_features: dict = Field(default_factory=dict, description="Standardized vehicle features used by model")
    limitations_note: str = Field(..., description="Scientific limitations and scope note")

