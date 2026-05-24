<script setup lang="ts">
import { ref, watch } from 'vue'
import ItemListRow from '@/components/knowledge-item/ItemListRow.vue'
import { useKnowledgeItemStore } from '@/stores/knowledge-item'
import type { KnowledgeItemListItem } from '@/types/knowledge-item'

const props = defineProps<{
  knowledgeBaseId: number
  selectedId?: number | null
}>()

const emit = defineEmits<{
  select: [item: KnowledgeItemListItem]
  create: []
}>()

const store = useKnowledgeItemStore()
const searchInput = ref(store.keyword)

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '可用', value: 'ready' },
  { label: '失败', value: 'failed' },
  { label: '已禁用', value: 'disabled' },
]

watch(
  () => store.statusFilter,
  () => store.loadList(props.knowledgeBaseId),
)

function handleSearch() {
  store.setKeyword(searchInput.value)
  store.loadList(props.knowledgeBaseId)
}
</script>

<template>
  <div class="item-list-panel">
    <div class="item-list-panel__toolbar">
      <a-input-search
        v-model="searchInput"
        allow-clear
        placeholder="搜索标题/内容"
        size="small"
        @search="handleSearch"
        @clear="handleSearch"
      />
      <a-select
        v-model="store.statusFilter"
        :options="statusOptions"
        size="small"
        placeholder="状态"
        style="width: 100%; margin-top: 8px"
      />
      <a-button type="primary" long size="small" style="margin-top: 8px" @click="emit('create')">
        新建条目
      </a-button>
    </div>

    <a-alert
      v-if="store.listError"
      type="error"
      :title="store.listError"
      banner
      closable
      style="margin: 8px 0"
    />

    <a-spin :loading="store.listLoading" style="flex: 1; overflow: hidden">
      <a-empty
        v-if="!store.listLoading && !store.list.length"
        description="暂无知识条目"
        style="margin-top: 40px"
      />

      <div v-else class="item-list-panel__list">
        <ItemListRow
          v-for="item in store.list"
          :key="item.id"
          :item="item"
          :active="props.selectedId === item.id"
          @select="emit('select', $event)"
        />
      </div>
    </a-spin>
  </div>
</template>

<style scoped>
.item-list-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-right: 1px solid var(--color-border-2);
  background: var(--color-bg-2);
}

.item-list-panel__toolbar {
  padding: 12px;
  border-bottom: 1px solid var(--color-border-2);
}

.item-list-panel__list {
  overflow: auto;
  max-height: calc(100vh - 280px);
}
</style>
