from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.schemas.knowledge_item import (
    ALLOWED_STATUS_TRANSITIONS,
    KnowledgeItemCreate,
    KnowledgeItemSourceType,
    KnowledgeItemStatus,
    KnowledgeItemStatusUpdate,
    KnowledgeItemUpdate,
)
from app.schemas.parse import ParseResult
from app.services.chunk_service import ChunkService
from app.services.knowledge_base_service import KnowledgeBaseNotFoundError, KnowledgeBaseService


class KnowledgeItemNotFoundError(Exception):
    def __init__(self, item_id: int) -> None:
        self.item_id = item_id
        super().__init__(f"Knowledge item {item_id} not found")


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition from '{current}' to '{target}'")


class KnowledgeItemService:
    @staticmethod
    def list_items(
        db: Session,
        knowledge_base_id: int,
        *,
        keyword: str | None = None,
        status: str | None = None,
        source_type: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        sort: str = "updated_at_desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[KnowledgeItem], int]:
        KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)

        query = db.query(KnowledgeItem).filter(
            KnowledgeItem.knowledge_base_id == knowledge_base_id
        )

        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(
                (KnowledgeItem.title.ilike(like))
                | (KnowledgeItem.summary.ilike(like))
                | (KnowledgeItem.content.ilike(like))
            )

        if status:
            query = query.filter(KnowledgeItem.status == status)

        if source_type:
            query = query.filter(KnowledgeItem.source_type == source_type)

        if category:
            query = query.filter(KnowledgeItem.category == category.strip())

        if tag:
            query = query.filter(KnowledgeItem.tags.like(f'%"{tag.strip()}"%'))

        if sort == "created_at_asc":
            query = query.order_by(KnowledgeItem.created_at.asc())
        elif sort == "title_asc":
            query = query.order_by(KnowledgeItem.title.asc())
        else:
            query = query.order_by(KnowledgeItem.updated_at.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    @staticmethod
    def get_item(db: Session, item_id: int) -> KnowledgeItem:
        item = db.get(KnowledgeItem, item_id)
        if item is None:
            raise KnowledgeItemNotFoundError(item_id)
        return item

    @staticmethod
    def _resolve_initial_status(payload: KnowledgeItemCreate) -> str:
        if payload.source_type == KnowledgeItemSourceType.FILE:
            return KnowledgeItemStatus.PENDING.value
        if payload.content and payload.content.strip():
            return KnowledgeItemStatus.READY.value
        return KnowledgeItemStatus.PENDING.value

    @staticmethod
    def _finalize_ready(
        db: Session,
        item: KnowledgeItem,
        *,
        parse_result: ParseResult | None = None,
    ) -> None:
        if item.content and not item.summary:
            item.summary = item.content.strip()[:200]
        item.processing_progress = 100
        item.error_message = None
        if item.content and item.content.strip():
            ChunkService.apply_to_item(db, item, parse_result)
        else:
            item.chunk_count = 0

    @staticmethod
    def create_item(
        db: Session,
        knowledge_base_id: int,
        payload: KnowledgeItemCreate,
    ) -> KnowledgeItem:
        try:
            KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
        except KnowledgeBaseNotFoundError as exc:
            raise exc

        initial_status = KnowledgeItemService._resolve_initial_status(payload)
        item = KnowledgeItem(
            knowledge_base_id=knowledge_base_id,
            title=payload.title.strip(),
            source_type=payload.source_type.value,
            status=initial_status,
            content=payload.content.strip() if payload.content else None,
            summary=payload.summary.strip() if payload.summary else None,
            file_name=payload.file_name.strip() if payload.file_name else None,
            file_type=payload.file_type,
            category=payload.category.strip() if payload.category else None,
            tags=payload.tags,
        )

        if initial_status == KnowledgeItemStatus.READY.value:
            db.add(item)
            db.flush()
            KnowledgeItemService._finalize_ready(db, item)
            db.commit()
            db.refresh(item)
            return item

        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update_item(
        db: Session,
        item_id: int,
        payload: KnowledgeItemUpdate,
    ) -> KnowledgeItem:
        item = KnowledgeItemService.get_item(db, item_id)
        data = payload.model_dump(exclude_unset=True)

        if "title" in data and data["title"] is not None:
            item.title = data["title"].strip()
        if "content" in data:
            item.content = data["content"].strip() if data["content"] else None
        if "summary" in data:
            item.summary = data["summary"].strip() if data["summary"] else None
        if "category" in data:
            item.category = data["category"].strip() if data["category"] else None
        if "tags" in data and data["tags"] is not None:
            item.tags = data["tags"]
        if "status" in data and data["status"] is not None:
            KnowledgeItemService._transition_status(
                db,
                item,
                data["status"],
                error_message=None,
            )

        if item.status == KnowledgeItemStatus.READY.value and "content" in data and item.content:
            KnowledgeItemService._finalize_ready(db, item)

        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete_item(db: Session, item_id: int) -> None:
        item = KnowledgeItemService.get_item(db, item_id)
        db.delete(item)
        db.commit()

    @staticmethod
    def _transition_status(
        db: Session,
        item: KnowledgeItem,
        target: KnowledgeItemStatus,
        *,
        error_message: str | None = None,
    ) -> None:
        current = KnowledgeItemStatus(item.status)
        allowed = ALLOWED_STATUS_TRANSITIONS.get(current, set())
        if target not in allowed and current != target:
            raise InvalidStatusTransitionError(current.value, target.value)

        item.status = target.value
        if target == KnowledgeItemStatus.FAILED:
            item.error_message = error_message or "处理失败"
            item.processing_progress = 0
        elif target == KnowledgeItemStatus.PROCESSING:
            item.processing_progress = 10
            item.error_message = None
        elif target == KnowledgeItemStatus.READY:
            item.processing_progress = 100
            item.error_message = None
        elif target == KnowledgeItemStatus.PENDING:
            item.processing_progress = 0
            item.error_message = None

    @staticmethod
    def update_status(
        db: Session,
        item_id: int,
        payload: KnowledgeItemStatusUpdate,
    ) -> KnowledgeItem:
        item = KnowledgeItemService.get_item(db, item_id)
        KnowledgeItemService._transition_status(
            db,
            item,
            payload.status,
            error_message=payload.error_message,
        )
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def parse_item(db: Session, item_id: int) -> KnowledgeItem:
        """Parse uploaded file and update item content/status."""
        from app.services.parser_service import ParserService

        item = KnowledgeItemService.get_item(db, item_id)

        if item.source_type != KnowledgeItemSourceType.FILE.value or not item.file_path:
            raise InvalidStatusTransitionError(item.status, KnowledgeItemStatus.PROCESSING.value)

        if item.status not in {
            KnowledgeItemStatus.PENDING.value,
            KnowledgeItemStatus.FAILED.value,
        }:
            raise InvalidStatusTransitionError(item.status, KnowledgeItemStatus.PROCESSING.value)

        ParserService.apply_to_item(db, item)
        db.refresh(item)
        return item

    @staticmethod
    def trigger_process(db: Session, item_id: int) -> KnowledgeItem:
        """Run parse pipeline for file imports, or mark manual entries ready when content exists."""
        item = KnowledgeItemService.get_item(db, item_id)

        if item.status not in {
            KnowledgeItemStatus.PENDING.value,
            KnowledgeItemStatus.FAILED.value,
        }:
            raise InvalidStatusTransitionError(item.status, KnowledgeItemStatus.PROCESSING.value)

        if item.source_type == KnowledgeItemSourceType.FILE.value and item.file_path:
            return KnowledgeItemService.parse_item(db, item_id)

        item.status = KnowledgeItemStatus.PROCESSING.value
        item.processing_progress = 50
        item.error_message = None
        db.commit()

        if item.content:
            item.status = KnowledgeItemStatus.READY.value
            KnowledgeItemService._finalize_ready(db, item)
        else:
            item.status = KnowledgeItemStatus.FAILED.value
            item.error_message = "条目无正文，请先录入内容或上传文档"

        db.commit()
        db.refresh(item)
        return item
