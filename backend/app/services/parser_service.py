from pathlib import Path

TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}


class ParserService:
    @staticmethod
    def can_parse(file_path: str) -> bool:
        return Path(file_path).suffix.lower() in TEXT_EXTENSIONS

    @staticmethod
    def parse_text_file(file_path: str) -> str:
        path = Path(file_path)
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            raise ValueError(f"暂不支持解析 {path.suffix} 格式")

        for encoding in ("utf-8", "utf-8-sig", "gbk"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue

        raise ValueError("无法识别文件编码，请转换为 UTF-8 后重试")

    @staticmethod
    def unsupported_message(file_type: str) -> str:
        if file_type in {"pdf"}:
            return "PDF 解析将在后续版本接入，文件已保存并创建知识条目"
        if file_type in {"doc", "docx"}:
            return "Word 解析将在后续版本接入，文件已保存并创建知识条目"
        return f"暂不支持解析 .{file_type} 格式"

    @staticmethod
    def derive_title(filename: str) -> str:
        stem = Path(filename).stem.strip()
        return stem[:200] if stem else "未命名文档"
