from pydantic import BaseModel, Field

from app.schemas.prompt import ChatMessage, CitationRef
from app.schemas.vector import VectorQueryFilter


class ChatStreamRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    conversation_id: str | None = Field(default=None, max_length=36)
    top_k: int = Field(default=5, ge=1, le=20)
    filter: VectorQueryFilter = Field(default_factory=VectorQueryFilter)


class StreamEventStart(BaseModel):
    type: str = "start"
    message_id: str


class StreamEventToken(BaseModel):
    type: str = "token"
    delta: str


class StreamEventReferences(BaseModel):
    type: str = "references"
    citations: list[CitationRef]


class StreamEventDone(BaseModel):
    type: str = "done"


class StreamEventError(BaseModel):
    type: str = "error"
    message: str
