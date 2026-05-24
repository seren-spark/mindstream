export type UnansweredStatus = 'open' | 'reviewing' | 'resolved' | 'dismissed'

export type UnansweredReason = 'no_citations' | 'reject_phrase' | 'low_score' | 'no_hits'

export interface UnansweredQuestion {
  id: string
  knowledge_base_id: number
  query_text: string
  occurrence_count: number
  first_asked_at: string
  last_asked_at: string
  status: UnansweredStatus
  reason: UnansweredReason | string
  top_score: number | null
  sample_user_message_id: string | null
  sample_assistant_message_id: string | null
  suggested_title: string | null
  suggested_summary: string | null
  resolved_item_id: number | null
  created_at: string
  updated_at: string
}

export interface UnansweredResolvePayload {
  title?: string
  content?: string
  summary?: string
}

export interface UnansweredResolveResult {
  unanswered: UnansweredQuestion
  knowledge_item_id: number
}

export interface PaginatedUnanswered {
  items: UnansweredQuestion[]
  total: number
  page: number
  page_size: number
}

export const REASON_LABELS: Record<string, string> = {
  no_citations: '无引用',
  reject_phrase: '拒答',
  low_score: '低分检索',
  no_hits: '无检索结果',
}

export const STATUS_LABELS: Record<UnansweredStatus, string> = {
  open: '待处理',
  reviewing: '处理中',
  resolved: '已沉淀',
  dismissed: '已忽略',
}
