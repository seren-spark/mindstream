from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

UnansweredStatus = Literal["open", "reviewing", "resolved", "dismissed"]


class UnansweredQuestionResponse(BaseModel):
    id: str
    knowledge_base_id: int
    query_text: str
    occurrence_count: int
    first_asked_at: datetime
    last_asked_at: datetime
    status: str
    reason: str
    top_score: float | None
    sample_user_message_id: str | None
    sample_assistant_message_id: str | None
    suggested_title: str | None
    suggested_summary: str | None
    resolved_item_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UnansweredQuestionUpdate(BaseModel):
    status: UnansweredStatus | None = None
    suggested_title: str | None = Field(default=None, max_length=200)
    suggested_summary: str | None = Field(default=None, max_length=5000)


class UnansweredResolveRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = Field(default=None, max_length=50000)
    summary: str | None = Field(default=None, max_length=2000)


class UnansweredResolveResponse(BaseModel):
    unanswered: UnansweredQuestionResponse
    knowledge_item_id: int
