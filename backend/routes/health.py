from fastapi import APIRouter
from backend.models.schemas import HealthResponse
from backend.core.config import settings
from backend.services.route_service import route_service
from backend.database.db import get_db_connection

router = APIRouter(tags=["Health & Status"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Returns server operational status, database connectivity, and ML model availability.
    """
    db_ok = False
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        model_loaded=route_service.is_model_loaded(),
        database_connected=db_ok
    )
