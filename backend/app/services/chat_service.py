"""RAG 流式问答编排。"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from sqlalchemy.orm import Session

from app.models.agent import ExpertAgent
from app.schemas.chat import ChatStreamRequest
from app.schemas.prompt import ChatMessage, PromptBuildRequest
from app.services.agent_service import AgentInvalidStateError, AgentNotFoundError, AgentService
from app.services.conversation_service import ConversationNotFoundError, ConversationService
from app.services.knowledge_base_service import KnowledgeBaseNotFoundError, KnowledgeBaseService
from app.services.llm_service import LlmService
from app.services.prompt_builder_service import PromptBuilderService
from app.services.retrieval_service import RetrievalService


def format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class ChatService:
    @staticmethod
    async def stream_chat(
        db: Session,
        knowledge_base_id: int,
        payload: ChatStreamRequest,
    ) -> AsyncIterator[str]:
        message_id = str(uuid.uuid4())
        assistant_parts: list[str] = []
        citations_payload: list[dict] | None = None
        conv = None
        agent: ExpertAgent | None = None

        try:
            kb = KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
        except KnowledgeBaseNotFoundError:
            yield format_sse({"type": "error", "message": "知识库不存在"})
            return

        if kb.status == "disabled":
            yield format_sse({"type": "error", "message": "知识库已禁用"})
            return

        if payload.agent_id:
            try:
                agent = AgentService.get_published(db, knowledge_base_id, payload.agent_id)
            except AgentNotFoundError:
                yield format_sse({"type": "error", "message": "Agent 不存在"})
                return
            except AgentInvalidStateError as exc:
                yield format_sse({"type": "error", "message": exc.message})
                return

        history: list[ChatMessage] = list(payload.history)
        user_message_id = str(uuid.uuid4())

        if payload.conversation_id:
            try:
                conv = ConversationService.get(db, knowledge_base_id, payload.conversation_id)
                if agent and conv.agent_id and conv.agent_id != agent.id:
                    yield format_sse({"type": "error", "message": "会话与 Agent 不匹配"})
                    return
                history = ConversationService.build_chat_history(db, conv.id)
                ConversationService.add_user_message(
                    db,
                    conv,
                    message_id=user_message_id,
                    content=payload.query,
                )
                ConversationService.start_assistant_message(db, conv, message_id=message_id)
            except ConversationNotFoundError:
                yield format_sse({"type": "error", "message": "会话不存在"})
                return

        yield format_sse({"type": "start", "message_id": message_id})

        try:
            search = RetrievalService.hybrid_search(
                db,
                knowledge_base_id,
                payload.query,
                top_k=payload.top_k,
                filter_=payload.filter,
            )

            prompt = PromptBuilderService.build(
                PromptBuildRequest(
                    query=payload.query,
                    hits=search.hits,
                    history=history,
                    knowledge_base_name=kb.name,
                ),
                agent=agent,
            )

            async for delta in LlmService.stream_completion(
                prompt.messages,
                prompt_result=prompt,
                query=payload.query,
            ):
                if delta:
                    assistant_parts.append(delta)
                    yield format_sse({"type": "token", "delta": delta})

            citations_payload = [c.model_dump() for c in prompt.citations]
            yield format_sse({"type": "references", "citations": citations_payload})
            yield format_sse({"type": "done"})

            if conv:
                ConversationService.finish_assistant_message(
                    db,
                    conv,
                    message_id,
                    content="".join(assistant_parts),
                    status="done",
                    citations=citations_payload,
                )

        except Exception as exc:
            err = f"问答失败: {exc}"
            if conv:
                ConversationService.finish_assistant_message(
                    db,
                    conv,
                    message_id,
                    content="".join(assistant_parts),
                    status="error",
                    error_message=err,
                    citations=citations_payload,
                )
            yield format_sse({"type": "error", "message": err})
