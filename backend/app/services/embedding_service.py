"""Embedding 服务 — 将 chunk 文本转为向量。"""

from __future__ import annotations

import hashlib
import math
from functools import lru_cache

from app.core.config import get_settings

settings = get_settings()

HASH_EMBEDDING_DIM = 384


class _HashEmbeddingBackend:
    """确定性伪向量，用于无模型下载的测试与 CI。"""

    def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return [self._embed_one(text) for text in input]

    def _embed_one(self, text: str) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for i in range(HASH_EMBEDDING_DIM):
            byte = seed[i % len(seed)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]


@lru_cache
def _get_chroma_default_backend():
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    return DefaultEmbeddingFunction()


def _get_backend():
    mode = settings.embedding_mode.lower()
    if mode == "hash":
        return _HashEmbeddingBackend()
    return _get_chroma_default_backend()


class EmbeddingService:
    @staticmethod
    def embed_texts(texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        backend = _get_backend()
        return backend(texts)

    @staticmethod
    def embed_query(text: str) -> list[float]:
        vectors = EmbeddingService.embed_texts([text])
        return vectors[0]
