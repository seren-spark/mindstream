import re
from pathlib import Path

from app.schemas.parse import ParseSection

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
TEXT_ENCODINGS = ("utf-8", "utf-8-sig", "gbk")


def derive_title(filename: str | None, file_path: str) -> str:
    name = filename or Path(file_path).name
    stem = Path(name).stem.strip()
    return stem[:200] if stem else "未命名文档"


def read_text_file(path: Path) -> str:
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("encoding_error")


def split_markdown_sections(content: str) -> list[ParseSection]:
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

    for line in content.splitlines():
        match = HEADING_PATTERN.match(line)
        if match:
            flush()
            current_level = len(match.group(1))
            current_title = match.group(2).strip()
            continue
        current_lines.append(line)

    flush()

    if not sections and content.strip():
        sections.append(ParseSection(index=0, text=content.strip()))

    return sections
