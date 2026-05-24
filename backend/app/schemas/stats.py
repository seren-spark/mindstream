from datetime import datetime

from pydantic import BaseModel, Field


class StatsOverviewResponse(BaseModel):
    knowledge_base_count: int
    item_count: int
    item_ready_count: int
    question_count_today: int
    question_count_period: int
    hit_rate: float = Field(ge=0, le=1)
    hit_rate_delta: float
    period_days: int
    generated_at: datetime


class TrendPoint(BaseModel):
    date: str
    question_count: int
    hit_count: int
    miss_count: int


class StatsTrendResponse(BaseModel):
    period_days: int
    knowledge_base_id: int | None
    points: list[TrendPoint]
    total_questions: int
    avg_daily: float


class HeatItem(BaseModel):
    rank: int
    knowledge_item_id: int
    title: str
    knowledge_base_id: int
    knowledge_base_name: str
    cite_count: int
    unique_questions: int
    last_cited_at: datetime | None


class StatsHeatResponse(BaseModel):
    period_days: int
    knowledge_base_id: int | None
    items: list[HeatItem]


class UnansweredItem(BaseModel):
    query_text: str
    occurrence_count: int
    last_asked_at: datetime
    knowledge_base_id: int
    knowledge_base_name: str
    sample_message_id: str
    suggested_action: str = "upload"


class StatsUnansweredResponse(BaseModel):
    period_days: int
    knowledge_base_id: int | None
    total_miss_count: int
    items: list[UnansweredItem]
