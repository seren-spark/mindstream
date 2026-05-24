from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
)
from app.services.conversation_service import ConversationNotFoundError, ConversationService

router = APIRouter(prefix="/knowledge-bases/{knowledge_base_id}/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    knowledge_base_id: int,
    payload: ConversationCreate | None = None,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    conv = ConversationService.create(db, knowledge_base_id, payload)
    return ConversationResponse.model_validate(conv)


@router.get("", response_model=PaginatedResponse[ConversationResponse])
def list_conversations(
    knowledge_base_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ConversationResponse]:
    items, total = ConversationService.list_conversations(
        db, knowledge_base_id, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[ConversationResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    knowledge_base_id: int,
    conversation_id: str,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    try:
        conv = ConversationService.get(db, knowledge_base_id, conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在") from exc
    return ConversationResponse.model_validate(conv)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    knowledge_base_id: int,
    conversation_id: str,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    try:
        conv = ConversationService.get(db, knowledge_base_id, conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在") from exc
    conv.title = payload.title
    db.commit()
    db.refresh(conv)
    return ConversationResponse.model_validate(conv)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    knowledge_base_id: int,
    conversation_id: str,
    db: Session = Depends(get_db),
) -> None:
    try:
        ConversationService.delete(db, knowledge_base_id, conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在") from exc


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(
    knowledge_base_id: int,
    conversation_id: str,
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[MessageResponse]:
    try:
        rows = ConversationService.list_messages(
            db, knowledge_base_id, conversation_id, limit=limit
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在") from exc
    return [ConversationService.message_to_response(m) for m in rows]
