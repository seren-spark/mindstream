<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { IconMenuFold, IconMenuUnfold, IconRefresh } from '@arco-design/web-vue/es/icon'

const route = useRoute()
const appStore = useAppStore()

const breadcrumbs = computed(() => {
  const matched = route.matched.filter((item) => item.meta?.title)
  return matched.map((item) => ({
    title: item.meta.title as string,
    path: item.path,
  }))
})

async function handleRefreshHealth() {
  await appStore.checkBackendHealth()
}
</script>

<template>
  <a-layout-header class="app-header">
    <div class="app-header__left">
      <a-button type="text" class="app-header__trigger" @click="appStore.toggleSidebar()">
        <icon-menu-unfold v-if="appStore.sidebarCollapsed" />
        <icon-menu-fold v-else />
      </a-button>
      <span class="app-header__logo">AI 知识库</span>
      <a-breadcrumb v-if="breadcrumbs.length" class="app-header__breadcrumb">
        <a-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
          {{ item.title }}
        </a-breadcrumb-item>
      </a-breadcrumb>
    </div>

    <div class="app-header__right">
      <a-space>
        <a-tag :color="appStore.backendOnline ? 'green' : 'red'" class="app-header__status">
          <template v-if="appStore.healthChecking">检测中...</template>
          <template v-else-if="appStore.backendOnline">
            后端已连接 v{{ appStore.backendVersion }}
          </template>
          <template v-else>后端未连接</template>
        </a-tag>
        <a-button
          type="text"
          size="small"
          :loading="appStore.healthChecking"
          @click="handleRefreshHealth"
        >
          <template #icon><icon-refresh /></template>
        </a-button>
      </a-space>
    </div>
  </a-layout-header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 16px;
  background: var(--color-bg-2);
  border-bottom: 1px solid var(--color-border-2);
}

.app-header__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.app-header__trigger {
  font-size: 18px;
}

.app-header__logo {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.app-header__breadcrumb {
  margin-left: 8px;
}

.app-header__right {
  flex-shrink: 0;
}

.app-header__status {
  cursor: default;
}
</style>
