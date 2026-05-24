<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { buildHeatOption } from '@/utils/chartOptions'
import type { HeatItem } from '@/types/stats'

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  items: HeatItem[]
  loading?: boolean
  error?: string
}>()

const option = ref(buildHeatOption([]))

watch(
  () => props.items,
  (items) => {
    option.value = buildHeatOption(items)
  },
  { immediate: true },
)

const isEmpty = computed(() => !props.loading && props.items.length === 0)
</script>

<template>
  <a-card class="dash-chart-card" :bordered="false">
    <template #title>
      <div class="chart-head">
        <span>知识热度榜</span>
        <span class="chart-head__hint">被 RAG 引用最多的条目</span>
      </div>
    </template>

    <a-spin :loading="loading" style="width: 100%">
      <a-result v-if="error" status="error" :title="error" />
      <a-empty v-else-if="isEmpty" description="暂无引用记录，问答后将展示热度" />
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
