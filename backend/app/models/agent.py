from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class ExpertAgent(Base, TimestampMixin):
    __tablename__ = "expert_agents"
    __table_args__ = (UniqueConstraint("knowledge_base_id", "slug", name="uq_agent_kb_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    knowledge_base_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    persona: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str] = mapped_column(String(50), nullable=False, default="professional")
    custom_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    welcome_message: Mapped[str] = mapped_column(String(800), nullable=False)
    suggested_questions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    avatar_type: Mapped[str] = mapped_column(String(20), nullable=False, default="emoji")
    avatar_value: Mapped[str] = mapped_column(String(500), nullable=False, default="🤖")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    current_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    versions: Mapped[list["AgentVersion"]] = relationship(
        "AgentVersion",
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by="AgentVersion.version_number",
    )


class AgentVersion(Base, TimestampMixin):
    __tablename__ = "agent_versions"
    __table_args__ = (UniqueConstraint("agent_id", "version_number", name="uq_agent_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_id: Mapped[str] = mapped_column(
        ForeignKey("expert_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    profile_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    prompt_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    generation_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    agent: Mapped["ExpertAgent"] = relationship("ExpertAgent", back_populates="versions")


class AgentGenerationJob(Base, TimestampMixin):
    __tablename__ = "agent_generation_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    knowledge_base_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    progress_message: Mapped[str | None] = mapped_column(String(200), nullable=True)
    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
