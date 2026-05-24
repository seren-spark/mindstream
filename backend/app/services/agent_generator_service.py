"""专家 Agent 异步生成任务。"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.agent import AgentGenerationJob, ExpertAgent
from app.models.knowledge_item import KnowledgeItem
from app.schemas.agent import AgentProfileGenerated
from app.schemas.knowledge_item import KnowledgeItemStatus
from app.services.agent_service import AgentService
from app.services.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)
settings = get_settings()

MIN_ITEMS_FOR_GENERATE = 1
SAMPLE_ITEM_LIMIT = 12
SAMPLE_CHARS = 4000


class AgentGeneratorService:
    @staticmethod
    def create_job(db: Session, knowledge_base_id: int) -> AgentGenerationJob:
        KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
        job = AgentGenerationJob(
            id=str(uuid.uuid4()),
            knowledge_base_id=knowledge_base_id,
            status="pending",
            input_snapshot={},
            model_name=settings.openai_model,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def sample_corpus(db: Session, knowledge_base_id: int) -> tuple[str, int]:
        rows = db.scalars(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.knowledge_base_id == knowledge_base_id,
                KnowledgeItem.status == KnowledgeItemStatus.READY.value,
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(SAMPLE_ITEM_LIMIT)
        ).all()
        parts: list[str] = []
        total = 0
        for item in rows:
            title = item.title or "未命名"
            body = (item.summary or item.content or "")[:800]
            block = f"## {title}\n{body}"
            parts.append(block)
            total += len(block)
            if total >= SAMPLE_CHARS:
                break
        return "\n\n".join(parts), len(rows)

    @staticmethod
    async def generate_profile_with_llm(kb_name: str, kb_description: str, corpus: str) -> AgentProfileGenerated:
        prompt = f"""你是知识库专家人设生成器。根据以下知识库样本，输出 JSON：
{{
  "name": "助手名称",
  "description": "一句话描述",
  "persona": "2-4句人设",
  "tone": "professional|concise|detailed",
  "welcome_message": "欢迎语",
  "suggested_questions": ["问题1","问题2","问题3"],
  "avatar_emoji": "emoji"
}}

知识库：{kb_name}
描述：{kb_description or "无"}

样本内容：
{corpus[:3500]}
"""
        mode = settings.llm_mode.lower()
        if mode == "openai" and settings.openai_api_key:
            return await AgentGeneratorService._openai_profile(prompt)
        return AgentGeneratorService._mock_profile(kb_name, corpus)

    @staticmethod
    def _mock_profile(kb_name: str, corpus: str) -> AgentProfileGenerated:
        return AgentProfileGenerated(
            name=f"{kb_name}专家助手",
            description=f"基于「{kb_name}」知识库的专业问答助手",
            persona=(
                f"你熟悉「{kb_name}」知识库中的内容，能够基于检索到的资料准确回答用户问题，"
                "并在信息不足时明确拒答。"
            ),
            welcome_message=f"你好，我是{kb_name}专家助手，有什么可以帮你？",
            suggested_questions=[
                f"{kb_name}有哪些核心内容？",
                "请总结知识库的主要主题",
            ],
        )

    @staticmethod
    async def _openai_profile(prompt: str) -> AgentProfileGenerated:
        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.openai_model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, headers={"Authorization": f"Bearer {settings.openai_api_key}"}, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw)
            return AgentProfileGenerated.model_validate(parsed)

    @staticmethod
    async def run_job(job_id: str) -> None:
        db = SessionLocal()
        job = None
        try:
            job = db.get(AgentGenerationJob, job_id)
            if not job or job.status not in ("pending", "running"):
                return
            job.status = "running"
            job.started_at = datetime.now(UTC)
            db.commit()

            kb = KnowledgeBaseService.get_knowledge_base(db, job.knowledge_base_id)
            corpus, item_count = AgentGeneratorService.sample_corpus(db, job.knowledge_base_id)
            if item_count < MIN_ITEMS_FOR_GENERATE:
                job.status = "failed"
                job.error_message = "知识库条目不足，请先上传并处理文档"
                job.finished_at = datetime.now(UTC)
                db.commit()
                return

            job.stage = "sampling"
            job.progress_message = "正在采样知识库内容"
            db.commit()

            profile = await AgentGeneratorService.generate_profile_with_llm(
                kb.name, kb.description or "", corpus
            )

            job.stage = "composing"
            job.progress_message = "正在组装 Agent 配置"
            db.commit()

            agent = AgentService.create_from_profile(
                db, job.knowledge_base_id, profile, source="generate", job_id=job.id
            )
            job.agent_id = agent.id
            job.status = "succeeded"
            job.stage = "done"
            job.progress_message = "生成完成"
            job.result_profile = profile.model_dump()
            job.finished_at = datetime.now(UTC)
            db.commit()
        except Exception as exc:
            logger.exception("Agent generation job failed")
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                job.finished_at = datetime.now(UTC)
                db.commit()
        finally:
            db.close()

    @staticmethod
    async def regenerate_agent(db: Session, agent: ExpertAgent) -> ExpertAgent:
        kb = KnowledgeBaseService.get_knowledge_base(db, agent.knowledge_base_id)
        corpus, item_count = AgentGeneratorService.sample_corpus(db, agent.knowledge_base_id)
        if item_count < MIN_ITEMS_FOR_GENERATE:
            raise ValueError("知识库条目不足")
        profile = await AgentGeneratorService.generate_profile_with_llm(
            kb.name, kb.description or "", corpus
        )
        return AgentService.update_from_profile(db, agent, profile, source="regenerate")
