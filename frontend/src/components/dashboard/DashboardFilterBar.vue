<script setup lang="ts">
import { onMounted } from 'vue'
import { useKnowledgeBaseStore } from '@/stores/knowledge-base'

const kbId = defineModel<number | undefined>('kbId')
const days = defineModel<number>('days', { default: 7 })

const emit = defineEmits<{ refresh: [] }>()

const kbStore = useKnowledgeBaseStore()

onMounted(() => {
  if (!kbStore.list.length) kbStore.loadList()
})

const dayOptions = [
  { label: '近 7 天', value: 7 },
  { label: '近 14 天', value: 14 },
  { label: '近 30 天', value: 30 },
]
</script>

<template>
  <div class="dash-filter">
    <p class="dash-filter__desc">知识运营驾驶舱 · 看清热度、趋势与知识缺口</p>
    <a-space wrap>
      <a-select
        v-model="kbId"
        placeholder="全部知识库"
        allow-clear
        style="width: 200px"
        :loading="kbStore.listLoading"
        @change="emit('refresh')"
      >
        <a-option v-for="kb in kbStore.list" :key="kb.id" :value="kb.id" :label="kb.name" />
      </a-select>
      <a-select
        v-model="days"
        :options="dayOptions"
        style="width: 120px"
        @change="emit('refresh')"
      />
      <a-button type="outline" @click="emit('refresh')">刷新</a-button>
    </a-space>
  </div>
</template>

<style scoped>
.dash-filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}

.dash-filter__desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-3);
}
</style>
