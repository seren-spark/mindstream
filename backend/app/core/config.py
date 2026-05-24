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
