import http from './index'
import type {
  StatsHeat,
  StatsOverview,
  StatsQuery,
  StatsTrend,
  StatsUnanswered,
} from '@/types/stats'

function buildParams(query?: StatsQuery) {
  return {
    knowledge_base_id: query?.knowledge_base_id,
    days: query?.days,
    limit: query?.limit,
  }
}

export function fetchStatsOverview(query?: StatsQuery) {
  return http.get<StatsOverview>('/stats/overview', { params: buildParams(query) })
}

export function fetchStatsTrend(query?: StatsQuery) {
  return http.get<StatsTrend>('/stats/trend', { params: buildParams(query) })
}

export function fetchStatsHeat(query?: StatsQuery) {
  return http.get<StatsHeat>('/stats/heat', {
    params: { ...buildParams(query), limit: query?.limit ?? 10 },
  })
}

export function fetchStatsUnanswered(query?: StatsQuery) {
  return http.get<StatsUnanswered>('/stats/unanswered', {
    params: { ...buildParams(query), limit: query?.limit ?? 20 },
  })
}
