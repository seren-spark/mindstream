"""会话与消息历史服务。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import ConversationMessage
from app.schemas.conversation import ConversationCreate, MessageResponse
from app.schemas.prompt import ChatMessage, ChatRole, CitationRef


class ConversationNotFoundError(Exception):
    pass


def _auto_title(text: str, *, max_len: int = 30) -> str:
    stripped = text.strip().replace("\n", " ")
    if not stripped:
        return "新对话"
    return stripped[:max_len] + ("…" if len(stripped) > max_len else "")


class ConversationService:
    @staticmethod
    def create(db: Session, knowledge_base_id: int, payload: ConversationCreate | None = None) -> Conversation:
        title = (payload.title if payload else None) or "新对话"
        agent_id = payload.agent_id if payload else None
        conv = Conversation(
            id=str(uuid.uuid4()),
            knowledge_base_id=knowledge_base_id,
            agent_id=agent_id,
            title=title,
            message_count=0,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def get(db: Session, knowledge_base_id: int, conversation_id: str) -> Conversation:
        conv = db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.knowledge_base_id == knowledge_base_id,
            )
        )
        if not conv:
            raise ConversationNotFoundError
        return conv

    @staticmethod
    def list_conversations(
        db: Session,
        knowledge_base_id: int,
        *,
        agent_id: str | None = None,
        page: int = 1,
        page_size: int = 30,
    ) -> tuple[list[Conversation], int]:
        base = select(Conversation).where(Conversation.knowledge_base_id == knowledge_base_id)
        if agent_id is not None:
            base = base.where(Conversation.agent_id == agent_id)
        total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = db.scalars(
            base.order_by(desc(Conversation.last_message_at), desc(Conversation.updated_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total

    @staticmethod
    def delete(db: Session, knowledge_base_id: int, conversation_id: str) -> None:
        conv = ConversationService.get(db, knowledge_base_id, conversation_id)
        db.delete(conv)
        db.commit()

    @staticmethod
    def list_messages(
        db: Session,
        knowledge_base_id: int,
        conversation_id: str,
        *,
        limit: int = 200,
    ) -> list[ConversationMessage]:
        ConversationService.get(db, knowledge_base_id, conversation_id)
        return list(
            db.scalars(
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == conversation_id)
                .order_by(ConversationMessage.created_at.asc())
                .limit(limit)
            ).all()
        )

    @staticmethod
    def message_to_response(msg: ConversationMessage) -> MessageResponse:
        citations: list[CitationRef] = []
        if msg.references_json:
            citations = [CitationRef.model_validate(c) for c in msg.references_json]
        return MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role,
            content=msg.content,
            status=msg.status,
            error_message=msg.error_message,
            citations=citations,
            created_at=msg.created_at,
            updated_at=msg.updated_at,
        )

    @staticmethod
    def add_user_message(
        db: Session,
        conversation: Conversation,
        *,
        message_id: str | None = None,
        content: str,
    ) -> ConversationMessage:
        msg = ConversationMessage(
            id=message_id or str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="user",
            content=content,
            status="done",
        )
        db.add(msg)
        if conversation.title == "新对话":
            conversation.title = _auto_title(content)
        conversation.message_count += 1
        conversation.last_message_at = datetime.now(UTC)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def start_assistant_message(
        db: Session,
        conversation: Conversation,
        *,
        message_id: str,
    ) -> ConversationMessage:
        msg = ConversationMessage(
            id=message_id,
            conversation_id=conversation.id,
            role="assistant",
            content="",
            status="streaming",
        )
        db.add(msg)
        conversation.message_count += 1
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def finish_assistant_message(
        db: Session,
        conversation: Conversation,
        message_id: str,
        *,
        content: str,
        status: str = "done",
        error_message: str | None = None,
        citations: list[dict] | None = None,
    ) -> ConversationMessage:
        msg = db.get(ConversationMessage, message_id)
        if not msg or msg.conversation_id != conversation.id:
            raise ConversationNotFoundError
        msg.content = content
        msg.status = status
        msg.error_message = error_message
        msg.references_json = citations
        conversation.last_message_at = datetime.now(UTC)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def build_chat_history(
        db: Session,
        conversation_id: str,
        *,
        exclude_message_id: str | None = None,
        limit_messages: int = 6,
    ) -> list[ChatMessage]:
        rows = db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .where(ConversationMessage.status == "done")
            .order_by(ConversationMessage.created_at.asc())
        ).all()
        items = [r for r in rows if r.id != exclude_message_id and r.content.strip()]
        recent = items[-limit_messages:] if len(items) > limit_messages else items
        result: list[ChatMessage] = []
        for row in recent:
            role = ChatRole.USER if row.role == "user" else ChatRole.ASSISTANT
            result.append(ChatMessage(role=role, content=row.content))
        return result
