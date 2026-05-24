from enum import StrEnum

from pydantic import BaseModel, Field


class ParserKind(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    MARKDOWN = "md"
    TEXT = "txt"


class ParseErrorCode(StrEnum):
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    FILE_CORRUPT = "FILE_CORRUPT"
    EMPTY_CONTENT = "EMPTY_CONTENT"
    ENCODING_ERROR = "ENCODING_ERROR"
    PARSER_INTERNAL = "PARSER_INTERNAL"
    LEGACY_DOC = "LEGACY_DOC"


class ParseSection(BaseModel):
    index: int
    title: str | None = None
    text: str
    page_start: int | None = None
    page_end: int | None = None
    heading_level: int | None = None


class ParseMetadata(BaseModel):
    page_count: int | None = None
    word_count: int | None = None
    char_count: int | None = None
    parser_name: str = "unknown"
    warnings: list[str] = Field(default_factory=list)


class ParseResult(BaseModel):
    success: bool
    title: str = ""
    raw_text: str = ""
    sections: list[ParseSection] = Field(default_factory=list)
    source_type: str = "file"
    file_type: str = ""
    page_count: int | None = None
    metadata: ParseMetadata = Field(default_factory=ParseMetadata)
    error_code: ParseErrorCode | None = None
    error_message: str | None = None


class ParseItemResponse(BaseModel):
    knowledge_item_id: int
    parse_status: str
    item_status: str
    error_message: str | None = None
