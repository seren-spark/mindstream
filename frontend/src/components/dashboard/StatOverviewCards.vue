<script setup lang="ts">
import type { StatsOverview } from '@/types/stats'

defineProps<{
  data: StatsOverview | null
  loading?: boolean
}>()

function formatRate(rate: number) {
  return `${(rate * 100).toFixed(1)}%`
}

function formatDelta(delta: number) {
  const pct = (delta * 100).toFixed(1)
  return delta >= 0 ? `+${pct}%` : `${pct}%`
}
</script>

<template>
  <a-row :gutter="[16, 16]" class="stat-cards">
    <a-col :xs="24" :sm="12" :lg="6">
      <a-card class="dash-card" :bordered="false" :loading="loading">
        <a-statistic title="知识库" :value="data?.knowledge_base_count ?? 0">
          <template #suffix>
            <span class="stat-hint">个</span>
          </template>
        </a-statistic>
        <p class="stat-desc">平台管理的知识库规模</p>
      </a-card>
    </a-col>
    <a-col :xs="24" :sm="12" :lg="6">
      <a-card class="dash-card" :bordered="false" :loading="loading">
        <a-statistic title="知识条目" :value="data?.item_ready_count ?? 0">
          <template #suffix>
            <span class="stat-hint">/ {{ data?.item_count ?? 0 }} 就绪</span>
          </template>
        </a-statistic>
        <p class="stat-desc">可参与检索的文档条目</p>
      </a-card>
    </a-col>
    <a-col :xs="24" :sm="12" :lg="6">
      <a-card class="dash-card" :bordered="false" :loading="loading">
        <a-statistic title="今日提问" :value="data?.question_count_today ?? 0">
          <template #suffix>
            <span class="stat-hint">次</span>
          </template>
        </a-statistic>
        <p class="stat-desc">
          近 {{ data?.period_days ?? 7 }} 日共 {{ data?.question_count_period ?? 0 }} 次
        </p>
      </a-card>
    </a-col>
    <a-col :xs="24" :sm="12" :lg="6">
      <a-card class="dash-card" :bordered="false" :loading="loading">
        <div class="rate-block">
          <div class="rate-label">RAG 命中率</div>
          <div class="rate-value">{{ formatRate(data?.hit_rate ?? 0) }}</div>
        </div>
        <p class="stat-desc">
          较上期
          <span :class="(data?.hit_rate_delta ?? 0) >= 0 ? 'delta-up' : 'delta-down'">
            {{ formatDelta(data?.hit_rate_delta ?? 0) }}
          </span>
          · 有引用依据的回答占比
        </p>
      </a-card>
    </a-col>
  </a-row>
</template>

<style scoped>
.rate-block {
  margin-bottom: 4px;
}

.rate-label {
  font-size: 14px;
  color: var(--color-text-2);
  margin-bottom: 4px;
}

.rate-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-1);
  letter-spacing: -0.02em;
}

.stat-cards {
  margin-bottom: 16px;
}

.dash-card {
  height: 100%;
  background: var(--color-bg-1);
  box-shadow: var(--ui-shadow-sm);
  transition:
    transform var(--ui-duration) var(--ui-ease),
    box-shadow var(--ui-duration) var(--ui-ease);
}

.dash-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--ui-shadow-md);
}

.stat-hint {
  font-size: 13px;
  color: var(--color-text-3);
  margin-left: 4px;
}

.stat-desc {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--color-text-3);
  line-height: 1.5;
}

.delta-up {
  color: rgb(var(--green-6));
}

.delta-down {
  color: rgb(var(--orange-6));
}

:deep(.arco-statistic-value) {
  font-weight: 600;
  letter-spacing: -0.02em;
}
</style>
