import mimetypes
import re
import uuid
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()

INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class FileValidationError(Exception):
    def __init__(self, message: str, code: str = "invalid_file") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip()
    name = INVALID_FILENAME_CHARS.sub("_", name)
    return name or "unnamed_file"


def get_file_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return suffix.lstrip(".")


def validate_upload_file(filename: str, size: int, content_type: str | None) -> tuple[str, str]:
    safe_name = sanitize_filename(filename)
    extension = Path(safe_name).suffix.lower()

    if extension not in settings.allowed_extension_set:
        allowed = ", ".join(sorted(settings.allowed_extension_set))
        raise FileValidationError(
            f"不支持的文件格式「{extension or '未知'}」，仅支持：{allowed}",
            code="unsupported_format",
        )

    if size <= 0:
        raise FileValidationError("文件为空，无法上传", code="empty_file")

    if size > settings.max_upload_size_bytes:
        raise FileValidationError(
            f"文件大小超过限制（最大 {settings.max_upload_size_mb} MB）",
            code="file_too_large",
        )

    mime_type = content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    file_type = get_file_extension(safe_name)
    return mime_type, file_type


def build_stored_filename(original_filename: str) -> str:
    safe_name = sanitize_filename(original_filename)
    return f"{uuid.uuid4().hex[:12]}_{safe_name}"


def build_upload_path(knowledge_base_id: int, stored_filename: str) -> Path:
    return Path(settings.upload_dir) / str(knowledge_base_id) / stored_filename
