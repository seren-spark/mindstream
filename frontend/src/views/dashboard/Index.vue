<script setup lang="ts">
import { onMounted, watch } from 'vue'
import PageContainer from '@/components/common/PageContainer.vue'
import DashboardFilterBar from '@/components/dashboard/DashboardFilterBar.vue'
import StatOverviewCards from '@/components/dashboard/StatOverviewCards.vue'
import QuestionTrendChart from '@/components/dashboard/QuestionTrendChart.vue'
import KnowledgeHeatRank from '@/components/dashboard/KnowledgeHeatRank.vue'
import UnansweredTable from '@/components/dashboard/UnansweredTable.vue'
import { useDashboardStats } from '@/composables/useDashboardStats'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const { kbId, days, overview, trend, heat, unanswered, loading, errors, refresh } =
  useDashboardStats()

onMounted(() => {
  appStore.checkBackendHealth()
  refresh()
})

watch([kbId, days], () => refresh())
</script>

<template>
  <PageContainer title="概览">
    <a-alert
      v-if="!appStore.backendOnline"
      type="warning"
      style="margin-bottom: 16px"
      title="后端未连接"
      closable
    >
      统计依赖后端 API，请确认 FastAPI 已启动。
    </a-alert>

    <DashboardFilterBar v-model:kb-id="kbId" v-model:days="days" @refresh="refresh" />

    <StatOverviewCards :data="overview" :loading="loading.overview" />

    <a-row :gutter="16">
      <a-col :xs="24" :lg="15">
        <QuestionTrendChart
          :points="trend?.points ?? []"
          :loading="loading.trend"
          :error="errors.trend"
          :period-days="days"
        />
      </a-col>
      <a-col :xs="24" :lg="9">
        <KnowledgeHeatRank
          :items="heat?.items ?? []"
          :loading="loading.heat"
          :error="errors.heat"
        />
      </a-col>
    </a-row>

    <UnansweredTable
      :items="unanswered?.items ?? []"
      :total="unanswered?.total_miss_count ?? 0"
      :loading="loading.unanswered"
      :error="errors.unanswered"
    />
  </PageContainer>
</template>

<style scoped>
:deep(.page-container__body) {
  max-width: 1200px;
}
</style>
