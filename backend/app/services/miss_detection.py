"""未命中判定 — 规则组合（Demo）。"""

from __future__ import annotations

from app.schemas.retrieval import RetrievalHit

MISS_PHRASE = "无法找到相关信息"
DEFAULT_SCORE_THRESHOLD = 0.35


def normalize_query(text: str) -> str:
    return text.strip().lower().replace("\n", " ")[:500]


def classify_miss(
    *,
    query: str,
    hits: list[RetrievalHit],
    citations: list | None,
    assistant_content: str,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
) -> tuple[bool, str, float | None]:
    """返回 (is_miss, reason, top_score)。"""
    if not query.strip():
        return False, "", None

    top_score = max((h.score for h in hits), default=None) if hits else None

    if citations and len(citations) > 0:
        return False, "", top_score

    content = assistant_content or ""
    if MISS_PHRASE in content:
        return True, "reject_phrase", top_score

    if not hits:
        return True, "no_hits", top_score

    if top_score is not None and top_score < score_threshold:
        return True, "low_score", top_score

    return True, "no_citations", top_score


def suggest_title(query: str) -> str:
    text = query.strip().replace("\n", " ")
    return text[:80] + ("…" if len(text) > 80 else "")


def suggest_summary(query: str, assistant_content: str) -> str:
    parts = [f"用户问题：{query.strip()[:300]}"]
    if assistant_content and MISS_PHRASE in assistant_content:
        parts.append("系统未能从现有知识库检索到足够依据，需补充对应说明。")
    return "\n\n".join(parts)
