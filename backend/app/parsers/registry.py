from pathlib import Path

from app.parsers.base import BaseDocumentParser
from app.parsers.docx_parser import DocxParser
from app.parsers.legacy_doc_parser import LegacyDocParser
from app.parsers.markdown_parser import MarkdownParser
from app.parsers.pdf_parser import PdfParser
from app.parsers.txt_parser import TxtParser

_REGISTRY: dict[str, BaseDocumentParser] = {
    ".pdf": PdfParser(),
    ".docx": DocxParser(),
    ".doc": LegacyDocParser(),
    ".md": MarkdownParser(),
    ".markdown": MarkdownParser(),
    ".txt": TxtParser(),
}


class ParserRegistry:
    @classmethod
    def supported_extensions(cls) -> frozenset[str]:
        return frozenset(_REGISTRY.keys())

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in _REGISTRY

    @classmethod
    def get_parser(cls, file_path: str) -> BaseDocumentParser:
        ext = Path(file_path).suffix.lower()
        parser = _REGISTRY.get(ext)
        if parser is None:
            raise ValueError(f"unsupported extension: {ext}")
        return parser
