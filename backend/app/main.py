from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.knowledge_base import router as knowledge_base_router
from app.api.ping import router as ping_router
from app.core.config import get_settings
from app.core.database import init_db
from app.schemas.common import ErrorResponse


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
    if isinstance(exc.detail, str):
        content = ErrorResponse(detail=exc.detail).model_dump()
    else:
        content = ErrorResponse(detail="Request failed", code=str(exc.status_code)).model_dump()
    return JSONResponse(status_code=exc.status_code, content=content)


app.include_router(ping_router, prefix="/api")
app.include_router(knowledge_base_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "AI Knowledge Base API", "docs": "/docs"}
