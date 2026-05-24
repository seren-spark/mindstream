"""RAG 流式问答编排。"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from sqlalchemy.orm import Session

from app.schemas.chat import ChatStreamRequest
from app.schemas.prompt import ChatMessage, PromptBuildRequest
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

        try:
            kb = KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
        except KnowledgeBaseNotFoundError:
            yield format_sse({"type": "error", "message": "知识库不存在"})
            return

        if kb.status == "disabled":
            yield format_sse({"type": "error", "message": "知识库已禁用"})
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
                    history=payload.history,
                    knowledge_base_name=kb.name,
                )
            )

            async for delta in LlmService.stream_completion(
                prompt.messages,
                prompt_result=prompt,
                query=payload.query,
            ):
                if delta:
                    yield format_sse({"type": "token", "delta": delta})

            citations = [c.model_dump() for c in prompt.citations]
            yield format_sse({"type": "references", "citations": citations})
            yield format_sse({"type": "done"})

        except Exception as exc:
            yield format_sse({"type": "error", "message": f"问答失败: {exc}"})
