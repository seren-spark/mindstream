from typing import Protocol

from app.schemas.parse import ParseResult, ParserKind


class BaseDocumentParser(Protocol):
    kind: ParserKind
    supported_extensions: frozenset[str]

    def parse(self, file_path: str, *, filename: str | None = None) -> ParseResult: ...
