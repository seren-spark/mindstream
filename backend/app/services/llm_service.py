"""LLM 流式调用 — Demo mock / OpenAI 兼容 API。"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator

import httpx

from app.core.config import get_settings
from app.schemas.prompt import LlmMessage, PromptBuildResult

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_mock_answer(prompt: PromptBuildResult | None, query: str) -> str:
    if not prompt or not prompt.has_context or not prompt.citations:
        return (
            "根据现有知识库资料，无法找到相关信息。\n\n"
            f"您的问题「{query}」在当前知识库中没有足够依据，请尝试换关键词或补充文档。"
        )

    lines = [
        "## 回答\n",
        f"针对您的问题「{query}」，根据知识库检索结果，结论如下：\n",
    ]
    for cite in prompt.citations[:3]:
        excerpt = cite.content_excerpt or cite.highlight_text
        lines.append(f"- {excerpt} [{cite.index}]")
    lines.append("\n### 说明\n")
    lines.append("以上内容均来自知识库参考片段，关键结论已标注引用编号。")
    return "\n".join(lines)


class LlmService:
    @staticmethod
    async def stream_completion(
        messages: list[LlmMessage],
        *,
        prompt_result: PromptBuildResult | None = None,
        query: str = "",
    ) -> AsyncIterator[str]:
        mode = settings.llm_mode.lower()
        if mode == "openai" and settings.openai_api_key:
            async for delta in LlmService._stream_openai(messages):
                yield delta
            return

        text = _build_mock_answer(prompt_result, query)
        delay = settings.llm_stream_delay_ms / 1000.0
        # 按小片段输出，模拟 token 流
        step = max(1, settings.llm_stream_chunk_chars)
        for i in range(0, len(text), step):
            yield text[i : i + step]
            if delay > 0:
                await asyncio.sleep(delay)

    @staticmethod
    async def _stream_openai(messages: list[LlmMessage]) -> AsyncIterator[str]:
        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_model,
            "messages": [m.model_dump() for m in messages],
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"].get("content") or ""
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except Exception as exc:
            logger.exception("OpenAI stream failed")
            yield f"\n\n[LLM 调用失败: {exc}]"
