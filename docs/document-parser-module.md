# 文档解析模块设计

> 对齐：`AI 知识库管理平台 - 技术方案.docx`、`document-upload-module.md`、`knowledge-item-module.md`  
> 当前实现：`backend/app/services/parser_service.py`（TXT/MD 已接入，PDF/Word 占位）

---

## 1. 模块职责定义

### 在知识生产链路中的位置

```
选择文件 → 上传落盘 → 创建 knowledge_item → 【解析 parse】 → 切片 chunk → 向量化 embed → 可检索 RAG
                                              ↑ 本模块
```

解析模块位于 **「文件字节」与「可切分纯文本」** 之间：输入是磁盘上的 `file_path` + 文件元信息，输出是统一的 `ParseResult`，供 `chunk_service` 消费。

### 为什么要独立成服务层

| 原因 | 说明 |
|------|------|
| 与上传解耦 | 上传只管校验、落盘、建条目；解析可同步（Demo）或异步（BackgroundTasks / 队列）切换，不改上传 API 契约 |
| 与切片解耦 | 解析输出「文档级」结构与 `raw_text`；切片只关心 token/段落边界，不关心 PDF 用哪套库 |
| 可测试 | 给定 fixture 文件即可单测 parser，无需走 HTTP / DB |
| 可扩展 | 新增 `.pptx` 只加 `PptxParser`，不动 upload / chunk / embed |
| 状态可追踪 | 解析失败写入 `error_message`，与条目状态机 `pending → processing → ready/failed` 对齐 |

---

## 2. 整体 Pipeline 设计

### 从文件到纯文本的完整步骤

```
1. 接收 ParseRequest（item_id, file_path, file_type, original_filename）
2. 校验文件存在、扩展名与 file_type 一致
3. ParserRegistry.get_parser(file_type) → 具体 Parser 实例
4. parser.parse(path) → ParseResult（含 raw_text、sections、metadata）
5. 后置校验：raw_text 去空白后非空；过短可 warning 但不必然 failed
6. 写回 knowledge_item：content=raw_text, title 可覆盖, status=ready；失败则 failed + error_message
7. （可选）触发 chunk_service.chunk(item_id, parse_result)
```

### 不同文件格式如何分发

采用 **注册表 + 策略类**（比巨型 if-else 更易扩展）：

```
.ext / file_type  →  PdfParser | DocxParser | MarkdownParser | TxtParser
```

路由键优先级：`Path.suffix.lower()` → 映射到 `ParserKind` 枚举。

### 统一接口设计

```python
class BaseDocumentParser(Protocol):
    kind: ParserKind
    supported_extensions: frozenset[str]

    def parse(self, file_path: str, *, filename: str | None = None) -> ParseResult: ...

class ParserRegistry:
    @classmethod
    def get_parser(cls, file_path: str) -> BaseDocumentParser: ...
```

`ParserService` 对外只暴露：

- `parse_file(file_path, filename) -> ParseResult`
- `apply_to_item(db, item) -> ParseStatus`（编排 DB + 状态机，供 upload / 重试 API 调用）

---

## 3. 数据结构设计

### Parser 输出：`ParseResult`

```python
class ParseSection(BaseModel):
    """便于引用源展示与按标题切片"""
    index: int
    title: str | None = None
    text: str
    page_start: int | None = None   # PDF 等
    page_end: int | None = None
    heading_level: int | None = None  # MD 标题级别

class ParseMetadata(BaseModel):
    page_count: int | None = None
    word_count: int | None = None
    char_count: int | None = None
    language: str | None = None
    parser_name: str              # e.g. "pypdf", "python-docx"
    parser_version: str | None = None
    warnings: list[str] = []      # 如「部分页无文本」

class ParseResult(BaseModel):
  success: bool
  title: str                      # 默认文件名 stem，PDF 可尝试 metadata
  raw_text: str                   # 全文，chunk 主输入
  sections: list[ParseSection]    # 可选，供按章节切片 / 引用
  source_type: str                # file
  file_type: str                  # pdf | docx | md | txt
  page_count: int | None = None
  metadata: ParseMetadata
  error_code: str | None = None   # FILE_CORRUPT | EMPTY_CONTENT | ...
  error_message: str | None = None
```

### 字段取舍（Demo）

| 字段 | MVP | 说明 |
|------|-----|------|
| `raw_text` | ✅ 必需 | chunk 的统一输入 |
| `title` | ✅ | 列表与引用源标题 |
| `sections` | ⚠️ 简化 | TXT 整篇 1 段；MD 按 `#` 拆；PDF 按页或整篇 |
| `page_count` | PDF ✅ | 引用「第 N 页」 |
| `metadata` | 基础 | 字数、解析器名，便于排障 |
| `sections` 精细结构 | 后续 | Word 标题样式、PDF 书签 |

### 与切片模块的兼容

`chunk_service` 入参建议：

```python
def chunk_item(parse_result: ParseResult, *, chunk_size: int = 500, overlap: int = 50) -> list[ChunkDraft]:
    # 优先 sections 非空则按 section 再切；否则对 raw_text 按 token/字符切
```

每个 `ChunkDraft` 携带 `source_page`、`section_title`，写入 `chunks` 表后供 RAG `references` 展示。

---

## 4. 各格式解析策略

### 技术选型（与技术方案 docx 一致）

| 格式 | 推荐库 | 优点 | 缺点 | Demo 取舍 |
|------|--------|------|------|-----------|
| **PDF** | `pypdf`（PyPDF2 继任） | 纯 Python、无系统依赖、安装快 | 扫描版无 OCR；复杂版式易乱序 | ✅ Demo 用；扫描版提示「需 OCR」 |
| **Word** | `python-docx` | 只读 .docx 稳定、API 简单 | 不支持旧 `.doc` | ✅ 仅 docx；`.doc` 提示转换 |
| **Markdown** | 标准库读文件 + 可选 `markdown-it-py` | 原文保留；it-py 可抽标题 | 渲染非必需 | MVP：读原文 + 按 `#` 拆 section |
| **TXT** | 标准库 + 多编码尝试 | 已实现（utf-8/gbk） | 无结构 | ✅ 保持现有逻辑 |

备选（不默认引入）：

- PDF 版式差：`pdfplumber`（表格好，依赖重一点）
- OCR：`pytesseract`（加分项，非 MVP）

### 各 Parser 行为要点

**PdfParser**

- `PdfReader.pages` 逐页 `extract_text()`
- `page_count = len(reader.pages)`
- 每页一个 `ParseSection`，`page_start=page_end=页码`
- 全文 `raw_text = "\n\n".join(sections)`

**DocxParser**

- 遍历 `document.paragraphs`，跳过空段
- 若 `paragraph.style.name` 以 `Heading` 开头，开新 section
- MVP 可退化为单 section 拼接

**MarkdownParser / TxtParser**

- 编码：`utf-8` → `utf-8-sig` → `gbk`（与现实现一致）
- MD：按行匹配 `^#{1,6}\s` 切 section；无标题则单 section

---

## 5. 错误处理设计

### 错误分类与错误码

| 场景 | error_code | 用户可见文案示例 |
|------|------------|------------------|
| 文件不存在 | `FILE_NOT_FOUND` | 文件不存在或已被删除 |
| 扩展名不支持 | `UNSUPPORTED_FORMAT` | 暂不支持 .xxx，请上传 PDF/Word/MD/TXT |
| 文件损坏 / 无法打开 | `FILE_CORRUPT` | 文件已损坏或格式不正确，请重新导出后上传 |
| 提取为空 | `EMPTY_CONTENT` | 未能从文档中提取文本（可能为扫描版 PDF） |
| 编码无法识别 | `ENCODING_ERROR` | 无法识别文本编码，请另存为 UTF-8 |
| 第三方库异常 | `PARSER_INTERNAL` | 解析失败，请稍后重试或联系管理员 |
| 旧版 .doc | `LEGACY_DOC` | 请另存为 .docx 后重新上传 |

### 透传路径

```
Parser.parse() 捕获异常 → ParseResult(success=False, error_code, error_message)
    → ParserService.apply_to_item()
        → knowledge_item.status = failed
        → knowledge_item.error_message = 友好文案
        → upload 响应 parse_status = failed
    → 前端 FileItem / 条目详情展示 error_message
```

**原则**：库异常记 `logger.exception`；前端只见 `error_message`，不见堆栈。

### 与状态机

```
pending --(开始解析)--> processing --(成功)--> ready
                              |
                              +--(失败)--> failed
```

重试：`failed → pending`，再调 `POST /knowledge-items/{id}/parse`（后续 API）。

---

## 6. 服务层设计建议

### 目录拆分（建议）

```
backend/app/
  services/
    parser_service.py          # 门面：parse_file、apply_to_item
  parsers/
    base.py                    # BaseDocumentParser, ParseResult
    registry.py                # ParserRegistry
    pdf_parser.py
    docx_parser.py
    markdown_parser.py
    txt_parser.py
  schemas/
    parse.py                   # ParseResult, ParseSection Pydantic
```

### 工厂 vs 路由

- **Demo**：`ParserRegistry` 字典 `{".pdf": PdfParser(), ...}` 即可，够面试讲清「开闭原则」。
- **后续**：可按 `file_type` 配置启用、降级（如 PDF 先 pypdf，失败再 pdfplumber）。

### 扩展新格式

1. 新建 `XxxParser` 实现 `parse()`
2. `registry.register(".xxx", XxxParser())`
3. `config.allowed_upload_extensions` 与前端常量同步

---

## 7. 与后续模块的接口边界

### 解析 → 切片

**交给 chunk 的：**

- `ParseResult.raw_text`（必需）
- `ParseResult.sections`（可选，用于语义边界）
- `file_type`, `page_count`, `title`（写入 chunk 元数据）

**不交给 chunk 的：**

- 原始文件字节、解析器内部对象

### 解析模块不应承担

- 文件上传、存储路径生成
- Token 计数与切片算法
- Embedding、ChromaDB 写入
- LLM 调用、摘要生成（可另设 `summary_service` 读 `content`）

### 避免耦合

- `chunk_service` 只依赖 `schemas/parse.py`，不 import `pypdf`
- 上传模块通过 `ParserService.apply_to_item` 触发解析，不直接 `import PdfParser`
- 解析结果写入 `knowledge_item.content` 是 **持久化策略**，可抽 `KnowledgeItemRepository.update_from_parse()`

---

## 8. 代码示例（可直接落地）

### 8.1 Schema

```python
# backend/app/schemas/parse.py
from enum import Enum
from pydantic import BaseModel, Field

class ParserKind(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "md"
    TEXT = "txt"

class ParseErrorCode(str, Enum):
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
```

### 8.2 注册表与 PDF 解析器（示例）

```python
# backend/app/parsers/registry.py
from pathlib import Path
from app.parsers.pdf_parser import PdfParser
from app.parsers.docx_parser import DocxParser
from app.parsers.markdown_parser import MarkdownParser
from app.parsers.txt_parser import TxtParser
from app.parsers.base import BaseDocumentParser

_REGISTRY: dict[str, BaseDocumentParser] = {
    ".pdf": PdfParser(),
    ".docx": DocxParser(),
    ".doc": DocxParser(),  # 仅 docx 真正支持，doc 在 parser 内抛 LEGACY_DOC
    ".md": MarkdownParser(),
    ".markdown": MarkdownParser(),
    ".txt": TxtParser(),
}

class ParserRegistry:
    @classmethod
    def get_parser(cls, file_path: str) -> BaseDocumentParser:
        ext = Path(file_path).suffix.lower()
        parser = _REGISTRY.get(ext)
        if not parser:
            raise ValueError(f"unsupported extension: {ext}")
        return parser
```

```python
# backend/app/parsers/pdf_parser.py
from pypdf import PdfReader
from app.schemas.parse import ParseResult, ParseSection, ParseMetadata, ParseErrorCode

class PdfParser:
    kind = "pdf"
    supported_extensions = frozenset({".pdf"})

    def parse(self, file_path: str, *, filename: str | None = None) -> ParseResult:
        try:
            reader = PdfReader(file_path)
        except Exception:
            return ParseResult(
                success=False,
                file_type="pdf",
                error_code=ParseErrorCode.FILE_CORRUPT,
                error_message="PDF 文件已损坏或无法打开",
                metadata=ParseMetadata(parser_name="pypdf"),
            )

        sections: list[ParseSection] = []
        for i, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if text:
                sections.append(
                    ParseSection(
                        index=len(sections),
                        text=text,
                        page_start=i + 1,
                        page_end=i + 1,
                    )
                )

        raw_text = "\n\n".join(s.text for s in sections).strip()
        if not raw_text:
            return ParseResult(
                success=False,
                file_type="pdf",
                page_count=len(reader.pages),
                error_code=ParseErrorCode.EMPTY_CONTENT,
                error_message="未能提取文本，可能为扫描版 PDF，后续可接入 OCR",
                metadata=ParseMetadata(parser_name="pypdf", page_count=len(reader.pages)),
            )

        title = (filename or Path(file_path).stem)[:200]
        return ParseResult(
            success=True,
            title=title,
            raw_text=raw_text,
            sections=sections,
            file_type="pdf",
            page_count=len(reader.pages),
            metadata=ParseMetadata(
                parser_name="pypdf",
                page_count=len(reader.pages),
                char_count=len(raw_text),
            ),
        )
```

### 8.3 ParserService 门面

```python
# backend/app/services/parser_service.py（演进版示意）
from pathlib import Path
from app.parsers.registry import ParserRegistry
from app.schemas.parse import ParseResult, ParseErrorCode

class ParserService:
    @staticmethod
    def parse_file(file_path: str, *, filename: str | None = None) -> ParseResult:
        path = Path(file_path)
        if not path.exists():
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.FILE_NOT_FOUND,
                error_message="文件不存在或已被删除",
            )
        try:
            parser = ParserRegistry.get_parser(str(path))
            return parser.parse(str(path), filename=filename)
        except ValueError:
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.UNSUPPORTED_FORMAT,
                error_message=f"暂不支持 {path.suffix} 格式",
            )
        except Exception:
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.PARSER_INTERNAL,
                error_message="文档解析失败，请稍后重试",
            )

    @staticmethod
    def derive_title(filename: str) -> str:
        stem = Path(filename).stem.strip()
        return stem[:200] if stem else "未命名文档"
```

### 8.4 在 Upload / FastAPI 中调用

```python
# upload_service._parse_item 内
result = ParserService.parse_file(item.file_path, filename=item.file_name)
if not result.success:
    item.status = KnowledgeItemStatus.FAILED.value
    item.error_message = result.error_message
    return ParseStatus.FAILED, result.error_message

item.content = result.raw_text
item.title = result.title or ParserService.derive_title(item.file_name or "")
item.status = KnowledgeItemStatus.READY.value
# chunk_service.chunk_from_parse(item.id, result)  # 下一阶段
```

```python
# 独立重试 API（可选）
@router.post("/knowledge-items/{item_id}/parse")
def reparse_item(item_id: int, db: Session = Depends(get_db)):
    item = KnowledgeItemService.get_item(db, item_id)
    status, msg = UploadService._parse_item(db, item)  # 或 ParserService.apply_to_item
    return {"parse_status": status, "error_message": msg}
```

### 8.5 依赖

```text
# backend/requirements.txt 追加
pypdf>=5.0.0
python-docx>=1.1.0
```

---

## 9. 演示与面试表达

### 「文档解析质量决定 RAG 上限」

> 检索和生成再强，也只能基于 **解析后的文本**。PDF 乱序、表格丢失、扫描版空白会导致 chunk 无信息，向量检索召回噪声，模型就会胡编。所以我们在链路里单独做 parser 层，并对 **空文本、扫描版** 显式失败或告警，而不是静默进入 ready。

### 「不同格式的统一抽象」

> 上传侧只认 `file_path` + `file_type`；解析侧用 `BaseDocumentParser` + `ParseResult`，无论 PDF 还是 MD，下游 chunk 只消费 `raw_text` 和 `sections`。这对应条目层的 `source_type=file` 统一模型——**入口多样，出口一种**。

### 「异常处理与工程分层」

> 解析器内部捕获库异常，映射为 `error_code` + 用户文案；服务层写状态机 `failed` 和 `error_message`；API 只返回 `parse_status`。日志留后端，前端可展示、可重试，答辩时能画一张 **Parser → Item → UI** 的错误传播图。

---

## 10. Demo 实施顺序（建议）

1. 抽 `schemas/parse.py`，TXT/MD 迁入 `TxtParser` / `MarkdownParser`（行为与现网一致）
2. 接 `pypdf` → PDF ready
3. 接 `python-docx` → docx ready；`.doc` 返回 `LEGACY_DOC`
4. `POST .../parse` 重试 + 上传页文案更新
5. 接入 `chunk_service`（500/50，与技术方案一致）

---

## 验证清单

1. 上传 `.txt` / `.md` → 条目 **可用**，正文与文件一致
2. 上传 `.pdf` / `.docx` → **可用**，`content` 非空；损坏文件 → **失败** + 明确 `error_message`
3. 空 PDF（扫描版）→ **失败**，提示 OCR
4. 条目 `failed` → 重试解析 → `ready`（重试 API 接入后）
