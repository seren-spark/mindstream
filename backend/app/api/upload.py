from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.upload import BatchUploadResponse, UploadFileResult
from app.services.knowledge_base_service import KnowledgeBaseNotFoundError
from app.services.upload_service import UploadService

router = APIRouter(prefix="/knowledge-bases", tags=["upload"])


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()][:10]


@router.post(
    "/{knowledge_base_id}/upload",
    response_model=UploadFileResult,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    knowledge_base_id: int,
    file: UploadFile = File(...),
    category: str | None = Form(default=None),
    tags: str | None = Form(default=None),
    auto_parse: bool = Form(default=True),
    db: Session = Depends(get_db),
) -> UploadFileResult:
    try:
        return await UploadService.upload_single_file(
            db,
            knowledge_base_id,
            file,
            category=category,
            tags=_parse_tags(tags),
            auto_parse=auto_parse,
        )
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{knowledge_base_id}/upload/batch",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents_batch(
    knowledge_base_id: int,
    files: list[UploadFile] = File(...),
    category: str | None = Form(default=None),
    tags: str | None = Form(default=None),
    auto_parse: bool = Form(default=True),
    db: Session = Depends(get_db),
) -> BatchUploadResponse:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请至少选择一个文件")
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="单次最多上传 10 个文件",
        )

    try:
        return await UploadService.upload_batch_files(
            db,
            knowledge_base_id,
            files,
            category=category,
            tags=_parse_tags(tags),
            auto_parse=auto_parse,
        )
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
