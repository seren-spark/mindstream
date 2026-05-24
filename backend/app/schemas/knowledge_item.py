from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KnowledgeItemSourceType(StrEnum):
    MANUAL = "manual"
    FILE = "file"
    AI_GENERATED = "ai_generated"


class KnowledgeItemStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DISABLED = "disabled"


ALLOWED_STATUS_TRANSITIONS: dict[KnowledgeItemStatus, set[KnowledgeItemStatus]] = {
    KnowledgeItemStatus.PENDING: {
        KnowledgeItemStatus.PROCESSING,
        KnowledgeItemStatus.READY,
        KnowledgeItemStatus.FAILED,
        KnowledgeItemStatus.DISABLED,
    },
    KnowledgeItemStatus.PROCESSING: {
        KnowledgeItemStatus.READY,
        KnowledgeItemStatus.FAILED,
        KnowledgeItemStatus.DISABLED,
    },
    KnowledgeItemStatus.READY: {KnowledgeItemStatus.DISABLED, KnowledgeItemStatus.PROCESSING},
    KnowledgeItemStatus.FAILED: {
        KnowledgeItemStatus.PENDING,
        KnowledgeItemStatus.PROCESSING,
        KnowledgeItemStatus.DISABLED,
    },
    KnowledgeItemStatus.DISABLED: {KnowledgeItemStatus.PENDING, KnowledgeItemStatus.READY},
}


class KnowledgeItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=50000)
    summary: str | None = Field(default=None, max_length=2000)
    source_type: KnowledgeItemSourceType = KnowledgeItemSourceType.MANUAL
    status: KnowledgeItemStatus | None = None
    tags: list[str] = Field(default_factory=list, max_length=10)
    category: str | None = Field(default=None, max_length=50)
    file_name: str | None = Field(default=None, max_length=255)
    file_type: str | None = Field(default=None, max_length=50)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        cleaned = [tag.strip() for tag in value if tag.strip()]
        return cleaned[:10]


class KnowledgeItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=50000)
    summary: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = Field(default=None, max_length=10)
    category: str | None = Field(default=None, max_length=50)
    status: KnowledgeItemStatus | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [tag.strip() for tag in value if tag.strip()]
        return cleaned[:10]


class KnowledgeItemStatusUpdate(BaseModel):
    status: KnowledgeItemStatus
    error_message: str | None = Field(default=None, max_length=2000)


class KnowledgeItemListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    knowledge_base_id: int
    title: str
    summary: str | None
    source_type: KnowledgeItemSourceType
    status: KnowledgeItemStatus
    tags: list[str]
    category: str | None
    file_name: str | None
    file_path: str | None
    file_type: str | None
    mime_type: str | None
    file_size: int
    chunk_count: int
    processing_progress: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class KnowledgeItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    knowledge_base_id: int
    title: str
    content: str | None
    summary: str | None
    source_type: KnowledgeItemSourceType
    status: KnowledgeItemStatus
    tags: list[str]
    category: str | None
    file_name: str | None
    file_path: str | None
    file_type: str | None
    mime_type: str | None
    file_size: int
    chunk_count: int
    processing_progress: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime
