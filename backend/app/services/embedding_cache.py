"""Embedding 向量本地缓存 — text_hash + model 为键。"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


class EmbeddingCacheStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(settings.embedding_cache_path)
        self._lock = threading.Lock()
        self._data: dict[str, list[float]] = {}
        self._load()

    def _cache_key(self, model_name: str, text_hash: str) -> str:
        return f"{model_name}:{text_hash}"

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._data = {k: v for k, v in raw.items() if isinstance(v, list)}
        except (json.JSONDecodeError, OSError):
            self._data = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, ensure_ascii=False),
            encoding="utf-8",
        )

    def get(self, model_name: str, text_hash: str) -> list[float] | None:
        key = self._cache_key(model_name, text_hash)
        with self._lock:
            return self._data.get(key)

    def set(self, model_name: str, text_hash: str, vector: list[float]) -> None:
        key = self._cache_key(model_name, text_hash)
        with self._lock:
            self._data[key] = vector
            if settings.embedding_cache_enabled:
                self._save()

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            if self._path.exists():
                self._path.unlink(missing_ok=True)


_cache_instance: EmbeddingCacheStore | None = None


def get_embedding_cache() -> EmbeddingCacheStore:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = EmbeddingCacheStore()
    return _cache_instance
