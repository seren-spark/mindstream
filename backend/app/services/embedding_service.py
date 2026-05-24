"""Embedding 服务 — 批量向量化、重试、缓存。"""

from __future__ import annotations

import hashlib
import logging
import math
import time
from functools import lru_cache

from app.core.config import get_settings
from app.schemas.embedding import EmbeddingBatchResult, EmbeddingInput, EmbeddingRecord
from app.services.embedding_cache import get_embedding_cache

logger = logging.getLogger(__name__)
settings = get_settings()

HASH_EMBEDDING_DIM = 384


class EmbeddingPipelineError(Exception):
    """向量化 pipeline 失败，供条目状态机捕获。"""


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class _HashEmbeddingBackend:
    """确定性伪向量，Demo / CI 免 API。"""

    def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return [self._embed_one(t) for t in input]

    def _embed_one(self, text: str) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values = [(seed[i % len(seed)] / 255.0) * 2.0 - 1.0 for i in range(HASH_EMBEDDING_DIM)]
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]


@lru_cache
def _get_chroma_default_backend():
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    return DefaultEmbeddingFunction()


def get_model_name() -> str:
    return settings.embedding_mode.lower()


def _get_backend():
    mode = get_model_name()
    if mode == "hash":
        return _HashEmbeddingBackend()
    return _get_chroma_default_backend()


def _call_backend(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    backend = _get_backend()
    return backend(texts)


def _embed_batch_with_retry(texts: list[str]) -> list[list[float]]:
    last_error: Exception | None = None
    for attempt in range(settings.embedding_max_retries + 1):
        try:
            return _call_backend(texts)
        except Exception as exc:
            last_error = exc
            if attempt >= settings.embedding_max_retries:
                break
            delay = settings.embedding_retry_base_delay * (2**attempt)
            logger.warning(
                "Embedding batch failed (attempt %s/%s), retry in %.1fs: %s",
                attempt + 1,
                settings.embedding_max_retries + 1,
                delay,
                exc,
            )
            time.sleep(delay)
    raise EmbeddingPipelineError(f"向量化失败，已重试 {settings.embedding_max_retries} 次: {last_error}")


class EmbeddingService:
    @staticmethod
    def build_inputs(
        drafts: list,
        *,
        knowledge_item_id: int,
    ) -> list[EmbeddingInput]:
        """从 ChunkDraft 列表构造 EmbeddingInput。"""
        sorted_drafts = sorted(drafts, key=lambda d: d.order_index)
        return [
            EmbeddingInput(
                chunk_id=d.chunk_id,
                text=d.content,
                text_hash=text_hash(d.content),
                knowledge_item_id=knowledge_item_id,
                order_index=d.order_index,
            )
            for d in sorted_drafts
        ]

    @staticmethod
    def embed_chunks(inputs: list[EmbeddingInput]) -> EmbeddingBatchResult:
        """批量向量化：缓存命中 + 分 batch API 调用 + 重试。"""
        if not inputs:
            return EmbeddingBatchResult(model_name=get_model_name())

        model_name = get_model_name()
        cache = get_embedding_cache()
        records: list[EmbeddingRecord] = []
        cache_hits = 0
        api_calls = 0

        pending: list[EmbeddingInput] = []
        for inp in inputs:
            cached = cache.get(model_name, inp.text_hash) if settings.embedding_cache_enabled else None
            if cached is not None:
                records.append(
                    EmbeddingRecord(
                        chunk_id=inp.chunk_id,
                        text_hash=inp.text_hash,
                        vector=cached,
                        dimension=len(cached),
                        from_cache=True,
                    )
                )
                cache_hits += 1
            else:
                pending.append(inp)

        batch_size = settings.embedding_batch_size
        for i in range(0, len(pending), batch_size):
            batch = pending[i : i + batch_size]
            texts = [b.text for b in batch]
            vectors = _embed_batch_with_retry(texts)
            api_calls += 1

            if len(vectors) != len(batch):
                raise EmbeddingPipelineError(
                    f"Embedding 返回数量不匹配：期望 {len(batch)}，实际 {len(vectors)}"
                )

            for inp, vector in zip(batch, vectors, strict=True):
                if settings.embedding_cache_enabled:
                    cache.set(model_name, inp.text_hash, vector)
                records.append(
                    EmbeddingRecord(
                        chunk_id=inp.chunk_id,
                        text_hash=inp.text_hash,
                        vector=vector,
                        dimension=len(vector),
                        from_cache=False,
                    )
                )

        order_map = {inp.chunk_id: inp.order_index for inp in inputs}
        records.sort(key=lambda r: order_map.get(r.chunk_id, 0))
        return EmbeddingBatchResult(
            records=records,
            total=len(records),
            cache_hits=cache_hits,
            api_calls=api_calls,
            model_name=model_name,
        )

    @staticmethod
    def embed_texts(texts: list[str]) -> list[list[float]]:
        """兼容旧接口：纯文本列表 → 向量（带 batch + retry + cache）。"""
        inputs = [
            EmbeddingInput(
                chunk_id=str(idx),
                text=t,
                text_hash=text_hash(t),
                knowledge_item_id=0,
                order_index=idx,
            )
            for idx, t in enumerate(texts)
        ]
        result = EmbeddingService.embed_chunks(inputs)
        return [r.vector for r in result.records]

    @staticmethod
    def embed_query(text: str) -> list[float]:
        """单条 query 向量化（检索用，走同一 cache/retry 路径）。"""
        return EmbeddingService.embed_texts([text])[0]
