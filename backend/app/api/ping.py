from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import PingResponse

router = APIRouter(tags=["health"])


@router.get("/ping", response_model=PingResponse)
async def ping() -> PingResponse:
    settings = get_settings()
    return PingResponse(
        status="ok",
        message="pong",
        version=settings.app_version,
    )
