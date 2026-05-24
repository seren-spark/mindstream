"""ChromaDB 向量存储封装 — 与 SQLite chunks 表 1:1 映射。"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.chunk import Chunk
from app.models.knowledge_item import KnowledgeItem
from app.schemas.chunk import ChunkDraft, SourceLocation
from app.schemas.knowledge_item import KnowledgeItemStatus
from app.schemas.vector import (
    VectorMetadata,
    VectorQueryFilter,
    VectorSearchHit,
    VectorStatsResponse,
)
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
settings = get_settings()

COLLECTION_PREFIX = "kb_"


class VectorStoreService:
    @staticmethod
    def collection_name(knowledge_base_id: int) -> str:
        return f"{COLLECTION_PREFIX}{knowledge_base_id}"

    @staticmethod
    @lru_cache
    def _get_client() -> chromadb.PersistentClient:
        path = Path(settings.chroma_path)
        path.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(path=str(path))

    @classmethod
    def _get_collection(cls, knowledge_base_id: int, *, create: bool = True) -> Collection | None:
        client = cls._get_client()
        name = cls.collection_name(knowledge_base_id)
        if create:
            return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
        try:
            return client.get_collection(name=name)
        except Exception:
            return None

    @staticmethod
    def build_metadata(item: KnowledgeItem, draft: ChunkDraft) -> dict[str, Any]:
        loc: SourceLocation = draft.source_location
        meta = VectorMetadata(
            knowledge_base_id=draft.knowledge_base_id,
            knowledge_item_id=draft.knowledge_item_id,
            item_title=(item.title or "")[:200],
            order_index=draft.order_index,
            section_title=(loc.section_title or "")[:200],
            page_start=loc.page_start or 0,
            item_status=item.status,
            source_type=item.source_type,
            category=(item.category or "")[:50],
            tags_csv=",".join(item.tags or [])[:500],
        )
        return meta.model_dump()

    @staticmethod
    def _build_where_clause(
        filter_: VectorQueryFilter,
        item_ids: list[int] | None = None,
    ) -> dict[str, Any] | None:
        clauses: list[dict[str, Any]] = []

        if filter_.item_status:
            clauses.append({"item_status": filter_.item_status})
        if filter_.knowledge_item_id is not None:
            clauses.append({"knowledge_item_id": filter_.knowledge_item_id})
        if filter_.category:
            clauses.append({"category": filter_.category})
        if filter_.source_type:
            clauses.append({"source_type": filter_.source_type})

        merged_item_ids = item_ids
        if filter_.knowledge_item_ids:
            if merged_item_ids is None:
                merged_item_ids = filter_.knowledge_item_ids
            else:
                allowed = set(filter_.knowledge_item_ids)
                merged_item_ids = [i for i in merged_item_ids if i in allowed]

        if merged_item_ids is not None:
            if not merged_item_ids:
                return {"knowledge_item_id": -1}
            if len(merged_item_ids) == 1:
                clauses.append({"knowledge_item_id": merged_item_ids[0]})
            else:
                clauses.append({"knowledge_item_id": {"$in": merged_item_ids}})

        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    @staticmethod
    def _resolve_item_ids_by_tag(db: Session, knowledge_base_id: int, tag: str) -> list[int]:
        needle = tag.strip()
        if not needle:
            return []
        rows = (
            db.query(KnowledgeItem.id)
            .filter(KnowledgeItem.knowledge_base_id == knowledge_base_id)
            .filter(KnowledgeItem.tags.like(f'%"{needle}"%'))
            .all()
        )
        return [row[0] for row in rows]

    @classmethod
    def upsert_vectors(
        cls,
        item: KnowledgeItem,
        drafts: list[ChunkDraft],
        embeddings: list[list[float]],
    ) -> int:
        """写入预计算向量（不负责 embedding）。"""
        if not drafts:
            cls.delete_item_vectors(item.knowledge_base_id, item.id)
            return 0

        if len(drafts) != len(embeddings):
            raise ValueError(
                f"drafts/embeddings 数量不一致: {len(drafts)} vs {len(embeddings)}"
            )

        collection = cls._get_collection(item.knowledge_base_id)
        cls.delete_item_vectors(item.knowledge_base_id, item.id)

        ids = [d.chunk_id for d in drafts]
        documents = [d.content for d in drafts]
        metadatas = [cls.build_metadata(item, d) for d in drafts]

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        logger.info(
            "Upserted %s vectors for item %s in %s",
            len(ids),
            item.id,
            cls.collection_name(item.knowledge_base_id),
        )
        return len(ids)

    @classmethod
    def upsert_chunks(cls, item: KnowledgeItem, drafts: list[ChunkDraft]) -> int:
        """兼容旧接口：内部走 IndexingService（embed + upsert）。"""
        from app.services.indexing_service import IndexingService

        result = IndexingService.index_item(item, drafts)
        return result.vector_count

    @classmethod
    def sync_item_from_db(cls, db: Session, item: KnowledgeItem) -> int:
        from app.services.indexing_service import IndexingService

        result = IndexingService.index_item_from_db(db, item)
        return result.vector_count

    @classmethod
    def delete_item_vectors(cls, knowledge_base_id: int, knowledge_item_id: int) -> None:
        collection = cls._get_collection(knowledge_base_id, create=False)
        if collection is None:
            return
        try:
            collection.delete(where={"knowledge_item_id": knowledge_item_id})
        except Exception:
            logger.exception(
                "Failed to delete vectors for item %s in kb %s",
                knowledge_item_id,
                knowledge_base_id,
            )

    @classmethod
    def delete_knowledge_base_vectors(cls, knowledge_base_id: int) -> None:
        client = cls._get_client()
        name = cls.collection_name(knowledge_base_id)
        try:
            client.delete_collection(name=name)
        except Exception:
            logger.debug("Collection %s not found or already deleted", name)

    @classmethod
    def get_stats(cls, db: Session, knowledge_base_id: int) -> VectorStatsResponse:
        collection = cls._get_collection(knowledge_base_id, create=False)
        vector_count = collection.count() if collection is not None else 0
        chunk_count = (
            db.query(Chunk)
            .filter(Chunk.knowledge_base_id == knowledge_base_id)
            .join(KnowledgeItem, KnowledgeItem.id == Chunk.knowledge_item_id)
            .filter(KnowledgeItem.status == KnowledgeItemStatus.READY.value)
            .count()
        )
        return VectorStatsResponse(
            knowledge_base_id=knowledge_base_id,
            collection_name=cls.collection_name(knowledge_base_id),
            vector_count=vector_count,
            chunk_count_sqlite=chunk_count,
            in_sync=vector_count == chunk_count,
        )

    @classmethod
    def query(
        cls,
        db: Session,
        knowledge_base_id: int,
        query_text: str,
        *,
        filter_: VectorQueryFilter | None = None,
        top_k: int | None = None,
    ) -> list[VectorSearchHit]:
        collection = cls._get_collection(knowledge_base_id, create=False)
        if collection is None or collection.count() == 0:
            return []

        filt = filter_ or VectorQueryFilter()
        item_ids: list[int] | None = None
        if filt.tag:
            item_ids = cls._resolve_item_ids_by_tag(db, knowledge_base_id, filt.tag)
            if not item_ids:
                return []

        where = cls._build_where_clause(filt, item_ids)
        query_embedding = EmbeddingService.embed_query(query_text)
        n_results = top_k or settings.vector_search_top_k

        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        hits: list[VectorSearchHit] = []
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for chunk_id, doc, meta, dist in zip(ids, documents, metadatas, distances, strict=False):
            if not meta:
                continue
            metadata = VectorMetadata.model_validate(meta)
            score = 1.0 - float(dist) if dist is not None else 0.0
            hits.append(
                VectorSearchHit(
                    chunk_id=chunk_id,
                    knowledge_item_id=metadata.knowledge_item_id,
                    item_title=metadata.item_title,
                    content=doc or "",
                    score=round(score, 4),
                    metadata=metadata,
                    order_index=metadata.order_index,
                    section_title=metadata.section_title,
                    page_start=metadata.page_start,
                )
            )
        return hits

    @classmethod
    def rebuild_knowledge_base(cls, db: Session, knowledge_base_id: int) -> tuple[int, int]:
        cls.delete_knowledge_base_vectors(knowledge_base_id)

        items = (
            db.query(KnowledgeItem)
            .filter(KnowledgeItem.knowledge_base_id == knowledge_base_id)
            .filter(KnowledgeItem.status == KnowledgeItemStatus.READY.value)
            .all()
        )

        total_vectors = 0
        for item in items:
            total_vectors += cls.sync_item_from_db(db, item)

        return total_vectors, len(items)
