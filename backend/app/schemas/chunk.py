from pydantic import BaseModel, Field


class SourceLocation(BaseModel):
    """引用源定位 — 供前端引用卡片与高亮跳转。"""

    page_start: int | None = None
    page_end: int | None = None
    section_index: int | None = None
    section_title: str | None = None
    heading_path: list[str] = Field(default_factory=list)
    char_start: int | None = None
    char_end: int | None = None


class ChunkMetadata(BaseModel):
    chunk_strategy: str = "section_paragraph_window"
    chunk_size: int
    overlap: int
    file_type: str | None = None
    parser_name: str | None = None
    language: str = "zh"
    is_continued: bool = False


class ChunkDraft(BaseModel):
    """切片输出，写入 DB 并供 embedding 消费。"""

    chunk_id: str
    knowledge_item_id: int
    knowledge_base_id: int
    content: str
    order_index: int
    token_count: int
    source_location: SourceLocation
    metadata: ChunkMetadata


class ChunkResponse(BaseModel):
    chunk_id: str
    knowledge_item_id: int
    content: str
    order_index: int
    token_count: int
    source_location: SourceLocation
    metadata: ChunkMetadata

    model_config = {"from_attributes": True}
