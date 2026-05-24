"""索引编排服务 — 向量化 + 向量库写入 pipeline。"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.schemas.chunk import ChunkDraft, ChunkMetadata, SourceLocation
from app.schemas.embedding import IndexingResult
from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingPipelineError, EmbeddingService
from app.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


class IndexingService:
    @staticmethod
    def index_item(
        item: KnowledgeItem,
        drafts: list[ChunkDraft],
        *,
        progress_callback=None,
    ) -> IndexingResult:
        """
        对条目 chunks 执行向量化并写入 ChromaDB。
        progress_callback(percent: int) 可选，用于更新 processing_progress。
        """
        if not drafts:
            VectorStoreService.delete_item_vectors(item.knowledge_base_id, item.id)
            return IndexingResult(
                vector_count=0,
                embedding=EmbeddingService.embed_chunks([]),
            )

        if progress_callback:
            progress_callback(70)

        inputs = EmbeddingService.build_inputs(drafts, knowledge_item_id=item.id)
        batch_result = EmbeddingService.embed_chunks(inputs)

        if progress_callback:
            progress_callback(85)

        record_map = {r.chunk_id: r.vector for r in batch_result.records}
        embeddings = [record_map[d.chunk_id] for d in sorted(drafts, key=lambda x: x.order_index)]

        count = VectorStoreService.upsert_vectors(item, drafts, embeddings)

        logger.info(
            "Indexed item %s: %s vectors (cache_hits=%s, api_calls=%s)",
            item.id,
            count,
            batch_result.cache_hits,
            batch_result.api_calls,
        )
        return IndexingResult(vector_count=count, embedding=batch_result)

    @staticmethod
    def index_item_from_db(db: Session, item: KnowledgeItem) -> IndexingResult:
        """从 SQLite 已有 chunks 重建向量索引。"""
        rows = ChunkService.list_chunks(db, item.id)
        if not rows:
            VectorStoreService.delete_item_vectors(item.knowledge_base_id, item.id)
            return IndexingResult(
                vector_count=0,
                embedding=EmbeddingService.embed_chunks([]),
            )

        drafts = [
            ChunkDraft(
                chunk_id=row.id,
                knowledge_item_id=row.knowledge_item_id,
                knowledge_base_id=row.knowledge_base_id,
                content=row.content,
                order_index=row.order_index,
                token_count=row.token_count,
                source_location=SourceLocation.model_validate(row.source_location),
                metadata=ChunkMetadata.model_validate(row.chunk_metadata),
            )
            for row in rows
        ]
        return IndexingService.index_item(item, drafts)

    @staticmethod
    def safe_index_item(
        db: Session,
        item: KnowledgeItem,
        drafts: list[ChunkDraft],
    ) -> IndexingResult:
        """向量化并写入；失败时清理向量、更新条目为 failed，抛出 EmbeddingPipelineError。"""
        from app.schemas.knowledge_item import KnowledgeItemStatus

        try:
            item.processing_progress = 60
            db.flush()

            def on_progress(p: int) -> None:
                item.processing_progress = p
                db.flush()

            result = IndexingService.index_item(item, drafts, progress_callback=on_progress)
            item.processing_progress = 100
            item.error_message = None
            return result
        except EmbeddingPipelineError as exc:
            VectorStoreService.delete_item_vectors(item.knowledge_base_id, item.id)
            item.status = KnowledgeItemStatus.FAILED.value
            item.error_message = str(exc)
            item.processing_progress = 0
            db.flush()
            raise
