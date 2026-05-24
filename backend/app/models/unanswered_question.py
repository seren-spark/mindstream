from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class UnansweredQuestion(Base, TimestampMixin):
    __tablename__ = "unanswered_questions"
    __table_args__ = (
        UniqueConstraint("knowledge_base_id", "query_norm", name="uq_unanswered_kb_query"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    knowledge_base_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query_text: Mapped[str] = mapped_column(String(500), nullable=False)
    query_norm: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    reason: Mapped[str] = mapped_column(String(30), nullable=False, default="no_citations")
    top_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_user_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    sample_assistant_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    suggested_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    suggested_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("knowledge_items.id", ondelete="SET NULL"),
        nullable=True,
    )
