from app.parsers.text_utils import derive_title
from app.schemas.parse import ParseErrorCode, ParseMetadata, ParseResult, ParserKind


class LegacyDocParser:
    kind = ParserKind.DOC
    supported_extensions = frozenset({".doc"})

    def parse(self, file_path: str, *, filename: str | None = None) -> ParseResult:
        title = derive_title(filename, file_path)
        return ParseResult(
            success=False,
            title=title,
            file_type="doc",
            error_code=ParseErrorCode.LEGACY_DOC,
            error_message="暂不支持旧版 .doc 格式，请在 Word 中另存为 .docx 后重新上传",
            metadata=ParseMetadata(parser_name="legacy-doc"),
        )
