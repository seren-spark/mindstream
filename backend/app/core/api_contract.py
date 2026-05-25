"""API 契约常量 — 路由分组、OpenAPI 标签、错误码。

设计原则：
- 成功响应：HTTP 2xx + 直接返回业务 JSON（不包 success/data 外壳）
- 失败响应：HTTP 4xx/5xx + ErrorResponse { detail, code?, errors? }
- 流式响应：HTTP 200 + text/event-stream，错误走 SSE error 事件
"""

from enum import StrEnum


class ApiErrorCode(StrEnum):
    """机器可读错误码，前端可 switch 分支处理。"""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INVALID_STATUS = "INVALID_STATUS"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    PIPELINE_ERROR = "PIPELINE_ERROR"
    STREAM_ERROR = "STREAM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# 逻辑分组 → 实际路由前缀（保持现有 URL，避免破坏性迁移）
API_GROUPS: dict[str, dict[str, str | list[str]]] = {
    "kb": {
        "description": "知识库容器：CRUD、启用/禁用",
        "prefixes": ["/api/knowledge-bases"],
        "tag": "kb",
    },
    "knowledge": {
        "description": "知识条目、切片、向量、检索、Prompt",
        "prefixes": [
            "/api/knowledge-items",
            "/api/knowledge-bases/{id}/items",
            "/api/knowledge-bases/{id}/vectors",
            "/api/knowledge-bases/{id}/search",
            "/api/knowledge-bases/{id}/prompt",
        ],
        "tag": "knowledge",
    },
    "upload": {
        "description": "文档上传与解析触发",
        "prefixes": ["/api/knowledge-bases/{id}/upload"],
        "tag": "upload",
    },
    "chat": {
        "description": "流式问答与会话历史",
        "prefixes": [
            "/api/knowledge-bases/{id}/chat",
            "/api/knowledge-bases/{id}/conversations",
        ],
        "tag": "chat",
    },
    "agent": {
        "description": "专家 Agent 与生成任务",
        "prefixes": ["/api/knowledge-bases/{id}/agents"],
        "tag": "agent",
    },
    "stats": {
        "description": "Dashboard 运营统计",
        "prefixes": ["/api/stats"],
        "tag": "stats",
    },
}

OPENAPI_TAGS: list[dict[str, str]] = [
    {"name": "health", "description": "健康检查"},
    *[
        {"name": meta["tag"], "description": str(meta["description"])}
        for meta in API_GROUPS.values()
    ],
    {"name": "unanswered", "description": "未命中问题沉淀（知识缺口）"},
]

# 流式接口 Content-Type，前端据此选择 fetch 而非 axios
STREAM_CONTENT_TYPE = "text/event-stream"
STREAM_ACCEPT = "text/event-stream"

# SSE 事件 type 字段约定（与 schemas/chat.py 一致）
SSE_EVENT_TYPES = ("start", "token", "references", "done", "error")
