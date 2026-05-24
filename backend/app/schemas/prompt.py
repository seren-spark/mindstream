from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.chunk import SourceLocation
from app.schemas.retrieval import RetrievalHit
from app.schemas.vector import VectorQueryFilter


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str = Field(min_length=1, max_length=8000)


class CitationRef(BaseModel):
    """与 Prompt 中 [n] 编号一一对应，供前端引用卡片。"""

    index: int = Field(ge=1, description="引用编号，对应 [1][2]…")
    chunk_id: str
    knowledge_item_id: int
    source_name: str
    display_title: str
    source_type: str = "manual"
    file_name: str | None = None
    category: str | None = None
    updated_at: str | None = None
    highlight_text: str = ""
    source_location: SourceLocation
    score: float = 0.0
    content_excerpt: str = ""


class PromptBuildRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    hits: list[RetrievalHit] = Field(default_factory=list)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    knowledge_base_name: str = ""
    top_k: int | None = None
    recall_k: int | None = None
    filter: VectorQueryFilter | None = None


class LlmMessage(BaseModel):
    role: str
    content: str


class PromptBuildResult(BaseModel):
    system_prompt: str
    messages: list[LlmMessage]
    citations: list[CitationRef]
    context_block: str
    history_turns_used: int
    chunks_used: int
    context_chars: int
    trimmed: bool = False
    has_context: bool = False
