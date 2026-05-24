export interface StatsOverview {
  knowledge_base_count: number
  item_count: number
  item_ready_count: number
  question_count_today: number
  question_count_period: number
  hit_rate: number
  hit_rate_delta: number
  period_days: number
  generated_at: string
}

export interface TrendPoint {
  date: string
  question_count: number
  hit_count: number
  miss_count: number
}

export interface StatsTrend {
  period_days: number
  knowledge_base_id: number | null
  points: TrendPoint[]
  total_questions: number
  avg_daily: number
}

export interface HeatItem {
  rank: number
  knowledge_item_id: number
  title: string
  knowledge_base_id: number
  knowledge_base_name: string
  cite_count: number
  unique_questions: number
  last_cited_at: string | null
}

export interface StatsHeat {
  period_days: number
  knowledge_base_id: number | null
  items: HeatItem[]
}

export interface UnansweredItem {
  id?: string | null
  query_text: string
  occurrence_count: number
  last_asked_at: string
  knowledge_base_id: number
  knowledge_base_name: string
  sample_message_id: string
  suggested_action: string
}

export interface StatsUnanswered {
  period_days: number
  knowledge_base_id: number | null
  total_miss_count: number
  items: UnansweredItem[]
}

export interface StatsQuery {
  knowledge_base_id?: number
  days?: number
  limit?: number
}
