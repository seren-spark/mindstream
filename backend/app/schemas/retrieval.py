from pydantic import BaseModel, Field

from app.schemas.chunk import SourceLocation
from app.schemas.vector import VectorQueryFilter


class RetrievalHit(BaseModel):
    """混合检索结果 — 同时供 RAG prompt 与前端引用卡片使用。"""

    chunk_id: str
    content: str
    score: float
    source_name: str
    display_title: str
    source_location: SourceLocation
    knowledge_item_id: int
    knowledge_base_id: int
    highlight_text: str = ""
    order_index: int = 0
    recall_sources: list[str] = Field(default_factory=list)
    vector_score: float | None = None
    keyword_score: float | None = None


class HybridSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    recall_k: int | None = Field(default=None, ge=1, le=50)
    filter: VectorQueryFilter = Field(default_factory=VectorQueryFilter)


class HybridSearchResponse(BaseModel):
    query: str
    hits: list[RetrievalHit]
    total: int
    vector_recall_count: int = 0
    keyword_recall_count: int = 0
