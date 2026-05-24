<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import AppSidebar from '@/components/common/AppSidebar.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const route = useRoute()
const isChatPage = computed(() => route.path.startsWith('/chat'))

onMounted(() => {
  appStore.checkBackendHealth()
})
</script>

<template>
  <a-layout class="default-layout">
    <AppSidebar />
    <a-layout class="default-layout__main">
      <AppHeader />
      <a-layout-content
        class="default-layout__content"
        :class="{ 'default-layout__content--chat': isChatPage }"
      >
        <router-view v-slot="{ Component }">
          <Transition :name="isChatPage ? 'ui-fade' : 'ui-page'" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </router-view>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<style scoped>
.default-layout {
  height: 100vh;
}

.default-layout__main {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.default-layout__content {
  flex: 1;
  min-height: 0;
  padding: 18px 20px;
  overflow: auto;
}

.default-layout__content--chat {
  padding: 0;
  overflow: hidden;
}
</style>
