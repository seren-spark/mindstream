"""专家 Agent CRUD 与生命周期。"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.agent import AgentGenerationJob, AgentVersion, ExpertAgent
from app.schemas.agent import AgentProfileGenerated, ExpertAgentCreate, ExpertAgentUpdate
from app.services.agent_prompt_composer import AgentPromptComposer
from app.services.knowledge_base_service import KnowledgeBaseService

INJECTION_DENYLIST = (
    "忽略以上",
    "忽略前面",
    "ignore previous",
    "ignore all",
    "disregard",
    "forget your instructions",
    "你现在是",
    "假装你是",
)


class AgentNotFoundError(Exception):
    pass


class AgentInvalidStateError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def _slugify(name: str) -> str:
    text = name.strip().lower()
    text = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return (text[:60] or "agent").strip("-")


def _sanitize_custom_instructions(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    lowered = value.lower()
    for phrase in INJECTION_DENYLIST:
        if phrase.lower() in lowered:
            raise AgentInvalidStateError(f"自定义说明包含不允许的内容：{phrase}")
    return value.strip()[:1000]


class AgentService:
    @staticmethod
    def _unique_slug(db: Session, knowledge_base_id: int, base_slug: str) -> str:
        slug = base_slug
        n = 1
        while db.scalar(
            select(ExpertAgent.id).where(
                ExpertAgent.knowledge_base_id == knowledge_base_id,
                ExpertAgent.slug == slug,
            )
        ):
            slug = f"{base_slug}-{n}"
            n += 1
        return slug[:64]

    @staticmethod
    def list_agents(
        db: Session,
        knowledge_base_id: int,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ExpertAgent], int]:
        KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
        base = select(ExpertAgent).where(ExpertAgent.knowledge_base_id == knowledge_base_id)
        if status:
            base = base.where(ExpertAgent.status == status)
        total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = db.scalars(
            base.order_by(desc(ExpertAgent.updated_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total

    @staticmethod
    def get(db: Session, knowledge_base_id: int, agent_id: str) -> ExpertAgent:
        agent = db.scalar(
            select(ExpertAgent).where(
                ExpertAgent.id == agent_id,
                ExpertAgent.knowledge_base_id == knowledge_base_id,
            )
        )
        if not agent:
            raise AgentNotFoundError
        return agent

    @staticmethod
    def get_published(db: Session, knowledge_base_id: int, agent_id: str) -> ExpertAgent:
        agent = AgentService.get(db, knowledge_base_id, agent_id)
        if agent.status != "published":
            raise AgentInvalidStateError("Agent 未发布或已归档")
        return agent

    @staticmethod
    def create_manual(db: Session, knowledge_base_id: int, payload: ExpertAgentCreate) -> ExpertAgent:
        KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
        slug = AgentService._unique_slug(db, knowledge_base_id, _slugify(payload.name))
        custom = _sanitize_custom_instructions(payload.custom_instructions)
        agent = ExpertAgent(
            id=str(uuid.uuid4()),
            knowledge_base_id=knowledge_base_id,
            slug=slug,
            name=payload.name,
            description=payload.description or "",
            persona=payload.persona or f"你是{payload.name}，负责基于知识库回答专业问题。",
            tone=payload.tone,
            custom_instructions=custom,
            welcome_message=payload.welcome_message,
            suggested_questions=payload.suggested_questions or [],
            avatar_type=payload.avatar_type,
            avatar_value=payload.avatar_value,
            status="draft",
        )
        db.add(agent)
        db.flush()
        AgentService._save_version(db, agent, source="manual")
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def create_from_profile(
        db: Session,
        knowledge_base_id: int,
        profile: AgentProfileGenerated,
        *,
        source: str,
        job_id: str | None = None,
    ) -> ExpertAgent:
        slug = AgentService._unique_slug(db, knowledge_base_id, _slugify(profile.name))
        agent = ExpertAgent(
            id=str(uuid.uuid4()),
            knowledge_base_id=knowledge_base_id,
            slug=slug,
            name=profile.name,
            description=profile.description,
            persona=profile.persona,
            tone=profile.tone,
            welcome_message=profile.welcome_message,
            suggested_questions=profile.suggested_questions,
            avatar_type="emoji",
            avatar_value=profile.avatar_emoji,
            status="draft",
        )
        db.add(agent)
        db.flush()
        AgentService._save_version(db, agent, source=source, job_id=job_id)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def update_from_profile(
        db: Session,
        agent: ExpertAgent,
        profile: AgentProfileGenerated,
        *,
        source: str,
    ) -> ExpertAgent:
        agent.name = profile.name
        agent.description = profile.description
        agent.persona = profile.persona
        agent.tone = profile.tone
        agent.welcome_message = profile.welcome_message
        agent.suggested_questions = profile.suggested_questions
        agent.avatar_value = profile.avatar_emoji
        AgentService._save_version(db, agent, source=source)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def update(
        db: Session,
        knowledge_base_id: int,
        agent_id: str,
        payload: ExpertAgentUpdate,
    ) -> ExpertAgent:
        agent = AgentService.get(db, knowledge_base_id, agent_id)
        data = payload.model_dump(exclude_unset=True)
        if "custom_instructions" in data:
            data["custom_instructions"] = _sanitize_custom_instructions(data["custom_instructions"])
        for key, value in data.items():
            setattr(agent, key, value)
        AgentService._save_version(db, agent, source="edit")
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def publish(db: Session, knowledge_base_id: int, agent_id: str) -> ExpertAgent:
        agent = AgentService.get(db, knowledge_base_id, agent_id)
        if agent.status == "archived":
            raise AgentInvalidStateError("已归档的 Agent 无法发布")
        agent.status = "published"
        agent.published_at = datetime.now(UTC)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def archive(db: Session, knowledge_base_id: int, agent_id: str) -> ExpertAgent:
        agent = AgentService.get(db, knowledge_base_id, agent_id)
        agent.status = "archived"
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def delete(db: Session, knowledge_base_id: int, agent_id: str) -> None:
        agent = AgentService.get(db, knowledge_base_id, agent_id)
        if agent.status != "draft":
            raise AgentInvalidStateError("仅草稿状态可删除，已发布请归档")
        db.delete(agent)
        db.commit()

    @staticmethod
    def list_versions(db: Session, knowledge_base_id: int, agent_id: str) -> list[AgentVersion]:
        AgentService.get(db, knowledge_base_id, agent_id)
        return list(
            db.scalars(
                select(AgentVersion)
                .where(AgentVersion.agent_id == agent_id)
                .order_by(AgentVersion.version_number.desc())
            ).all()
        )

    @staticmethod
    def get_version(
        db: Session, knowledge_base_id: int, agent_id: str, version_id: str
    ) -> AgentVersion:
        AgentService.get(db, knowledge_base_id, agent_id)
        version = db.scalar(
            select(AgentVersion).where(
                AgentVersion.id == version_id,
                AgentVersion.agent_id == agent_id,
            )
        )
        if not version:
            raise AgentNotFoundError
        return version

    @staticmethod
    def get_job(db: Session, knowledge_base_id: int, job_id: str) -> AgentGenerationJob:
        job = db.scalar(
            select(AgentGenerationJob).where(
                AgentGenerationJob.id == job_id,
                AgentGenerationJob.knowledge_base_id == knowledge_base_id,
            )
        )
        if not job:
            raise AgentNotFoundError
        return job

    @staticmethod
    def _save_version(
        db: Session,
        agent: ExpertAgent,
        *,
        source: str,
        job_id: str | None = None,
    ) -> AgentVersion:
        kb = KnowledgeBaseService.get_knowledge_base(db, agent.knowledge_base_id)
        next_num = (
            db.scalar(
                select(func.max(AgentVersion.version_number)).where(AgentVersion.agent_id == agent.id)
            )
            or 0
        ) + 1
        snapshot = {
            "name": agent.name,
            "description": agent.description,
            "persona": agent.persona,
            "tone": agent.tone,
            "custom_instructions": agent.custom_instructions,
            "welcome_message": agent.welcome_message,
            "suggested_questions": agent.suggested_questions,
            "avatar_type": agent.avatar_type,
            "avatar_value": agent.avatar_value,
        }
        prompt = AgentPromptComposer.preview_without_context(agent, kb.name)
        version = AgentVersion(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            version_number=next_num,
            source=source,
            profile_snapshot=snapshot,
            prompt_snapshot=prompt,
            generation_job_id=job_id,
        )
        db.add(version)
        agent.current_version_id = version.id
        return version
