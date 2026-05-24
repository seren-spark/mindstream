from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.knowledge_base import KnowledgeBaseStatus
from app.schemas.vector import (
    VectorRebuildResponse,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorStatsResponse,
)
from app.services.knowledge_base_service import KnowledgeBaseNotFoundError, KnowledgeBaseService
from app.services.vector_store_service import VectorStoreService

router = APIRouter(prefix="/knowledge-bases", tags=["vectors"])


@router.get("/{knowledge_base_id}/vectors/stats", response_model=VectorStatsResponse)
def get_vector_stats(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
) -> VectorStatsResponse:
    try:
        kb = KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if kb.status == KnowledgeBaseStatus.DISABLED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="知识库已禁用")

    return VectorStoreService.get_stats(db, knowledge_base_id)


@router.post("/{knowledge_base_id}/vectors/rebuild", response_model=VectorRebuildResponse)
def rebuild_vectors(
    knowledge_base_id: int,
    db: Session = Depends(get_db),
) -> VectorRebuildResponse:
    try:
        KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    vector_count, item_count = VectorStoreService.rebuild_knowledge_base(db, knowledge_base_id)
    return VectorRebuildResponse(
        knowledge_base_id=knowledge_base_id,
        vector_count=vector_count,
        item_count=item_count,
        message=f"已重建 {item_count} 个条目的 {vector_count} 条向量",
    )


@router.post("/{knowledge_base_id}/vectors/search", response_model=VectorSearchResponse)
def search_vectors(
    knowledge_base_id: int,
    payload: VectorSearchRequest,
    db: Session = Depends(get_db),
) -> VectorSearchResponse:
    try:
        kb = KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if kb.status == KnowledgeBaseStatus.DISABLED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="知识库已禁用")

    hits = VectorStoreService.query(
        db,
        knowledge_base_id,
        payload.query,
        filter_=payload.filter,
        top_k=payload.top_k,
    )
    return VectorSearchResponse(query=payload.query, hits=hits, total=len(hits))
