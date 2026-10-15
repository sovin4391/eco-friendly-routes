from fastapi import APIRouter, HTTPException, status
from backend.models.schemas import RouteRequest, RouteComparisonResponse
from backend.services.route_service import route_service

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post("/compare", response_model=RouteComparisonResponse)
async def compare_routes(request: RouteRequest):
    """
    Receives origin and destination parameters, evaluates candidate routes,
    and returns comparative environmental metrics.
    
    In this setup phase, routes and ML estimation are not hardcoded or mocked with fake data.
    Returns HTTP 501 until dataset collection and ML model training are executed.
    """
    try:
        return await route_service.get_route_comparison(request)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(ve)
        )
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route evaluation failed: {str(e)}"
        )

