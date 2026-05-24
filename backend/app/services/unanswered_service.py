"""未命中问题沉淀服务。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.unanswered_question import UnansweredQuestion
from app.schemas.knowledge_item import KnowledgeItemCreate, KnowledgeItemSourceType, KnowledgeItemStatus
from app.schemas.retrieval import RetrievalHit
from app.schemas.unanswered import UnansweredResolveRequest
from app.services.knowledge_base_service import KnowledgeBaseNotFoundError, KnowledgeBaseService
from app.services.knowledge_item_service import KnowledgeItemService
from app.services.miss_detection import (
    classify_miss,
    normalize_query,
    suggest_summary,
    suggest_title,
)


class UnansweredNotFoundError(Exception):
    pass


class UnansweredService:
    @staticmethod
    def record_from_chat(
        db: Session,
        *,
        knowledge_base_id: int,
        query: str,
        hits: list[RetrievalHit],
        citations: list | None,
        assistant_content: str,
        user_message_id: str | None = None,
        assistant_message_id: str | None = None,
    ) -> UnansweredQuestion | None:
        is_miss, reason, top_score = classify_miss(
            query=query,
            hits=hits,
            citations=citations,
            assistant_content=assistant_content,
        )
        if not is_miss:
            return None

        now = datetime.now(UTC)
        norm = normalize_query(query)
        existing = db.scalar(
            select(UnansweredQuestion).where(
                UnansweredQuestion.knowledge_base_id == knowledge_base_id,
                UnansweredQuestion.query_norm == norm,
                UnansweredQuestion.status.in_(("open", "reviewing")),
            )
        )
        if existing:
            existing.occurrence_count += 1
            existing.last_asked_at = now
            existing.reason = reason
            if top_score is not None:
                existing.top_score = max(existing.top_score or 0, top_score)
            if user_message_id:
                existing.sample_user_message_id = user_message_id
            if assistant_message_id:
                existing.sample_assistant_message_id = assistant_message_id
            db.commit()
            db.refresh(existing)
            return existing

        row = UnansweredQuestion(
            id=str(uuid.uuid4()),
            knowledge_base_id=knowledge_base_id,
            query_text=query.strip()[:500],
            query_norm=norm,
            occurrence_count=1,
            first_asked_at=now,
            last_asked_at=now,
            status="open",
            reason=reason,
            top_score=top_score,
            sample_user_message_id=user_message_id,
            sample_assistant_message_id=assistant_message_id,
            suggested_title=suggest_title(query),
            suggested_summary=suggest_summary(query, assistant_content),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def list_questions(
        db: Session,
        knowledge_base_id: int,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[UnansweredQuestion], int]:
        KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
        base = select(UnansweredQuestion).where(
            UnansweredQuestion.knowledge_base_id == knowledge_base_id
        )
        if status:
            base = base.where(UnansweredQuestion.status == status)
        total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = db.scalars(
            base.order_by(
                desc(UnansweredQuestion.occurrence_count),
                desc(UnansweredQuestion.last_asked_at),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total

    @staticmethod
    def get(db: Session, knowledge_base_id: int, question_id: str) -> UnansweredQuestion:
        row = db.scalar(
            select(UnansweredQuestion).where(
                UnansweredQuestion.id == question_id,
                UnansweredQuestion.knowledge_base_id == knowledge_base_id,
            )
        )
        if not row:
            raise UnansweredNotFoundError
        return row

    @staticmethod
    def update(
        db: Session,
        knowledge_base_id: int,
        question_id: str,
        *,
        status: str | None = None,
        suggested_title: str | None = None,
        suggested_summary: str | None = None,
    ) -> UnansweredQuestion:
        row = UnansweredService.get(db, knowledge_base_id, question_id)
        if status is not None:
            row.status = status
        if suggested_title is not None:
            row.suggested_title = suggested_title
        if suggested_summary is not None:
            row.suggested_summary = suggested_summary
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def dismiss(db: Session, knowledge_base_id: int, question_id: str) -> UnansweredQuestion:
        return UnansweredService.update(
            db, knowledge_base_id, question_id, status="dismissed"
        )

    @staticmethod
    def resolve_to_item(
        db: Session,
        knowledge_base_id: int,
        question_id: str,
        payload: UnansweredResolveRequest,
    ) -> tuple[UnansweredQuestion, int]:
        row = UnansweredService.get(db, knowledge_base_id, question_id)
        if row.status == "resolved":
            raise ValueError("该问题已沉淀")

        title = (payload.title or row.suggested_title or row.query_text)[:200]
        summary = payload.summary or row.suggested_summary
        content = payload.content or summary or f"针对用户常见问题「{row.query_text}」的补充说明。\n\n{summary or ''}"

        item = KnowledgeItemService.create_item(
            db,
            knowledge_base_id,
            KnowledgeItemCreate(
                title=title,
                content=content.strip(),
                summary=summary[:2000] if summary else None,
                source_type=KnowledgeItemSourceType.MANUAL,
                status=KnowledgeItemStatus.PENDING,
                tags=["未命中沉淀"],
                category="运营补充",
            ),
        )
        row.status = "resolved"
        row.resolved_item_id = item.id
        db.commit()
        db.refresh(row)
        return row, item.id

    @staticmethod
    def top_for_stats(
        db: Session,
        *,
        knowledge_base_id: int | None = None,
        limit: int = 20,
        days: int = 30,
    ) -> list[UnansweredQuestion]:
        since = datetime.now(UTC) - timedelta(days=days)
        stmt = select(UnansweredQuestion).where(
            UnansweredQuestion.status.in_(("open", "reviewing")),
            UnansweredQuestion.last_asked_at >= since,
        )
        if knowledge_base_id is not None:
            stmt = stmt.where(UnansweredQuestion.knowledge_base_id == knowledge_base_id)
        return list(
            db.scalars(
                stmt.order_by(
                    desc(UnansweredQuestion.occurrence_count),
                    desc(UnansweredQuestion.last_asked_at),
                ).limit(limit)
            ).all()
        )
