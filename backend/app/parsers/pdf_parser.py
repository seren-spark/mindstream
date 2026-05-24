import logging
from pathlib import Path

from pypdf import PdfReader

from app.parsers.text_utils import derive_title
from app.schemas.parse import (
    ParseErrorCode,
    ParseMetadata,
    ParseResult,
    ParserKind,
    ParseSection,
)

logger = logging.getLogger(__name__)


class PdfParser:
    kind = ParserKind.PDF
    supported_extensions = frozenset({".pdf"})

    def parse(self, file_path: str, *, filename: str | None = None) -> ParseResult:
        path = Path(file_path)
        title = derive_title(filename, file_path)

        try:
            reader = PdfReader(str(path))
        except Exception as exc:
            logger.warning("PDF open failed: %s", path, exc_info=exc)
            return ParseResult(
                success=False,
                title=title,
                file_type="pdf",
                error_code=ParseErrorCode.FILE_CORRUPT,
                error_message="PDF 文件已损坏或无法打开，请重新导出后上传",
                metadata=ParseMetadata(parser_name="pypdf"),
            )

        page_count = len(reader.pages)
        sections: list[ParseSection] = []
        warnings: list[str] = []

        for index, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if text:
                sections.append(
                    ParseSection(
                        index=len(sections),
                        text=text,
                        page_start=index + 1,
                        page_end=index + 1,
                    )
                )
            else:
                warnings.append(f"第 {index + 1} 页未提取到文本")

        raw_text = "\n\n".join(section.text for section in sections).strip()
        if not raw_text:
            return ParseResult(
                success=False,
                title=title,
                file_type="pdf",
                page_count=page_count,
                error_code=ParseErrorCode.EMPTY_CONTENT,
                error_message="未能从 PDF 提取文本，可能为扫描版，后续可接入 OCR",
                metadata=ParseMetadata(
                    parser_name="pypdf",
                    page_count=page_count,
                    warnings=warnings,
                ),
            )

        return ParseResult(
            success=True,
            title=title,
            raw_text=raw_text,
            sections=sections,
            file_type="pdf",
            page_count=page_count,
            metadata=ParseMetadata(
                parser_name="pypdf",
                page_count=page_count,
                char_count=len(raw_text),
                word_count=len(raw_text.split()),
                warnings=warnings,
            ),
        )
