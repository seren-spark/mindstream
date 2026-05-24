from pydantic import BaseModel, Field


class EmbeddingInput(BaseModel):
    chunk_id: str
    text: str
    text_hash: str
    knowledge_item_id: int
    order_index: int = 0


class EmbeddingRecord(BaseModel):
    chunk_id: str
    text_hash: str
    vector: list[float]
    dimension: int
    from_cache: bool = False


class EmbeddingBatchResult(BaseModel):
    records: list[EmbeddingRecord] = Field(default_factory=list)
    total: int = 0
    cache_hits: int = 0
    api_calls: int = 0
    model_name: str = ""


class IndexingResult(BaseModel):
    vector_count: int
    embedding: EmbeddingBatchResult
