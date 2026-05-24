import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.knowledge_item import KnowledgeItem
from app.schemas.knowledge_item import KnowledgeItemSourceType, KnowledgeItemStatus
from app.schemas.upload import BatchUploadResponse, ParseStatus, UploadFileResult
from app.services.knowledge_base_service import KnowledgeBaseNotFoundError, KnowledgeBaseService
from app.services.parser_service import ParserService
from app.utils.file_helpers import (
    FileValidationError,
    build_stored_filename,
    build_upload_path,
    validate_upload_file,
)

settings = get_settings()


class UploadService:
    @staticmethod
    def _create_file_item(
        db: Session,
        *,
        knowledge_base_id: int,
        original_filename: str,
        stored_filename: str,
        target_path: Path,
        mime_type: str,
        file_type: str,
        size: int,
        category: str | None,
        tags: list[str],
    ) -> KnowledgeItem:
        title = ParserService.derive_title(original_filename)
        item = KnowledgeItem(
            knowledge_base_id=knowledge_base_id,
            title=title,
            source_type=KnowledgeItemSourceType.FILE.value,
            status=KnowledgeItemStatus.PENDING.value,
            file_name=original_filename,
            file_path=str(target_path.as_posix()),
            file_type=file_type,
            mime_type=mime_type,
            file_size=size,
            category=category,
            tags=tags,
            processing_progress=0,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def _parse_item(db: Session, item: KnowledgeItem) -> tuple[ParseStatus, str | None]:
        return ParserService.apply_to_item(db, item)

    @staticmethod
    async def upload_single_file(
        db: Session,
        knowledge_base_id: int,
        upload_file: UploadFile,
        *,
        category: str | None = None,
        tags: list[str] | None = None,
        auto_parse: bool = True,
    ) -> UploadFileResult:
        try:
            KnowledgeBaseService.get_knowledge_base(db, knowledge_base_id)
        except KnowledgeBaseNotFoundError as exc:
            raise exc

        upload_id = uuid.uuid4().hex
        filename = upload_file.filename or "unnamed_file"
        content = await upload_file.read()
        size = len(content)

        try:
            mime_type, file_type = validate_upload_file(filename, size, upload_file.content_type)
        except FileValidationError as exc:
            return UploadFileResult(
                upload_id=upload_id,
                knowledge_item_id=0,
                knowledge_base_id=knowledge_base_id,
                original_filename=filename,
                stored_filename="",
                mime_type=upload_file.content_type or "application/octet-stream",
                file_type="",
                size=size,
                item_status=KnowledgeItemStatus.FAILED,
                parse_status=ParseStatus.FAILED,
                error_message=exc.message,
            )

        stored_filename = build_stored_filename(filename)
        target_path = build_upload_path(knowledge_base_id, stored_filename)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(target_path, "wb") as out_file:
            await out_file.write(content)

        item = UploadService._create_file_item(
            db,
            knowledge_base_id=knowledge_base_id,
            original_filename=filename,
            stored_filename=stored_filename,
            target_path=target_path,
            mime_type=mime_type,
            file_type=file_type,
            size=size,
            category=category.strip() if category else None,
            tags=tags or [],
        )

        parse_status = ParseStatus.PENDING
        error_message: str | None = None
        if auto_parse:
            parse_status, error_message = UploadService._parse_item(db, item)
            db.refresh(item)

        return UploadFileResult(
            upload_id=upload_id,
            knowledge_item_id=item.id,
            knowledge_base_id=knowledge_base_id,
            original_filename=filename,
            stored_filename=stored_filename,
            mime_type=mime_type,
            file_type=file_type,
            size=size,
            item_status=KnowledgeItemStatus(item.status),
            parse_status=parse_status,
            error_message=error_message,
        )

    @staticmethod
    async def upload_batch_files(
        db: Session,
        knowledge_base_id: int,
        upload_files: list[UploadFile],
        *,
        category: str | None = None,
        tags: list[str] | None = None,
        auto_parse: bool = True,
    ) -> BatchUploadResponse:
        results: list[UploadFileResult] = []
        for upload_file in upload_files:
            result = await UploadService.upload_single_file(
                db,
                knowledge_base_id,
                upload_file,
                category=category,
                tags=tags,
                auto_parse=auto_parse,
            )
            results.append(result)

        succeeded = sum(1 for item in results if item.knowledge_item_id > 0)
        failed = len(results) - succeeded
        return BatchUploadResponse(
            total=len(results),
            succeeded=succeeded,
            failed=failed,
            results=results,
        )
