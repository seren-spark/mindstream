<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { IconDashboard, IconBook, IconMessage } from '@arco-design/web-vue/es/icon'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const menuItems = [
  { key: '/dashboard', title: '概览', icon: IconDashboard },
  { key: '/knowledge', title: '知识库', icon: IconBook },
  { key: '/chat', title: '智能问答', icon: IconMessage },
]

const selectedKeys = computed(() => {
  if (route.path.startsWith('/knowledge')) return ['/knowledge']
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
      <span v-if="!appStore.sidebarCollapsed">Knowledge Hub</span>
      <span v-else>KH</span>
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
  background: var(--color-bg-2);
  border-right: 1px solid var(--color-border-2);
}

.app-sidebar__brand {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 56px;
  font-size: 14px;
  font-weight: 600;
  color: rgb(var(--primary-6));
  border-bottom: 1px solid var(--color-border-2);
}
</style>
