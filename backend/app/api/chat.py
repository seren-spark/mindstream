from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chat import ChatStreamRequest
from app.services.chat_service import ChatService

router = APIRouter(prefix="/knowledge-bases", tags=["chat"])


@router.post("/{knowledge_base_id}/chat/stream")
async def stream_chat(
    knowledge_base_id: int,
    payload: ChatStreamRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """SSE 流式 RAG 问答。事件类型：start / token / references / done / error。"""

    async def event_generator():
        async for chunk in ChatService.stream_chat(db, knowledge_base_id, payload):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
