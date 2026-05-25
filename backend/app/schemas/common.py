from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.api_contract import ApiErrorCode

T = TypeVar("T")


class PingResponse(BaseModel):
    status: str
    message: str
    version: str = "0.1.0"


class ValidationErrorItem(BaseModel):
    """422 字段级错误，与 FastAPI RequestValidationError 对齐。"""

    loc: list[str | int]
    msg: str
    type: str


class ErrorResponse(BaseModel):
    """统一错误体 — 所有非 2xx JSON 响应均为此结构。"""

    detail: str
    code: ApiErrorCode | str | None = None
    errors: list[ValidationErrorItem] | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """统一分页列表 — 成功时 HTTP 200，body 即此结构（无外层包装）。"""

    items: list[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class PaginationParams(BaseModel):
    """列表接口通用 query 参数基类。"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class MessageResponse(BaseModel):
    """简单操作反馈（可选，用于无需返回实体的 POST）。"""

    message: str


def build_error_content(
    detail: str,
    *,
    code: ApiErrorCode | str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"detail": detail}
    if code is not None:
        payload["code"] = code.value if isinstance(code, ApiErrorCode) else code
    if errors:
        payload["errors"] = errors
    return payload
