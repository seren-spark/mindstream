from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Knowledge Base"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = "sqlite:///./data/app.db"
    chroma_path: str = "./data/chroma"
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 20
    allowed_upload_extensions: str = ".pdf,.docx,.doc,.md,.markdown,.txt"

    chunk_size: int = 400
    chunk_overlap: int = 60
    chunk_min_size: int = 80

    embedding_mode: str = "hash"
    vector_search_top_k: int = 5
    embedding_batch_size: int = 32
    embedding_max_retries: int = 3
    embedding_retry_base_delay: float = 1.0
    embedding_cache_enabled: bool = True
    embedding_cache_path: str = "./data/embedding_cache.json"

    hybrid_recall_top_k: int = 20
    hybrid_final_top_k: int = 5
    rrf_k: int = 60

    rag_max_history_turns: int = 3
    rag_max_context_chars: int = 6000
    rag_chunk_max_chars: int = 800

    llm_mode: str = "mock"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    llm_stream_delay_ms: float = 25.0
    llm_stream_chunk_chars: int = 2

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_extension_set(self) -> set[str]:
        return {
            ext.strip().lower()
            for ext in self.allowed_upload_extensions.split(",")
            if ext.strip()
        }

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
