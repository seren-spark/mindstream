from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.services.vector_store_service import VectorStoreService


class KnowledgeBaseNotFoundError(Exception):
    def __init__(self, knowledge_base_id: int) -> None:
        self.knowledge_base_id = knowledge_base_id
        super().__init__(f"Knowledge base {knowledge_base_id} not found")


class KnowledgeBaseService:
    @staticmethod
    def list_knowledge_bases(
        db: Session,
        *,
        keyword: str | None = None,
        status: str | None = None,
        sort: str = "created_at_desc",
        page: int = 1,
        page_size: int = 12,
    ) -> tuple[list[KnowledgeBase], int]:
        query = db.query(KnowledgeBase)

        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(
                (KnowledgeBase.name.ilike(like)) | (KnowledgeBase.description.ilike(like))
            )

        if status:
            query = query.filter(KnowledgeBase.status == status)

        if sort == "created_at_asc":
            query = query.order_by(KnowledgeBase.created_at.asc())
        elif sort == "name_asc":
            query = query.order_by(KnowledgeBase.name.asc())
        else:
            query = query.order_by(KnowledgeBase.created_at.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    @staticmethod
    def get_knowledge_base(db: Session, knowledge_base_id: int) -> KnowledgeBase:
        item = db.get(KnowledgeBase, knowledge_base_id)
        if item is None:
            raise KnowledgeBaseNotFoundError(knowledge_base_id)
        return item

    @staticmethod
    def create_knowledge_base(db: Session, payload: KnowledgeBaseCreate) -> KnowledgeBase:
        item = KnowledgeBase(
            name=payload.name.strip(),
            description=payload.description.strip() if payload.description else None,
            tags=payload.tags,
            status=payload.status.value,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update_knowledge_base(
        db: Session,
        knowledge_base_id: int,
        payload: KnowledgeBaseUpdate,
    ) -> KnowledgeBase:
        item = KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
        data = payload.model_dump(exclude_unset=True)

        if "name" in data and data["name"] is not None:
            item.name = data["name"].strip()
        if "description" in data:
            item.description = data["description"].strip() if data["description"] else None
        if "tags" in data and data["tags"] is not None:
            item.tags = data["tags"]
        if "status" in data and data["status"] is not None:
            item.status = data["status"].value

        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete_knowledge_base(db: Session, knowledge_base_id: int) -> None:
        item = KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
        VectorStoreService.delete_knowledge_base_vectors(knowledge_base_id)
        db.delete(item)
        db.commit()
