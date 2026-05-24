<script setup lang="ts">
import { useRouter } from 'vue-router'
import { formatDateTime } from '@/utils/format'
import { ROUTE_NAMES } from '@/utils/constants'
import type { UnansweredItem } from '@/types/stats'

defineProps<{
  items: UnansweredItem[]
  total: number
  loading?: boolean
  error?: string
}>()

const router = useRouter()

function goAll(kbId?: number) {
  router.push({
    name: ROUTE_NAMES.KNOWLEDGE_GAPS,
    query: kbId ? { kbId: String(kbId) } : undefined,
  })
}

function goResolve(record: UnansweredItem) {
  router.push({
    name: ROUTE_NAMES.KNOWLEDGE_GAPS,
    query: { kbId: String(record.knowledge_base_id) },
  })
}
</script>

<template>
  <a-card class="dash-table-card" :bordered="false">
    <template #title>
      <div class="chart-head">
        <span>未命中问题 · 待补知识</span>
        <span class="chart-head__hint">检索无有效依据，共 {{ total }} 次未命中</span>
      </div>
    </template>
    <template #extra>
      <a-button type="text" size="small" @click="goAll()">查看全部</a-button>
    </template>

    <a-spin :loading="loading" style="width: 100%">
      <a-result v-if="error" status="error" :title="error" />
      <a-empty v-else-if="!items.length" description="暂无未命中记录，知识库覆盖良好" />
      <a-table v-else :data="items" :pagination="false" row-key="query_text" size="medium">
        <template #columns>
          <a-table-column title="问题" data-index="query_text" ellipsis tooltip />
          <a-table-column title="重复" data-index="occurrence_count" :width="80" align="center" />
          <a-table-column title="知识库" data-index="knowledge_base_name" :width="140" ellipsis />
          <a-table-column title="最近提问" :width="168">
            <template #cell="{ record }">
              {{ formatDateTime(record.last_asked_at) }}
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="120" align="center">
            <template #cell="{ record }">
              <a-button type="text" size="small" @click="goResolve(record)">去沉淀</a-button>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-spin>
  </a-card>
</template>

<style scoped>
.dash-table-card {
  margin-top: 16px;
  background: var(--color-bg-1);
  box-shadow: var(--ui-shadow-sm);
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
</style>
