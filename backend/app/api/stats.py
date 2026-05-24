from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.stats import (
    StatsHeatResponse,
    StatsOverviewResponse,
    StatsTrendResponse,
    StatsUnansweredResponse,
)
from app.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverviewResponse)
def stats_overview(
    knowledge_base_id: int | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
) -> StatsOverviewResponse:
    return StatsService.overview(db, knowledge_base_id=knowledge_base_id, days=days)


@router.get("/trend", response_model=StatsTrendResponse)
def stats_trend(
    knowledge_base_id: int | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
) -> StatsTrendResponse:
    return StatsService.trend(db, knowledge_base_id=knowledge_base_id, days=days)


@router.get("/heat", response_model=StatsHeatResponse)
def stats_heat(
    knowledge_base_id: int | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=90),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> StatsHeatResponse:
    return StatsService.heat(
        db, knowledge_base_id=knowledge_base_id, days=days, limit=limit
    )


@router.get("/unanswered", response_model=StatsUnansweredResponse)
def stats_unanswered(
    knowledge_base_id: int | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=90),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> StatsUnansweredResponse:
    return StatsService.unanswered(
        db, knowledge_base_id=knowledge_base_id, days=days, limit=limit
    )
