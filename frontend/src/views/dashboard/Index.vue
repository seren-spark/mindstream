<script setup lang="ts">
import { onMounted } from 'vue'
import PageContainer from '@/components/common/PageContainer.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

onMounted(() => {
  appStore.checkBackendHealth()
})
</script>

<template>
  <PageContainer title="概览">
    <a-row :gutter="16">
      <a-col :span="8">
        <a-card title="后端状态" :bordered="false">
          <a-result
            v-if="appStore.backendOnline"
            status="success"
            title="联调正常"
            subtitle="前后端通信链路已打通"
          />
          <a-result
            v-else
            status="error"
            title="后端未连接"
            subtitle="请确认 FastAPI 服务已启动在 8000 端口"
          />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="知识文档" :bordered="false">
          <a-statistic title="总数" :value="0" />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="问答会话" :bordered="false">
          <a-statistic title="总数" :value="0" />
        </a-card>
      </a-col>
    </a-row>
  </PageContainer>
</template>
