"""
Feature engineering, transformation, and input standardization utilities
for vehicle CO2 emission prediction and route environmental estimation.
"""
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

# Mapping common user-friendly vehicle terms to Canada dataset categories
FUEL_TYPE_MAP = {
    "gasoline": "X",       # Regular gasoline
    "regular_gasoline": "X",
    "petrol": "X",
    "gas": "X",
    "premium": "Z",        # Premium gasoline
    "premium_gasoline": "Z",
    "diesel": "D",         # Diesel
    "ethanol": "E",        # Ethanol (E85)
    "e85": "E",
    "natural_gas": "N",    # Natural gas
    "cng": "N",
}

# Default typical specs for quick prediction when deep technical specs are unknown
VEHICLE_TYPE_DEFAULTS = {
    "compact": {
        "make": "TOYOTA",
        "vehicle_class": "COMPACT",
        "engine_size_l": 1.8,
        "cylinders": 4,
        "transmission": "AS6",
        "fuel_type": "X",
        "fuel_consumption_comb": 7.5,
    },
    "mid-size": {
        "make": "HONDA",
        "vehicle_class": "MID-SIZE",
        "engine_size_l": 2.4,
        "cylinders": 4,
        "transmission": "AS6",
        "fuel_type": "X",
        "fuel_consumption_comb": 8.8,
    },
    "suv": {
        "make": "FORD",
        "vehicle_class": "SUV - SMALL",
        "engine_size_l": 2.5,
        "cylinders": 4,
        "transmission": "AS6",
        "fuel_type": "X",
        "fuel_consumption_comb": 9.8,
    },
    "truck": {
        "make": "CHEVROLET",
        "vehicle_class": "PICKUP TRUCK - STANDARD",
        "engine_size_l": 5.3,
        "cylinders": 8,
        "transmission": "AS8",
        "fuel_type": "X",
        "fuel_consumption_comb": 13.5,
    },
    "diesel_car": {
        "make": "VOLKSWAGEN",
        "vehicle_class": "COMPACT",
        "engine_size_l": 2.0,
        "cylinders": 4,
        "transmission": "M6",
        "fuel_type": "D",
        "fuel_consumption_comb": 6.8,
    },
}


def standardize_vehicle_input(raw_input: Dict[str, Any]) -> pd.DataFrame:
    """
    Standardizes arbitrary dictionary/schema inputs to the exact column names
    and expected types required by the trained emissions model pipeline:
    - 'Make'
    - 'Vehicle Class'
    - 'Engine Size(L)'
    - 'Cylinders'
    - 'Transmission'
    - 'Fuel Type'
    - 'Fuel Consumption Comb (L/100 km)'
    """
    # Check if a preset vehicle type was requested
    raw_type = str(raw_input.get("vehicle_type", "")).lower().strip()
    defaults = VEHICLE_TYPE_DEFAULTS.get(raw_type, VEHICLE_TYPE_DEFAULTS["mid-size"]).copy()

    # Extract or fallback to defaults
    make = str(raw_input.get("make") or defaults["make"]).upper().strip()
    vehicle_class = str(raw_input.get("vehicle_class") or defaults["vehicle_class"]).upper().strip()
    transmission = str(raw_input.get("transmission") or defaults["transmission"]).upper().strip()

    raw_fuel = str(raw_input.get("fuel_type") or defaults["fuel_type"]).lower().strip()
    fuel_code = FUEL_TYPE_MAP.get(raw_fuel, raw_fuel.upper())

    try:
        engine_size = float(raw_input.get("engine_size_l") or defaults["engine_size_l"])
    except (ValueError, TypeError):
        engine_size = defaults["engine_size_l"]

    try:
        cylinders = int(raw_input.get("cylinders") or defaults["cylinders"])
    except (ValueError, TypeError):
        cylinders = defaults["cylinders"]

    try:
        fuel_comb = raw_input.get("fuel_consumption_comb")
        if fuel_comb is None:
            fuel_comb = raw_input.get("fuel_consumption_comb_l_100km")
        if fuel_comb is None:
            # Check city/hwy combination: (0.55 * city + 0.45 * hwy) standard NRC formula
            city = raw_input.get("fuel_consumption_city")
            hwy = raw_input.get("fuel_consumption_hwy")
            if city is not None and hwy is not None:
                fuel_comb = round(0.55 * float(city) + 0.45 * float(hwy), 2)
            else:
                fuel_comb = defaults["fuel_consumption_comb"]
        fuel_comb = float(fuel_comb)
    except (ValueError, TypeError):
        fuel_comb = defaults["fuel_consumption_comb"]

    data = {
        "Make": [make],
        "Vehicle Class": [vehicle_class],
        "Engine Size(L)": [engine_size],
        "Cylinders": [cylinders],
        "Transmission": [transmission],
        "Fuel Type": [fuel_code],
        "Fuel Consumption Comb (L/100 km)": [fuel_comb],
    }

    return pd.DataFrame(data)


def calculate_baseline_emissions(distance_km: float, vehicle_type: str = "gasoline") -> float:
    """
    Standard static emission factor calculation (g CO2 / km) for baseline comparison.
    Standard reference factors (EPA / EEA benchmarks):
    - gasoline: ~192 g CO2/km
    - diesel: ~171 g CO2/km
    - hybrid: ~105 g CO2/km
    - ev: ~0 g direct tailpipe CO2/km
    """
    factors = {
        "gasoline": 192.0,
        "diesel": 171.0,
        "hybrid": 105.0,
        "ev": 0.0,
    }
    factor = factors.get(vehicle_type.lower(), 192.0)
    return distance_km * factor
