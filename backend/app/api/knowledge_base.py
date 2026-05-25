from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.api_errors import not_found
from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseStatus,
    KnowledgeBaseUpdate,
)
from app.services.knowledge_base_service import KnowledgeBaseNotFoundError, KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases", tags=["kb"])


@router.get("", response_model=PaginatedResponse[KnowledgeBaseResponse])
def list_knowledge_bases(
    keyword: str | None = Query(default=None, max_length=100),
    status: KnowledgeBaseStatus | None = None,
    sort: str = Query(
        default="created_at_desc",
        pattern="^(created_at_desc|created_at_asc|name_asc)$",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[KnowledgeBaseResponse]:
    items, total = KnowledgeBaseService.list_knowledge_bases(
        db,
        keyword=keyword,
        status=status.value if status else None,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[KnowledgeBaseResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
) -> KnowledgeBaseResponse:
    item = KnowledgeBaseService.create_knowledge_base(db, payload)
    return KnowledgeBaseResponse.model_validate(item)


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
) -> KnowledgeBaseResponse:
    try:
        item = KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
    except KnowledgeBaseNotFoundError as exc:
        raise not_found(str(exc)) from exc
    return KnowledgeBaseResponse.model_validate(item)


@router.put("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base(
    knowledge_base_id: int,
    payload: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
) -> KnowledgeBaseResponse:
    try:
        item = KnowledgeBaseService.update_knowledge_base(db, knowledge_base_id, payload)
    except KnowledgeBaseNotFoundError as exc:
        raise not_found(str(exc)) from exc
    return KnowledgeBaseResponse.model_validate(item)


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
) -> None:
    try:
        KnowledgeBaseService.delete_knowledge_base(db, knowledge_base_id)
    except KnowledgeBaseNotFoundError as exc:
        raise not_found(str(exc)) from exc
