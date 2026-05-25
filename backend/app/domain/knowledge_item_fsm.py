"""知识条目生命周期状态机 — 单一事实来源（Single Source of Truth）。"""

from enum import StrEnum


class KnowledgeItemStatus(StrEnum):
    """条目在 RAG 流水线中的业务状态，与 UI loading 无关。"""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DISABLED = "disabled"


# 合法状态转移表：current -> {allowed targets}
ALLOWED_TRANSITIONS: dict[KnowledgeItemStatus, frozenset[KnowledgeItemStatus]] = {
    KnowledgeItemStatus.PENDING: frozenset(
        {
            KnowledgeItemStatus.PROCESSING,
            KnowledgeItemStatus.READY,
            KnowledgeItemStatus.FAILED,
            KnowledgeItemStatus.DISABLED,
        }
    ),
    KnowledgeItemStatus.PROCESSING: frozenset(
        {
            KnowledgeItemStatus.READY,
            KnowledgeItemStatus.FAILED,
            KnowledgeItemStatus.DISABLED,
        }
    ),
    KnowledgeItemStatus.READY: frozenset(
        {KnowledgeItemStatus.DISABLED, KnowledgeItemStatus.PROCESSING}
    ),
    KnowledgeItemStatus.FAILED: frozenset(
        {
            KnowledgeItemStatus.PENDING,
            KnowledgeItemStatus.PROCESSING,
            KnowledgeItemStatus.DISABLED,
        }
    ),
    KnowledgeItemStatus.DISABLED: frozenset(
        {KnowledgeItemStatus.PENDING, KnowledgeItemStatus.READY}
    ),
}

# 可被 RAG 检索引用的终态
RETRIEVABLE_STATUSES: frozenset[KnowledgeItemStatus] = frozenset({KnowledgeItemStatus.READY})

# 允许用户/系统触发重试的来源态
RETRYABLE_FROM: frozenset[KnowledgeItemStatus] = frozenset(
    {KnowledgeItemStatus.PENDING, KnowledgeItemStatus.FAILED}
)

# 流水线各阶段的 processing_progress 锚点（0–100）
PIPELINE_PROGRESS = {
    "queued": 0,
    "parsing": 30,
    "chunking": 50,
    "embedding_start": 60,
    "embedding_mid": 70,
    "embedding_write": 85,
    "done": 100,
}


def can_transition(current: KnowledgeItemStatus, target: KnowledgeItemStatus) -> bool:
    if current == target:
        return True
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def assert_transition(current: KnowledgeItemStatus, target: KnowledgeItemStatus) -> None:
    if not can_transition(current, target):
        raise ValueError(f"Cannot transition from '{current.value}' to '{target.value}'")


def is_retrievable(status: KnowledgeItemStatus | str) -> bool:
    return KnowledgeItemStatus(status) in RETRIEVABLE_STATUSES


def is_retryable(status: KnowledgeItemStatus | str) -> bool:
    return KnowledgeItemStatus(status) in RETRYABLE_FROM
