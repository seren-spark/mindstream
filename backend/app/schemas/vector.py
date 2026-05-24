from pydantic import BaseModel, Field


class VectorMetadata(BaseModel):
    """写入 ChromaDB 的 metadata（仅标量字段）。"""

    knowledge_base_id: int
    knowledge_item_id: int
    item_title: str = ""
    order_index: int = 0
    section_title: str = ""
    page_start: int = 0
    item_status: str = "ready"
    source_type: str = "manual"
    category: str = ""
    tags_csv: str = ""


class VectorQueryFilter(BaseModel):
    knowledge_item_id: int | None = None
    knowledge_item_ids: list[int] | None = None
    item_status: str | None = "ready"
    category: str | None = None
    source_type: str | None = None
    tag: str | None = None


class VectorSearchHit(BaseModel):
    chunk_id: str
    knowledge_item_id: int
    item_title: str
    content: str
    score: float
    metadata: VectorMetadata
    order_index: int = 0
    section_title: str = ""
    page_start: int = 0


class VectorSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    filter: VectorQueryFilter = Field(default_factory=VectorQueryFilter)


class VectorSearchResponse(BaseModel):
    query: str
    hits: list[VectorSearchHit]
    total: int


class VectorStatsResponse(BaseModel):
    knowledge_base_id: int
    collection_name: str
    vector_count: int
    chunk_count_sqlite: int
    in_sync: bool


class VectorRebuildResponse(BaseModel):
    knowledge_base_id: int
    vector_count: int
    item_count: int
    message: str
