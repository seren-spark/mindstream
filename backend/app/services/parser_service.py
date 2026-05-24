import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.parsers.registry import ParserRegistry
from app.parsers.text_utils import derive_title
from app.schemas.knowledge_item import KnowledgeItemStatus
from app.schemas.parse import ParseErrorCode, ParseResult
from app.schemas.upload import ParseStatus
from app.services.knowledge_item_service import KnowledgeItemService

logger = logging.getLogger(__name__)


class ParserService:
    @staticmethod
    def can_parse(file_path: str) -> bool:
        return ParserRegistry.is_supported(file_path)

    @staticmethod
    def derive_title(filename: str) -> str:
        return derive_title(filename, filename)

    @staticmethod
    def parse_file(file_path: str, *, filename: str | None = None) -> ParseResult:
        path = Path(file_path)
        display_name = filename or path.name

        if not path.exists():
            return ParseResult(
                success=False,
                title=derive_title(display_name, file_path),
                error_code=ParseErrorCode.FILE_NOT_FOUND,
                error_message="文件不存在或已被删除",
            )

        if not ParserRegistry.is_supported(str(path)):
            return ParseResult(
                success=False,
                title=derive_title(display_name, file_path),
                file_type=path.suffix.lstrip(".").lower(),
                error_code=ParseErrorCode.UNSUPPORTED_FORMAT,
                error_message=f"暂不支持解析 {path.suffix} 格式",
            )

        try:
            parser = ParserRegistry.get_parser(str(path))
            return parser.parse(str(path), filename=display_name)
        except Exception:
            logger.exception("Parser failed for %s", path)
            return ParseResult(
                success=False,
                title=derive_title(display_name, file_path),
                file_type=path.suffix.lstrip(".").lower(),
                error_code=ParseErrorCode.PARSER_INTERNAL,
                error_message="文档解析失败，请稍后重试",
            )

    @staticmethod
    def apply_to_item(db: Session, item: KnowledgeItem) -> tuple[ParseStatus, str | None]:
        if not item.file_path:
            return ParseStatus.FAILED, "文件路径缺失"

        file_path = Path(item.file_path)
        if not file_path.exists():
            item.status = KnowledgeItemStatus.FAILED.value
            item.error_message = "文件不存在或已被删除"
            item.processing_progress = 0
            db.commit()
            return ParseStatus.FAILED, item.error_message

        if not ParserRegistry.is_supported(str(file_path)):
            message = f"暂不支持解析 .{item.file_type or file_path.suffix.lstrip('.')} 格式"
            item.status = KnowledgeItemStatus.PENDING.value
            item.processing_progress = 0
            item.error_message = message
            db.commit()
            return ParseStatus.PENDING, message

        item.status = KnowledgeItemStatus.PROCESSING.value
        item.processing_progress = 30
        item.error_message = None
        db.commit()

        result = ParserService.parse_file(str(file_path), filename=item.file_name)
        if result.success:
            item.content = result.raw_text.strip()
            if result.title:
                item.title = result.title
            KnowledgeItemService._finalize_ready(db, item, parse_result=result)
            db.commit()
            db.refresh(item)
            return ParseStatus.COMPLETED, None

        item.status = KnowledgeItemStatus.FAILED.value
        item.error_message = result.error_message or "文档解析失败"
        item.processing_progress = 0
        db.commit()
        db.refresh(item)
        return ParseStatus.FAILED, item.error_message
