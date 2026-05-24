from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.prompt import CitationRef


class ConversationCreate(BaseModel):
    title: str = Field(default="新对话", max_length=200)
    agent_id: str | None = Field(default=None, max_length=36)


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ConversationResponse(BaseModel):
    id: str
    knowledge_base_id: int
    agent_id: str | None = None
    title: str
    message_count: int
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    status: str
    error_message: str | None = None
    citations: list[CitationRef] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
