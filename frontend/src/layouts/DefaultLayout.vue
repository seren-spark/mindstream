<script setup lang="ts">
import { onMounted } from 'vue'
import AppHeader from '@/components/common/AppHeader.vue'
import AppSidebar from '@/components/common/AppSidebar.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

onMounted(() => {
  appStore.checkBackendHealth()
})
</script>

<template>
  <a-layout class="default-layout">
    <AppSidebar />
    <a-layout>
      <AppHeader />
      <a-layout-content class="default-layout__content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<style scoped>
.default-layout {
  height: 100vh;
}

.default-layout__content {
  padding: 16px;
  overflow: auto;
  background: var(--color-fill-2);
}
</style>
