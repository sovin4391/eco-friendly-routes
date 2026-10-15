import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    APP_NAME: str = "Eco-Friendly Routes API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # CORS configuration allowing React frontend dev server
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'eco_routes.db'}"
    
    # Model storage path
    MODELS_DIR: Path = BASE_DIR / "models"
    MODEL_PATH: Path = BASE_DIR / "models" / "emissions_model.joblib"
    LEGACY_MODEL_PATH: Path = BASE_DIR / "models" / "eco_route_regressor.joblib"
    
    # External routing and geocoding providers (Configurable via environment variables)
    ROUTING_PROVIDER: str = os.getenv("ROUTING_PROVIDER", "osrm")
    OSRM_BASE_URL: str = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")
    GEOCODING_PROVIDER: str = os.getenv("GEOCODING_PROVIDER", "nominatim")
    NOMINATIM_BASE_URL: str = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org")
    ROUTING_TIMEOUT_SEC: float = float(os.getenv("ROUTING_TIMEOUT_SEC", "10.0"))
    HTTP_USER_AGENT: str = os.getenv("HTTP_USER_AGENT", "EcoFriendlyRoutes-Capstone/1.0 (contact: info@eco-routes.local)")
    
    # Routing integrity & endpoint plausibility safeguards
    MAX_WAYPOINT_SNAPPING_METERS: float = float(os.getenv("MAX_WAYPOINT_SNAPPING_METERS", "25000.0"))
    MAX_ENDPOINT_DETOUR_KM: float = float(os.getenv("MAX_ENDPOINT_DETOUR_KM", "25.0"))
    MAX_ROUTE_DISTANCE_KM: float = float(os.getenv("MAX_ROUTE_DISTANCE_KM", "3000.0"))

settings = Settings()

