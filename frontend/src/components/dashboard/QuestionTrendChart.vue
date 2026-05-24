<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { buildTrendOption } from '@/utils/chartOptions'
import type { TrendPoint } from '@/types/stats'

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  points: TrendPoint[]
  loading?: boolean
  error?: string
  periodDays?: number
}>()

const option = ref(buildTrendOption([]))

watch(
  () => props.points,
  (pts) => {
    option.value = buildTrendOption(pts)
  },
  { immediate: true },
)

const isEmpty = computed(() => !props.loading && props.points.every((p) => p.question_count === 0))
</script>

<template>
  <a-card class="dash-chart-card" :bordered="false">
    <template #title>
      <div class="chart-head">
        <span>每日提问趋势</span>
        <span class="chart-head__hint">近 {{ periodDays ?? 7 }} 日用户提问次数</span>
      </div>
    </template>

    <a-spin :loading="loading" style="width: 100%">
      <a-result v-if="error" status="error" :title="error" />
      <a-empty v-else-if="isEmpty" description="所选时段暂无提问，去发起首次问答吧" />
      <VChart v-else class="chart-box" :option="option" autoresize />
    </a-spin>
  </a-card>
</template>

<style scoped>
.dash-chart-card {
  background: var(--color-bg-1);
  box-shadow: var(--ui-shadow-sm);
  min-height: 320px;
}

.chart-head {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chart-head__hint {
  font-size: 12px;
  font-weight: 400;
  color: var(--color-text-3);
}

.chart-box {
  width: 100%;
  height: 260px;
}
</style>
