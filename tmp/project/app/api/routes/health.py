"""
API routes for service health probes.
"""

from fastapi import APIRouter, status

from app.domain.schemas.health import HealthResponse
from app.domain.services.health_service import get_liveness, get_readiness


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def live_probe() -> HealthResponse:
    return get_liveness()


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse}},
)
def readiness_probe() -> HealthResponse:
    return get_readiness()
