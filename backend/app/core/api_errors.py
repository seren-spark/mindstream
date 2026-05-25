"""API 异常辅助 — 统一抛出带 code 的 HTTPException。"""

from fastapi import HTTPException, status

from app.core.api_contract import ApiErrorCode
from app.schemas.common import build_error_content


def api_error(
    status_code: int,
    detail: str,
    *,
    code: ApiErrorCode | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=build_error_content(detail, code=code or _default_code(status_code)),
    )


def _default_code(status_code: int) -> ApiErrorCode:
    if status_code == status.HTTP_404_NOT_FOUND:
        return ApiErrorCode.NOT_FOUND
    if status_code == status.HTTP_409_CONFLICT:
        return ApiErrorCode.CONFLICT
    if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return ApiErrorCode.VALIDATION_ERROR
    return ApiErrorCode.INTERNAL_ERROR


def not_found(detail: str) -> HTTPException:
    return api_error(status.HTTP_404_NOT_FOUND, detail, code=ApiErrorCode.NOT_FOUND)


def conflict(detail: str) -> HTTPException:
    return api_error(status.HTTP_409_CONFLICT, detail, code=ApiErrorCode.CONFLICT)


def bad_request(detail: str, *, code: ApiErrorCode = ApiErrorCode.VALIDATION_ERROR) -> HTTPException:
    return api_error(status.HTTP_400_BAD_REQUEST, detail, code=code)
