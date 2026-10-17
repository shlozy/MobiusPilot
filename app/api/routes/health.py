from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "database": "sqlite", "messaging_platform": settings.messaging_platform}


@router.get("/ready")
def readiness() -> dict:
    return {"status": "ready", "app": settings.app_name}
