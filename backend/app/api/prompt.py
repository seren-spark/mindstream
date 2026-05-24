from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.knowledge_base import KnowledgeBaseStatus
from app.schemas.prompt import PromptBuildRequest, PromptBuildResult
from app.services.knowledge_base_service import KnowledgeBaseNotFoundError, KnowledgeBaseService
from app.services.prompt_builder_service import PromptBuilderService
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/knowledge-bases", tags=["prompt"])


@router.post("/{knowledge_base_id}/prompt/build", response_model=PromptBuildResult)
def build_rag_prompt(
    knowledge_base_id: int,
    payload: PromptBuildRequest,
    db: Session = Depends(get_db),
) -> PromptBuildResult:
    """组装 RAG Prompt（检索 + 模板），不调用 LLM，供调试与后续 chat 模块消费。"""
    try:
        kb = KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if kb.status == KnowledgeBaseStatus.DISABLED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="知识库已禁用")

    if payload.hits:
        hits = payload.hits
    else:
        search = RetrievalService.hybrid_search(
            db,
            knowledge_base_id,
            payload.query,
            top_k=payload.top_k,
            recall_k=payload.recall_k,
            filter_=payload.filter,
        )
        hits = search.hits

    return PromptBuilderService.build(
        payload.model_copy(
            update={
                "hits": hits,
                "knowledge_base_name": kb.name,
            }
        )
    )
