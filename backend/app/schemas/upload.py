from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.knowledge_item import KnowledgeItemStatus


class ParseStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING = "pending"


class UploadFileResult(BaseModel):
    upload_id: str
    knowledge_item_id: int
    knowledge_base_id: int
    original_filename: str
    stored_filename: str
    mime_type: str
    file_type: str
    size: int
    item_status: KnowledgeItemStatus
    parse_status: ParseStatus
    error_message: str | None = None


class BatchUploadResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[UploadFileResult] = Field(default_factory=list)


class UploadErrorDetail(BaseModel):
    original_filename: str
    error_message: str
    error_code: str
