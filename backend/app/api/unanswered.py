from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.unanswered import (
    UnansweredQuestionResponse,
    UnansweredQuestionUpdate,
    UnansweredResolveRequest,
    UnansweredResolveResponse,
)
from app.services.unanswered_service import UnansweredNotFoundError, UnansweredService

router = APIRouter(
    prefix="/knowledge-bases/{knowledge_base_id}/unanswered-questions",
    tags=["unanswered-questions"],
)


@router.get("", response_model=PaginatedResponse[UnansweredQuestionResponse])
def list_unanswered(
    knowledge_base_id: int,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[UnansweredQuestionResponse]:
    items, total = UnansweredService.list_questions(
        db, knowledge_base_id, status=status_filter, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[UnansweredQuestionResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{question_id}", response_model=UnansweredQuestionResponse)
def get_unanswered(
    knowledge_base_id: int,
    question_id: str,
    db: Session = Depends(get_db),
) -> UnansweredQuestionResponse:
    try:
        row = UnansweredService.get(db, knowledge_base_id, question_id)
    except UnansweredNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在") from exc
    return UnansweredQuestionResponse.model_validate(row)


@router.patch("/{question_id}", response_model=UnansweredQuestionResponse)
def update_unanswered(
    knowledge_base_id: int,
    question_id: str,
    payload: UnansweredQuestionUpdate,
    db: Session = Depends(get_db),
) -> UnansweredQuestionResponse:
    try:
        row = UnansweredService.update(
            db,
            knowledge_base_id,
            question_id,
            status=payload.status,
            suggested_title=payload.suggested_title,
            suggested_summary=payload.suggested_summary,
        )
    except UnansweredNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在") from exc
    return UnansweredQuestionResponse.model_validate(row)


@router.post("/{question_id}/dismiss", response_model=UnansweredQuestionResponse)
def dismiss_unanswered(
    knowledge_base_id: int,
    question_id: str,
    db: Session = Depends(get_db),
) -> UnansweredQuestionResponse:
    try:
        row = UnansweredService.dismiss(db, knowledge_base_id, question_id)
    except UnansweredNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在") from exc
    return UnansweredQuestionResponse.model_validate(row)


@router.post("/{question_id}/resolve", response_model=UnansweredResolveResponse)
def resolve_unanswered(
    knowledge_base_id: int,
    question_id: str,
    payload: UnansweredResolveRequest | None = None,
    db: Session = Depends(get_db),
) -> UnansweredResolveResponse:
    try:
        row, item_id = UnansweredService.resolve_to_item(
            db, knowledge_base_id, question_id, payload or UnansweredResolveRequest()
        )
    except UnansweredNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UnansweredResolveResponse(
        unanswered=UnansweredQuestionResponse.model_validate(row),
        knowledge_item_id=item_id,
    )
