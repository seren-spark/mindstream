from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.unanswered import router as unanswered_router
from app.api.stats import router as stats_router
from app.api.agent import router as agent_router
from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from app.api.knowledge_base import router as knowledge_base_router
from app.api.knowledge_item import router as knowledge_item_router
from app.api.ping import router as ping_router
from app.api.prompt import router as prompt_router
from app.api.retrieval import router as retrieval_router
from app.api.upload import router as upload_router
from app.api.vector import router as vector_router
from app.core.api_contract import OPENAPI_TAGS, ApiErrorCode
from app.core.config import get_settings
from app.core.database import init_db
from app.schemas.common import ErrorResponse, ValidationErrorItem, build_error_content


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    description=(
        "AI 知识库管理平台 REST API。\n\n"
        "**契约约定**：成功响应直接返回业务 JSON；"
        "列表接口返回 `{ items, total, page, page_size }`；"
        "错误返回 `{ detail, code?, errors? }`；"
        "流式问答使用 `POST .../chat/stream`，Content-Type 为 `text/event-stream`。"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        content = exc.detail
    elif isinstance(exc.detail, str):
        content = build_error_content(exc.detail)
    else:
        content = build_error_content("Request failed", code=str(exc.status_code))
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        ValidationErrorItem(loc=list(err.get("loc", [])), msg=err.get("msg", ""), type=err.get("type", ""))
        for err in exc.errors()
    ]
    content = ErrorResponse(
        detail="请求参数校验失败",
        code=ApiErrorCode.VALIDATION_ERROR,
        errors=errors,
    ).model_dump()
    return JSONResponse(status_code=422, content=content)


app.include_router(ping_router, prefix="/api")
app.include_router(knowledge_base_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(conversation_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(unanswered_router, prefix="/api")
app.include_router(knowledge_item_router, prefix="/api")
app.include_router(prompt_router, prefix="/api")
app.include_router(retrieval_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(vector_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "AI Knowledge Base API", "docs": "/docs"}
