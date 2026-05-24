from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.knowledge_base import KnowledgeBaseStatus
from app.schemas.retrieval import HybridSearchRequest, HybridSearchResponse
from app.services.knowledge_base_service import KnowledgeBaseNotFoundError, KnowledgeBaseService
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/knowledge-bases", tags=["retrieval"])


@router.post("/{knowledge_base_id}/search", response_model=HybridSearchResponse)
def hybrid_search(
    knowledge_base_id: int,
    payload: HybridSearchRequest,
    db: Session = Depends(get_db),
) -> HybridSearchResponse:
    """混合检索：向量 + 关键词，RRF 融合后返回 top_k。"""
    try:
        kb = KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if kb.status == KnowledgeBaseStatus.DISABLED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="知识库已禁用")

    return RetrievalService.hybrid_search(
        db,
        knowledge_base_id,
        payload.query,
        top_k=payload.top_k,
        recall_k=payload.recall_k,
        filter_=payload.filter,
    )
