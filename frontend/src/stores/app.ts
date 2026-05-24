import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchPing } from '@/api/ping'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const backendOnline = ref(false)
  const backendVersion = ref('')
  const healthChecking = ref(false)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  async function checkBackendHealth() {
    healthChecking.value = true
    try {
      const { data } = await fetchPing()
      backendOnline.value = data.status === 'ok'
      backendVersion.value = data.version
    } catch {
      backendOnline.value = false
      backendVersion.value = ''
    } finally {
      healthChecking.value = false
    }
  }

  return {
    sidebarCollapsed,
    backendOnline,
    backendVersion,
    healthChecking,
    toggleSidebar,
    checkBackendHealth,
  }
})
