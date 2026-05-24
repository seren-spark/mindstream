import logging
from pathlib import Path

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from app.parsers.text_utils import derive_title
from app.schemas.parse import (
    ParseErrorCode,
    ParseMetadata,
    ParseResult,
    ParserKind,
    ParseSection,
)

logger = logging.getLogger(__name__)

HEADING_PREFIX = "Heading"


class DocxParser:
    kind = ParserKind.DOCX
    supported_extensions = frozenset({".docx"})

    def parse(self, file_path: str, *, filename: str | None = None) -> ParseResult:
        path = Path(file_path)
        title = derive_title(filename, file_path)

        try:
            document = Document(str(path))
        except PackageNotFoundError:
            return ParseResult(
                success=False,
                title=title,
                file_type="docx",
                error_code=ParseErrorCode.FILE_CORRUPT,
                error_message="Word 文件已损坏或格式不正确，请重新导出后上传",
                metadata=ParseMetadata(parser_name="python-docx"),
            )
        except Exception as exc:
            logger.warning("DOCX open failed: %s", path, exc_info=exc)
            return ParseResult(
                success=False,
                title=title,
                file_type="docx",
                error_code=ParseErrorCode.FILE_CORRUPT,
                error_message="Word 文件已损坏或格式不正确，请重新导出后上传",
                metadata=ParseMetadata(parser_name="python-docx"),
            )

        sections: list[ParseSection] = []
        current_title: str | None = None
        current_level: int | None = None
        current_lines: list[str] = []

        def flush() -> None:
            nonlocal current_title, current_level, current_lines
            text = "\n".join(current_lines).strip()
            if text or current_title:
                sections.append(
                    ParseSection(
                        index=len(sections),
                        title=current_title,
                        text=text,
                        heading_level=current_level,
                    )
                )
            current_lines = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue

            style_name = paragraph.style.name if paragraph.style else ""
            if style_name.startswith(HEADING_PREFIX):
                flush()
                level_text = style_name.removeprefix(HEADING_PREFIX).strip()
                current_level = int(level_text) if level_text.isdigit() else 1
                current_title = text
                continue

            current_lines.append(text)

        flush()

        if not sections:
            return ParseResult(
                success=False,
                title=title,
                file_type="docx",
                error_code=ParseErrorCode.EMPTY_CONTENT,
                error_message="未能从 Word 文档提取文本",
                metadata=ParseMetadata(parser_name="python-docx"),
            )

        raw_text = "\n\n".join(
            (f"{section.title}\n{section.text}" if section.title else section.text)
            for section in sections
        ).strip()

        return ParseResult(
            success=True,
            title=title,
            raw_text=raw_text,
            sections=sections,
            file_type="docx",
            metadata=ParseMetadata(
                parser_name="python-docx",
                char_count=len(raw_text),
                word_count=len(raw_text.split()),
            ),
        )
