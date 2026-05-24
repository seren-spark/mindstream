import { reactive, ref } from 'vue'
import {
  fetchStatsHeat,
  fetchStatsOverview,
  fetchStatsTrend,
  fetchStatsUnanswered,
} from '@/api/stats'
import type { StatsHeat, StatsOverview, StatsTrend, StatsUnanswered } from '@/types/stats'

export function useDashboardStats() {
  const kbId = ref<number | undefined>()
  const days = ref(7)

  const overview = ref<StatsOverview | null>(null)
  const trend = ref<StatsTrend | null>(null)
  const heat = ref<StatsHeat | null>(null)
  const unanswered = ref<StatsUnanswered | null>(null)

  const loading = reactive({
    overview: false,
    trend: false,
    heat: false,
    unanswered: false,
  })

  const errors = reactive({
    overview: '',
    trend: '',
    heat: '',
    unanswered: '',
  })

  function queryParams() {
    return {
      knowledge_base_id: kbId.value,
      days: days.value,
    }
  }

  async function refresh() {
    const params = queryParams()
    loading.overview = true
    loading.trend = true
    loading.heat = true
    loading.unanswered = true

    const [o, t, h, u] = await Promise.allSettled([
      fetchStatsOverview(params),
      fetchStatsTrend(params),
      fetchStatsHeat({ ...params, days: Math.max(days.value, 7) }),
      fetchStatsUnanswered({ ...params, days: Math.max(days.value, 7) }),
    ])

    if (o.status === 'fulfilled') {
      overview.value = o.value.data
      errors.overview = ''
    } else {
      errors.overview = '概览数据加载失败'
    }
    loading.overview = false

    if (t.status === 'fulfilled') {
      trend.value = t.value.data
      errors.trend = ''
    } else {
      errors.trend = '趋势数据加载失败'
    }
    loading.trend = false

    if (h.status === 'fulfilled') {
      heat.value = h.value.data
      errors.heat = ''
    } else {
      errors.heat = '热度数据加载失败'
    }
    loading.heat = false

    if (u.status === 'fulfilled') {
      unanswered.value = u.value.data
      errors.unanswered = ''
    } else {
      errors.unanswered = '未命中数据加载失败'
    }
    loading.unanswered = false
  }

  return {
    kbId,
    days,
    overview,
    trend,
    heat,
    unanswered,
    loading,
    errors,
    refresh,
  }
}
