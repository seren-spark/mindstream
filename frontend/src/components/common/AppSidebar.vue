<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { IconDashboard, IconBook, IconMessage, IconBulb } from '@arco-design/web-vue/es/icon'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const menuItems = [
  { key: '/dashboard', title: '概览', icon: IconDashboard },
  { key: '/knowledge', title: '知识库', icon: IconBook },
  { key: '/gaps', title: '知识缺口', icon: IconBulb },
  { key: '/chat', title: '智能问答', icon: IconMessage },
]

const selectedKeys = computed(() => {
  if (route.path.startsWith('/knowledge')) return ['/knowledge']
  if (route.path.startsWith('/gaps')) return ['/gaps']
  return [route.path]
})

function handleMenuClick(key: string) {
  router.push(key)
}
</script>

<template>
  <a-layout-sider
    :collapsed="appStore.sidebarCollapsed"
    collapsible
    :trigger="null"
    :width="220"
    :collapsed-width="48"
    breakpoint="lg"
    class="app-sidebar"
  >
    <div class="app-sidebar__brand">
      <span v-if="!appStore.sidebarCollapsed" class="app-sidebar__brand-text">Knowledge Hub</span>
      <span v-else class="app-sidebar__brand-short">KH</span>
    </div>

    <a-menu
      :selected-keys="selectedKeys"
      :collapsed="appStore.sidebarCollapsed"
      @menu-item-click="handleMenuClick"
    >
      <a-menu-item v-for="item in menuItems" :key="item.key">
        <template #icon>
          <component :is="item.icon" />
        </template>
        {{ item.title }}
      </a-menu-item>
    </a-menu>
  </a-layout-sider>
</template>

<style scoped>
.app-sidebar {
  background: color-mix(in srgb, var(--color-bg-2) 92%, transparent);
  border-right: 1px solid var(--color-border-1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.app-sidebar__brand {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 56px;
  border-bottom: 1px solid var(--color-border-1);
}

.app-sidebar__brand-text {
  font-size: 14px;
  font-weight: 600;
  color: rgb(var(--primary-6));
  letter-spacing: -0.01em;
}

.app-sidebar__brand-short {
  font-size: 13px;
  font-weight: 700;
  color: rgb(var(--primary-6));
}
</style>
