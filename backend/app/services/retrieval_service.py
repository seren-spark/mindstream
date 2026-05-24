"""混合检索服务 — 向量 + 关键词双路召回，RRF 融合。"""

from __future__ import annotations

import logging
import re
from collections import defaultdict

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.chunk import Chunk
from app.models.knowledge_item import KnowledgeItem
from app.schemas.chunk import SourceLocation
from app.schemas.knowledge_item import KnowledgeItemStatus
from app.schemas.retrieval import HybridSearchResponse, RetrievalHit
from app.schemas.vector import VectorQueryFilter, VectorSearchHit
from app.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)
settings = get_settings()

TERM_SPLIT_PATTERN = re.compile(r"[\s,，。；;、!?！？]+")


def split_query_terms(query: str) -> list[str]:
    """切分 query 为检索词；中文短 query 保留整句。"""
    stripped = query.strip()
    if not stripped:
        return []
    terms = [t for t in TERM_SPLIT_PATTERN.split(stripped) if len(t) >= 2]
    if not terms:
        return [stripped]
    if stripped not in terms:
        terms.insert(0, stripped)
    return terms


def rrf_fuse(
    ranked_lists: dict[str, list[str]],
    *,
    k: int | None = None,
) -> list[tuple[str, float]]:
    """
    Reciprocal Rank Fusion。
    ranked_lists: {"vector": [chunk_id...], "keyword": [chunk_id...]}
    返回 [(chunk_id, rrf_score)] 降序。
    """
    rrf_k = k if k is not None else settings.rrf_k
    scores: dict[str, float] = defaultdict(float)
    for ids in ranked_lists.values():
        for rank, chunk_id in enumerate(ids, start=1):
            scores[chunk_id] += 1.0 / (rrf_k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def build_highlight(content: str, query: str, *, window: int = 80) -> str:
    """截取 query 附近文本供前端展示。"""
    if not content:
        return ""
    lowered = content.lower()
    needle = query.strip().lower()
    idx = lowered.find(needle) if needle else -1
    if idx < 0:
        for term in split_query_terms(query):
            idx = lowered.find(term.lower())
            if idx >= 0:
                break
    if idx < 0:
        return content[: window * 2] + ("..." if len(content) > window * 2 else "")
    start = max(0, idx - window)
    end = min(len(content), idx + len(needle or query) + window)
    snippet = content[start:end]
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(content) else ""
    return f"{prefix}{snippet}{suffix}"


def build_display_title(item_title: str, source_location: SourceLocation) -> str:
    if source_location.heading_path:
        return f"{item_title} › {' › '.join(source_location.heading_path)}"
    if source_location.section_title:
        return f"{item_title} › {source_location.section_title}"
    if source_location.page_start:
        return f"{item_title} › 第 {source_location.page_start} 页"
    return item_title


class RetrievalService:
    @staticmethod
    def _apply_item_filters(
        query,
        knowledge_base_id: int,
        filter_: VectorQueryFilter,
    ):
        query = query.filter(Chunk.knowledge_base_id == knowledge_base_id)
        query = query.filter(KnowledgeItem.status == KnowledgeItemStatus.READY.value)

        if filter_.item_status and filter_.item_status != KnowledgeItemStatus.READY.value:
            query = query.filter(KnowledgeItem.status == filter_.item_status)

        if filter_.knowledge_item_id is not None:
            query = query.filter(Chunk.knowledge_item_id == filter_.knowledge_item_id)
        if filter_.knowledge_item_ids:
            query = query.filter(Chunk.knowledge_item_id.in_(filter_.knowledge_item_ids))
        if filter_.category:
            query = query.filter(KnowledgeItem.category == filter_.category)
        if filter_.source_type:
            query = query.filter(KnowledgeItem.source_type == filter_.source_type)
        return query

    @classmethod
    def keyword_recall(
        cls,
        db: Session,
        knowledge_base_id: int,
        query_text: str,
        *,
        filter_: VectorQueryFilter | None = None,
        recall_k: int | None = None,
    ) -> list[tuple[str, float]]:
        """
        关键词召回。返回 [(chunk_id, keyword_score)]，score 为归一化 rank 分。
        """
        limit = recall_k or settings.hybrid_recall_top_k
        filt = filter_ or VectorQueryFilter()

        if filt.tag:
            item_ids = VectorStoreService._resolve_item_ids_by_tag(db, knowledge_base_id, filt.tag)
            if not item_ids:
                return []
            filt = filt.model_copy(update={"knowledge_item_ids": item_ids})

        base = (
            db.query(Chunk, KnowledgeItem)
            .join(KnowledgeItem, KnowledgeItem.id == Chunk.knowledge_item_id)
        )
        base = cls._apply_item_filters(base, knowledge_base_id, filt)

        terms = split_query_terms(query_text)
        phrase = query_text.strip()

        # 整句优先
        rows = (
            base.filter(Chunk.content.ilike(f"%{phrase}%"))
            .order_by(Chunk.order_index.asc())
            .limit(limit * 3)
            .all()
        )

        # 整句无结果时，任一词命中（OR）
        if not rows and len(terms) > 1:
            clauses = [Chunk.content.ilike(f"%{term}%") for term in terms]
            rows = base.filter(or_(*clauses)).limit(limit * 3).all()

        if not rows:
            return []

        # 按命中词数 + 词频粗排
        scored: list[tuple[str, float, Chunk, KnowledgeItem]] = []
        for chunk, item in rows:
            content_lower = chunk.content.lower()
            hit_count = sum(1 for t in terms if t.lower() in content_lower)
            freq = sum(content_lower.count(t.lower()) for t in terms)
            kw_score = hit_count * 10 + freq
            scored.append((chunk.id, float(kw_score), chunk, item))

        scored.sort(key=lambda x: x[1], reverse=True)
        seen: set[str] = set()
        result: list[tuple[str, float]] = []
        for chunk_id, kw_score, _, _ in scored:
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            result.append((chunk_id, kw_score))
            if len(result) >= limit:
                break

        # 归一化 score 到 0~1
        if result:
            max_score = result[0][1] or 1.0
            result = [(cid, round(s / max_score, 4)) for cid, s in result]
        return result

    @classmethod
    def vector_recall(
        cls,
        db: Session,
        knowledge_base_id: int,
        query_text: str,
        *,
        filter_: VectorQueryFilter | None = None,
        recall_k: int | None = None,
    ) -> list[VectorSearchHit]:
        limit = recall_k or settings.hybrid_recall_top_k
        return VectorStoreService.query(
            db,
            knowledge_base_id,
            query_text,
            filter_=filter_ or VectorQueryFilter(),
            top_k=limit,
        )

    @classmethod
    def _load_chunks_map(
        cls,
        db: Session,
        chunk_ids: list[str],
    ) -> dict[str, tuple[Chunk, KnowledgeItem]]:
        if not chunk_ids:
            return {}
        rows = (
            db.query(Chunk, KnowledgeItem)
            .join(KnowledgeItem, KnowledgeItem.id == Chunk.knowledge_item_id)
            .filter(Chunk.id.in_(chunk_ids))
            .all()
        )
        return {chunk.id: (chunk, item) for chunk, item in rows}

    @classmethod
    def hybrid_search(
        cls,
        db: Session,
        knowledge_base_id: int,
        query_text: str,
        *,
        top_k: int | None = None,
        recall_k: int | None = None,
        filter_: VectorQueryFilter | None = None,
    ) -> HybridSearchResponse:
        """混合检索主入口。"""
        final_k = top_k or settings.hybrid_final_top_k
        recall = recall_k or settings.hybrid_recall_top_k
        filt = filter_ or VectorQueryFilter()

        vector_hits = cls.vector_recall(
            db, knowledge_base_id, query_text, filter_=filt, recall_k=recall
        )
        keyword_hits = cls.keyword_recall(
            db, knowledge_base_id, query_text, filter_=filt, recall_k=recall
        )

        vector_ids = [h.chunk_id for h in vector_hits]
        keyword_ids = [cid for cid, _ in keyword_hits]

        fused = rrf_fuse({"vector": vector_ids, "keyword": keyword_ids})

        vector_score_map = {h.chunk_id: h.score for h in vector_hits}
        keyword_score_map = dict(keyword_hits)

        chunk_ids = [cid for cid, _ in fused[: final_k * 2]]
        chunks_map = cls._load_chunks_map(db, chunk_ids)

        hits: list[RetrievalHit] = []
        for chunk_id, rrf_score in fused:
            if chunk_id not in chunks_map:
                continue
            chunk, item = chunks_map[chunk_id]
            loc = SourceLocation.model_validate(chunk.source_location)
            sources: list[str] = []
            if chunk_id in vector_score_map:
                sources.append("vector")
            if chunk_id in keyword_score_map:
                sources.append("keyword")

            hits.append(
                RetrievalHit(
                    chunk_id=chunk_id,
                    content=chunk.content,
                    score=round(rrf_score, 6),
                    source_name=item.title,
                    display_title=build_display_title(item.title, loc),
                    source_location=loc,
                    knowledge_item_id=item.id,
                    knowledge_base_id=chunk.knowledge_base_id,
                    highlight_text=build_highlight(chunk.content, query_text),
                    order_index=chunk.order_index,
                    recall_sources=sources,
                    vector_score=vector_score_map.get(chunk_id),
                    keyword_score=keyword_score_map.get(chunk_id),
                )
            )
            if len(hits) >= final_k:
                break

        logger.info(
            "Hybrid search kb=%s query=%r vector=%s keyword=%s fused=%s",
            knowledge_base_id,
            query_text[:50],
            len(vector_hits),
            len(keyword_hits),
            len(hits),
        )
        return HybridSearchResponse(
            query=query_text,
            hits=hits,
            total=len(hits),
            vector_recall_count=len(vector_hits),
            keyword_recall_count=len(keyword_hits),
        )

    @classmethod
    def build_rag_context(cls, hits: list[RetrievalHit]) -> str:
        """将检索结果格式化为 RAG prompt context。"""
        if not hits:
            return ""
        blocks: list[str] = []
        for i, hit in enumerate(hits, start=1):
            blocks.append(
                f"[{i}] 来源：{hit.display_title}\n{hit.content}"
            )
        return "\n\n".join(blocks)
