from pathlib import Path

from app.parsers.text_utils import derive_title, read_text_file
from app.schemas.parse import (
    ParseErrorCode,
    ParseMetadata,
    ParseResult,
    ParserKind,
    ParseSection,
)


class TxtParser:
    kind = ParserKind.TEXT
    supported_extensions = frozenset({".txt"})

    def parse(self, file_path: str, *, filename: str | None = None) -> ParseResult:
        path = Path(file_path)
        title = derive_title(filename, file_path)

        try:
            content = read_text_file(path)
        except ValueError:
            return ParseResult(
                success=False,
                title=title,
                file_type="txt",
                error_code=ParseErrorCode.ENCODING_ERROR,
                error_message="无法识别文本编码，请另存为 UTF-8 后重试",
                metadata=ParseMetadata(parser_name="stdlib"),
            )

        raw_text = content.strip()
        if not raw_text:
            return ParseResult(
                success=False,
                title=title,
                file_type="txt",
                error_code=ParseErrorCode.EMPTY_CONTENT,
                error_message="文档内容为空",
                metadata=ParseMetadata(parser_name="stdlib"),
            )

        sections = [ParseSection(index=0, text=raw_text)]
        return ParseResult(
            success=True,
            title=title,
            raw_text=raw_text,
            sections=sections,
            file_type="txt",
            metadata=ParseMetadata(
                parser_name="stdlib",
                char_count=len(raw_text),
                word_count=len(raw_text.split()),
            ),
        )
