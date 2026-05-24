"""Dashboard 统计 — 只读聚合。"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_item import KnowledgeItem
from app.models.message import ConversationMessage
from app.schemas.knowledge_item import KnowledgeItemStatus
from app.schemas.stats import (
    HeatItem,
    StatsHeatResponse,
    StatsOverviewResponse,
    StatsTrendResponse,
    StatsUnansweredResponse,
    TrendPoint,
    UnansweredItem,
)
from app.services.miss_detection import MISS_PHRASE
from app.services.unanswered_service import UnansweredService


def _period_start(days: int) -> datetime:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return start - timedelta(days=days - 1)


def _is_hit(msg: ConversationMessage) -> bool:
    refs = msg.references_json
    return bool(refs and isinstance(refs, list) and len(refs) > 0)


def _is_miss(msg: ConversationMessage) -> bool:
    if msg.role != "assistant" or msg.status != "done":
        return False
    if _is_hit(msg):
        return False
    if MISS_PHRASE in (msg.content or ""):
        return True
    return not msg.references_json or len(msg.references_json) == 0


class StatsService:
    @staticmethod
    def _assistant_messages(
        db: Session,
        *,
        knowledge_base_id: int | None,
        since: datetime,
    ) -> list[ConversationMessage]:
        stmt = (
            select(ConversationMessage)
            .join(Conversation, ConversationMessage.conversation_id == Conversation.id)
            .where(
                ConversationMessage.role == "assistant",
                ConversationMessage.status == "done",
                ConversationMessage.created_at >= since,
            )
        )
        if knowledge_base_id is not None:
            stmt = stmt.where(Conversation.knowledge_base_id == knowledge_base_id)
        return list(db.scalars(stmt.order_by(ConversationMessage.created_at.asc())).all())

    @staticmethod
    def _user_messages(
        db: Session,
        *,
        knowledge_base_id: int | None,
        since: datetime,
    ) -> list[tuple[ConversationMessage, int, str]]:
        stmt = (
            select(ConversationMessage, Conversation.knowledge_base_id, KnowledgeBase.name)
            .join(Conversation, ConversationMessage.conversation_id == Conversation.id)
            .join(KnowledgeBase, Conversation.knowledge_base_id == KnowledgeBase.id)
            .where(
                ConversationMessage.role == "user",
                ConversationMessage.created_at >= since,
            )
        )
        if knowledge_base_id is not None:
            stmt = stmt.where(Conversation.knowledge_base_id == knowledge_base_id)
        rows = db.execute(stmt.order_by(ConversationMessage.created_at.asc())).all()
        return [(r[0], r[1], r[2]) for r in rows]

    @staticmethod
    def overview(
        db: Session,
        *,
        knowledge_base_id: int | None = None,
        days: int = 7,
    ) -> StatsOverviewResponse:
        since = _period_start(days)
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        kb_query = select(func.count()).select_from(KnowledgeBase)
        if knowledge_base_id is not None:
            kb_query = kb_query.where(KnowledgeBase.id == knowledge_base_id)
        kb_count = db.scalar(kb_query) or 0

        item_query = select(func.count()).select_from(KnowledgeItem)
        if knowledge_base_id is not None:
            item_query = item_query.where(KnowledgeItem.knowledge_base_id == knowledge_base_id)
        item_count = db.scalar(item_query) or 0

        ready_query = select(func.count()).select_from(KnowledgeItem).where(
            KnowledgeItem.status == KnowledgeItemStatus.READY.value
        )
        if knowledge_base_id is not None:
            ready_query = ready_query.where(KnowledgeItem.knowledge_base_id == knowledge_base_id)
        item_ready = db.scalar(ready_query) or 0

        user_rows = StatsService._user_messages(db, knowledge_base_id=knowledge_base_id, since=since)
        question_period = len(user_rows)
        question_today = sum(1 for m, _, _ in user_rows if m.created_at >= today_start)

        assistants = StatsService._assistant_messages(
            db, knowledge_base_id=knowledge_base_id, since=since
        )
        hit_count = sum(1 for m in assistants if _is_hit(m))
        hit_rate = hit_count / len(assistants) if assistants else 0.0

        prev_since = since - timedelta(days=days)
        prev_assistants = StatsService._assistant_messages(
            db, knowledge_base_id=knowledge_base_id, since=prev_since
        )
        prev_in_period = [m for m in prev_assistants if m.created_at < since]
        prev_hits = sum(1 for m in prev_in_period if _is_hit(m))
        prev_rate = prev_hits / len(prev_in_period) if prev_in_period else hit_rate
        hit_rate_delta = hit_rate - prev_rate

        return StatsOverviewResponse(
            knowledge_base_count=kb_count,
            item_count=item_count,
            item_ready_count=item_ready,
            question_count_today=question_today,
            question_count_period=question_period,
            hit_rate=round(hit_rate, 4),
            hit_rate_delta=round(hit_rate_delta, 4),
            period_days=days,
            generated_at=datetime.now(UTC),
        )

    @staticmethod
    def trend(
        db: Session,
        *,
        knowledge_base_id: int | None = None,
        days: int = 7,
    ) -> StatsTrendResponse:
        since = _period_start(days)
        user_rows = StatsService._user_messages(db, knowledge_base_id=knowledge_base_id, since=since)
        assistants = StatsService._assistant_messages(
            db, knowledge_base_id=knowledge_base_id, since=since
        )

        q_by_day: dict[str, int] = defaultdict(int)
        for msg, _, _ in user_rows:
            d = msg.created_at.astimezone(UTC).date().isoformat()
            q_by_day[d] += 1

        hit_by_day: dict[str, int] = defaultdict(int)
        miss_by_day: dict[str, int] = defaultdict(int)
        for msg in assistants:
            d = msg.created_at.astimezone(UTC).date().isoformat()
            if _is_hit(msg):
                hit_by_day[d] += 1
            elif _is_miss(msg):
                miss_by_day[d] += 1

        points: list[TrendPoint] = []
        start_date = since.date()
        for i in range(days):
            d = (start_date + timedelta(days=i)).isoformat()
            points.append(
                TrendPoint(
                    date=d,
                    question_count=q_by_day.get(d, 0),
                    hit_count=hit_by_day.get(d, 0),
                    miss_count=miss_by_day.get(d, 0),
                )
            )

        total = sum(p.question_count for p in points)
        avg = round(total / days, 1) if days else 0.0

        return StatsTrendResponse(
            period_days=days,
            knowledge_base_id=knowledge_base_id,
            points=points,
            total_questions=total,
            avg_daily=avg,
        )

    @staticmethod
    def heat(
        db: Session,
        *,
        knowledge_base_id: int | None = None,
        days: int = 30,
        limit: int = 10,
    ) -> StatsHeatResponse:
        since = _period_start(days)
        assistants = StatsService._assistant_messages(
            db, knowledge_base_id=knowledge_base_id, since=since
        )

        cite_counts: dict[int, int] = defaultdict(int)
        last_cited: dict[int, datetime] = {}
        conv_ids_by_item: dict[int, set[str]] = defaultdict(set)

        for msg in assistants:
            if not _is_hit(msg):
                continue
            for ref in msg.references_json or []:
                if not isinstance(ref, dict):
                    continue
                item_id = ref.get("knowledge_item_id")
                if not item_id:
                    continue
                iid = int(item_id)
                cite_counts[iid] += 1
                ts = msg.created_at
                if iid not in last_cited or ts > last_cited[iid]:
                    last_cited[iid] = ts
                conv_ids_by_item[iid].add(msg.conversation_id)

        if not cite_counts:
            return StatsHeatResponse(
                period_days=days, knowledge_base_id=knowledge_base_id, items=[]
            )

        sorted_ids = sorted(cite_counts.keys(), key=lambda k: cite_counts[k], reverse=True)[:limit]
        items_db = {
            i.id: i
            for i in db.scalars(
                select(KnowledgeItem).where(KnowledgeItem.id.in_(sorted_ids))
            ).all()
        }
        kb_names = {kb.id: kb.name for kb in db.scalars(select(KnowledgeBase)).all()}

        items: list[HeatItem] = []
        for rank, item_id in enumerate(sorted_ids, start=1):
            item = items_db.get(item_id)
            if not item:
                continue
            items.append(
                HeatItem(
                    rank=rank,
                    knowledge_item_id=item_id,
                    title=item.title,
                    knowledge_base_id=item.knowledge_base_id,
                    knowledge_base_name=kb_names.get(item.knowledge_base_id, ""),
                    cite_count=cite_counts[item_id],
                    unique_questions=len(conv_ids_by_item[item_id]),
                    last_cited_at=last_cited.get(item_id),
                )
            )

        return StatsHeatResponse(
            period_days=days,
            knowledge_base_id=knowledge_base_id,
            items=items,
        )

    @staticmethod
    def unanswered(
        db: Session,
        *,
        knowledge_base_id: int | None = None,
        days: int = 30,
        limit: int = 20,
    ) -> StatsUnansweredResponse:
        rows = UnansweredService.top_for_stats(
            db, knowledge_base_id=knowledge_base_id, limit=limit, days=days
        )
        if rows:
            kb_names = {
                kb.id: kb.name for kb in db.scalars(select(KnowledgeBase)).all()
            }
            items = [
                UnansweredItem(
                    id=r.id,
                    query_text=r.query_text,
                    occurrence_count=r.occurrence_count,
                    last_asked_at=r.last_asked_at,
                    knowledge_base_id=r.knowledge_base_id,
                    knowledge_base_name=kb_names.get(r.knowledge_base_id, ""),
                    sample_message_id=r.sample_user_message_id or r.id,
                    suggested_action="upload",
                )
                for r in rows
            ]
            total = sum(r.occurrence_count for r in rows)
            return StatsUnansweredResponse(
                period_days=days,
                knowledge_base_id=knowledge_base_id,
                total_miss_count=total,
                items=items,
            )

        return StatsService._unanswered_from_messages(
            db, knowledge_base_id=knowledge_base_id, days=days, limit=limit
        )

    @staticmethod
    def _unanswered_from_messages(
        db: Session,
        *,
        knowledge_base_id: int | None = None,
        days: int = 30,
        limit: int = 20,
    ) -> StatsUnansweredResponse:
        since = _period_start(days)

        stmt = (
            select(ConversationMessage, Conversation.knowledge_base_id, KnowledgeBase.name)
            .join(Conversation, ConversationMessage.conversation_id == Conversation.id)
            .join(KnowledgeBase, Conversation.knowledge_base_id == KnowledgeBase.id)
            .where(ConversationMessage.created_at >= since)
        )
        if knowledge_base_id is not None:
            stmt = stmt.where(Conversation.knowledge_base_id == knowledge_base_id)
        rows = db.execute(stmt.order_by(ConversationMessage.created_at.asc())).all()

        by_conv: dict[str, list[tuple[ConversationMessage, int, str]]] = defaultdict(list)
        for msg, kb_id, kb_name in rows:
            by_conv[msg.conversation_id].append((msg, kb_id, kb_name))

        agg: dict[tuple[str, int], dict] = {}
        total_miss = 0

        for conv_msgs in by_conv.values():
            for i, (msg, kb_id, kb_name) in enumerate(conv_msgs):
                if msg.role != "assistant" or not _is_miss(msg):
                    continue
                total_miss += 1
                user_msg = None
                for j in range(i - 1, -1, -1):
                    if conv_msgs[j][0].role == "user":
                        user_msg = conv_msgs[j]
                        break
                if not user_msg:
                    continue
                u, kid, kname = user_msg
                key_text = u.content.strip().replace("\n", " ")
                if not key_text:
                    continue
                norm = key_text.lower()
                key = (norm, kid)
                if key not in agg:
                    agg[key] = {
                        "query_text": key_text[:200],
                        "occurrence_count": 0,
                        "last_asked_at": u.created_at,
                        "knowledge_base_id": kid,
                        "knowledge_base_name": kname,
                        "sample_message_id": u.id,
                    }
                agg[key]["occurrence_count"] += 1
                if u.created_at > agg[key]["last_asked_at"]:
                    agg[key]["last_asked_at"] = u.created_at
                    agg[key]["sample_message_id"] = u.id

        sorted_items = sorted(
            agg.values(), key=lambda x: (x["occurrence_count"], x["last_asked_at"]), reverse=True
        )[:limit]

        items = [UnansweredItem(**row) for row in sorted_items]

        return StatsUnansweredResponse(
            period_days=days,
            knowledge_base_id=knowledge_base_id,
            total_miss_count=total_miss,
            items=items,
        )
