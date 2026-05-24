from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.knowledge_item import (
    KnowledgeItemCreate,
    KnowledgeItemListItem,
    KnowledgeItemResponse,
    KnowledgeItemSourceType,
    KnowledgeItemStatus,
    KnowledgeItemStatusUpdate,
    KnowledgeItemUpdate,
)
from app.schemas.parse import ParseItemResponse
from app.schemas.upload import ParseStatus
from app.services.knowledge_base_service import KnowledgeBaseNotFoundError
from app.services.knowledge_item_service import (
    InvalidStatusTransitionError,
    KnowledgeItemNotFoundError,
    KnowledgeItemService,
)

router = APIRouter(tags=["knowledge-items"])


@router.get(
    "/knowledge-bases/{knowledge_base_id}/items",
    response_model=PaginatedResponse[KnowledgeItemListItem],
)
def list_knowledge_items(
    knowledge_base_id: int,
    keyword: str | None = Query(default=None, max_length=100),
    status: KnowledgeItemStatus | None = None,
    source_type: KnowledgeItemSourceType | None = None,
    category: str | None = Query(default=None, max_length=100),
    tag: str | None = Query(default=None, max_length=50),
    sort: str = Query(
        default="updated_at_desc",
        pattern="^(updated_at_desc|created_at_asc|title_asc)$",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[KnowledgeItemListItem]:
    try:
        items, total = KnowledgeItemService.list_items(
            db,
            knowledge_base_id,
            keyword=keyword,
            status=status.value if status else None,
            source_type=source_type.value if source_type else None,
            category=category,
            tag=tag,
            sort=sort,
            page=page,
            page_size=page_size,
        )
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return PaginatedResponse(
        items=[KnowledgeItemListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/knowledge-bases/{knowledge_base_id}/items",
    response_model=KnowledgeItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_item(
    knowledge_base_id: int,
    payload: KnowledgeItemCreate,
    db: Session = Depends(get_db),
) -> KnowledgeItemResponse:
    try:
        item = KnowledgeItemService.create_item(db, knowledge_base_id, payload)
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return KnowledgeItemResponse.model_validate(item)


@router.get("/knowledge-items/{item_id}", response_model=KnowledgeItemResponse)
def get_knowledge_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> KnowledgeItemResponse:
    try:
        item = KnowledgeItemService.get_item(db, item_id)
    except KnowledgeItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return KnowledgeItemResponse.model_validate(item)


@router.put("/knowledge-items/{item_id}", response_model=KnowledgeItemResponse)
def update_knowledge_item(
    item_id: int,
    payload: KnowledgeItemUpdate,
    db: Session = Depends(get_db),
) -> KnowledgeItemResponse:
    try:
        item = KnowledgeItemService.update_item(db, item_id, payload)
    except KnowledgeItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return KnowledgeItemResponse.model_validate(item)


@router.patch("/knowledge-items/{item_id}/status", response_model=KnowledgeItemResponse)
def update_knowledge_item_status(
    item_id: int,
    payload: KnowledgeItemStatusUpdate,
    db: Session = Depends(get_db),
) -> KnowledgeItemResponse:
    try:
        item = KnowledgeItemService.update_status(db, item_id, payload)
    except KnowledgeItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return KnowledgeItemResponse.model_validate(item)


@router.post("/knowledge-items/{item_id}/process", response_model=KnowledgeItemResponse)
def trigger_knowledge_item_process(
    item_id: int,
    db: Session = Depends(get_db),
) -> KnowledgeItemResponse:
    try:
        item = KnowledgeItemService.trigger_process(db, item_id)
    except KnowledgeItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return KnowledgeItemResponse.model_validate(item)


@router.post("/knowledge-items/{item_id}/parse", response_model=ParseItemResponse)
def parse_knowledge_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> ParseItemResponse:
    try:
        item = KnowledgeItemService.parse_item(db, item_id)
    except KnowledgeItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if item.status == KnowledgeItemStatus.READY.value:
        parse_status = ParseStatus.COMPLETED
    elif item.status == KnowledgeItemStatus.FAILED.value:
        parse_status = ParseStatus.FAILED
    else:
        parse_status = ParseStatus.PENDING

    return ParseItemResponse(
        knowledge_item_id=item.id,
        parse_status=parse_status.value,
        item_status=item.status,
        error_message=item.error_message,
    )


@router.delete("/knowledge-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> None:
    try:
        KnowledgeItemService.delete_item(db, item_id)
    except KnowledgeItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
