"""文本切片服务 — 消费 ParseResult，输出并持久化 Chunk。"""

from __future__ import annotations

import re
import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.chunk import Chunk
from app.models.knowledge_item import KnowledgeItem
from app.schemas.chunk import ChunkDraft, ChunkMetadata, ChunkResponse, SourceLocation
from app.schemas.parse import ParseResult, ParseSection

settings = get_settings()

SENTENCE_SEP = re.compile(r"(?<=[。！？；!?;])")
PARAGRAPH_SEP = re.compile(r"\n\s*\n+")


def estimate_tokens(text: str) -> int:
    """Demo：中文粗略 1 字 ≈ 1.5 token；生产环境可换 tiktoken。"""
    return max(1, int(len(text) * 1.5))


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    parts = SENTENCE_SEP.split(text)
    return [p.strip() for p in parts if p.strip()]


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in PARAGRAPH_SEP.split(text) if p.strip()]


def sliding_window(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    step = max(1, size - overlap)
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            for sep in ("。", "！", "？", "；", "\n", "，", " "):
                idx = text.rfind(sep, start + size // 2, end)
                if idx > start:
                    end = idx + 1
                    break
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start += step
    return chunks


def merge_units(units: list[str], size: int, overlap: int) -> list[str]:
    if not units:
        return []

    result: list[str] = []
    buf = ""
    for unit in units:
        candidate = f"{buf}{unit}" if buf else unit
        if len(candidate) <= size:
            buf = candidate
        else:
            if buf:
                result.append(buf)
            if len(unit) > size:
                result.extend(sliding_window(unit, size, overlap))
                buf = ""
            else:
                buf = unit
    if buf:
        result.append(buf)
    return result


def build_heading_path(section: ParseSection, stack: list[str]) -> list[str]:
    if section.title:
        level = section.heading_level or 1
        stack = stack[: level - 1]
        stack.append(section.title)
    return stack


def prefix_content(heading_path: list[str], body: str) -> str:
    if not heading_path:
        return body
    return f"【{' > '.join(heading_path)}】\n{body}"


def chunk_text_block(
    text: str,
    *,
    chunk_size: int,
    overlap: int,
    min_chunk: int,
    char_offset_base: int,
    section: ParseSection | None,
    heading_path: list[str],
    knowledge_item_id: int,
    knowledge_base_id: int,
    order_start: int,
    file_type: str,
    parser_name: str | None = None,
) -> tuple[list[ChunkDraft], int]:
    paragraphs = split_paragraphs(text) or [text]
    units: list[str] = []
    for para in paragraphs:
        if len(para) > chunk_size:
            units.extend(split_sentences(para))
        else:
            units.append(para)

    pieces = merge_units(units, chunk_size, overlap)
    chunks: list[ChunkDraft] = []
    search_from = 0

    for i, piece in enumerate(pieces):
        if len(piece) < min_chunk and i < len(pieces) - 1:
            continue

        local_idx = text.find(piece, search_from)
        if local_idx < 0:
            local_idx = search_from
        abs_start = char_offset_base + local_idx
        abs_end = abs_start + len(piece)
        search_from = local_idx + len(piece)

        full_content = prefix_content(heading_path, piece)
        chunks.append(
            ChunkDraft(
                chunk_id=str(uuid.uuid4()),
                knowledge_item_id=knowledge_item_id,
                knowledge_base_id=knowledge_base_id,
                content=full_content,
                order_index=order_start + len(chunks),
                token_count=estimate_tokens(full_content),
                source_location=SourceLocation(
                    page_start=section.page_start if section else None,
                    page_end=section.page_end if section else None,
                    section_index=section.index if section else None,
                    section_title=section.title if section else None,
                    heading_path=list(heading_path),
                    char_start=abs_start,
                    char_end=abs_end,
                ),
                metadata=ChunkMetadata(
                    chunk_size=chunk_size,
                    overlap=overlap,
                    file_type=file_type,
                    parser_name=parser_name,
                    is_continued=i > 0,
                ),
            )
        )

    return chunks, order_start + len(chunks)


def chunk_parse_result(
    parse_result: ParseResult,
    *,
    knowledge_item_id: int,
    knowledge_base_id: int,
    chunk_size: int | None = None,
    overlap: int | None = None,
    min_chunk_size: int | None = None,
) -> list[ChunkDraft]:
    """ParseResult → ChunkDraft 列表。优先 sections，否则 fallback raw_text。"""
    size = chunk_size if chunk_size is not None else settings.chunk_size
    ovlp = overlap if overlap is not None else settings.chunk_overlap
    min_chunk = min_chunk_size if min_chunk_size is not None else settings.chunk_min_size

    raw = normalize_text(parse_result.raw_text)
    if not raw:
        return []

    parser_name = parse_result.metadata.parser_name if parse_result.metadata else None
    all_chunks: list[ChunkDraft] = []
    order = 0
    heading_stack: list[str] = []

    if parse_result.sections:
        cursor = 0
        for section in parse_result.sections:
            body = normalize_text(section.text)
            if not body:
                continue
            heading_stack = build_heading_path(section, heading_stack)
            char_base = raw.find(body, cursor)
            if char_base < 0:
                char_base = cursor

            chunks, order = chunk_text_block(
                body,
                chunk_size=size,
                overlap=ovlp,
                min_chunk=min_chunk,
                char_offset_base=char_base,
                section=section,
                heading_path=heading_stack,
                knowledge_item_id=knowledge_item_id,
                knowledge_base_id=knowledge_base_id,
                order_start=order,
                file_type=parse_result.file_type,
                parser_name=parser_name,
            )
            all_chunks.extend(chunks)
            cursor = char_base + len(body)
    else:
        chunks, _ = chunk_text_block(
            raw,
            chunk_size=size,
            overlap=ovlp,
            min_chunk=min_chunk,
            char_offset_base=0,
            section=None,
            heading_path=[],
            knowledge_item_id=knowledge_item_id,
            knowledge_base_id=knowledge_base_id,
            order_start=0,
            file_type=parse_result.file_type,
            parser_name=parser_name,
        )
        all_chunks = chunks

    return all_chunks


def parse_result_from_item(item: KnowledgeItem) -> ParseResult:
    """手动录入条目无解析结果时，构造最小 ParseResult。"""
    return ParseResult(
        success=True,
        title=item.title,
        raw_text=item.content or "",
        file_type=item.file_type or "manual",
    )


class ChunkService:
    @staticmethod
    def to_response(row: Chunk) -> ChunkResponse:
        return ChunkResponse(
            chunk_id=row.id,
            knowledge_item_id=row.knowledge_item_id,
            content=row.content,
            order_index=row.order_index,
            token_count=row.token_count,
            source_location=SourceLocation.model_validate(row.source_location),
            metadata=ChunkMetadata.model_validate(row.chunk_metadata),
        )

    @staticmethod
    def list_chunks(db: Session, item_id: int) -> list[Chunk]:
        return (
            db.query(Chunk)
            .filter(Chunk.knowledge_item_id == item_id)
            .order_by(Chunk.order_index.asc())
            .all()
        )

    @staticmethod
    def delete_chunks_for_item(db: Session, item_id: int) -> None:
        db.query(Chunk).filter(Chunk.knowledge_item_id == item_id).delete()

    @staticmethod
    def persist_chunks(db: Session, drafts: list[ChunkDraft]) -> list[Chunk]:
        rows = [
            Chunk(
                id=d.chunk_id,
                knowledge_item_id=d.knowledge_item_id,
                knowledge_base_id=d.knowledge_base_id,
                content=d.content,
                order_index=d.order_index,
                token_count=d.token_count,
                source_location=d.source_location.model_dump(),
                chunk_metadata=d.metadata.model_dump(),
            )
            for d in drafts
        ]
        db.add_all(rows)
        return rows

    @staticmethod
    def apply_to_item(
        db: Session,
        item: KnowledgeItem,
        parse_result: ParseResult | None = None,
    ) -> list[ChunkDraft]:
        """对条目执行切片并持久化，更新 chunk_count。"""
        result = parse_result or parse_result_from_item(item)
        ChunkService.delete_chunks_for_item(db, item.id)

        drafts = chunk_parse_result(
            result,
            knowledge_item_id=item.id,
            knowledge_base_id=item.knowledge_base_id,
        )
        if drafts:
            ChunkService.persist_chunks(db, drafts)
        item.chunk_count = len(drafts)
        return drafts
