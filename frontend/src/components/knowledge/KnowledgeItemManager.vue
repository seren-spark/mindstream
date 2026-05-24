<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import ItemEditorPanel from '@/components/knowledge-item/ItemEditorPanel.vue'
import ItemListPanel from '@/components/knowledge-item/ItemListPanel.vue'
import { useKnowledgeItemStore } from '@/stores/knowledge-item'
import type { KnowledgeItemListItem } from '@/types/knowledge-item'

const props = defineProps<{
  knowledgeBaseId: number
}>()

const store = useKnowledgeItemStore()

async function loadItems() {
  await store.loadList(props.knowledgeBaseId, true)
}

onMounted(loadItems)

watch(
  () => props.knowledgeBaseId,
  () => {
    store.reset()
    loadItems()
  },
)

onUnmounted(() => {
  store.reset()
})

function confirmLeave(): Promise<boolean> {
  return new Promise((resolve) => {
    Modal.confirm({
      title: '有未保存的更改',
      content: '离开后将丢失当前编辑内容，是否继续？',
      onOk: () => resolve(true),
      onCancel: () => resolve(false),
    })
  })
}

async function handleSelect(item: KnowledgeItemListItem) {
  if (store.isDirty) {
    const confirmed = await confirmLeave()
    if (!confirmed) return
    store.isDirty = false
  }
  store.isCreating = false
  await store.loadDetail(item.id)
  store.populateFormFromCurrent()
}

async function handleCreate() {
  if (store.isDirty) {
    const confirmed = await confirmLeave()
    if (!confirmed) return
    store.isDirty = false
  }
  store.startCreate()
}

function handleSaved(itemId: number) {
  store.selectedId = itemId
  store.populateFormFromCurrent()
}

async function handleDelete() {
  if (!store.current) return
  Modal.warning({
    title: '确认删除条目？',
    content: `删除「${store.current.title}」后不可恢复。`,
    okText: '删除',
    cancelText: '取消',
    onOk: async () => {
      try {
        await store.remove(store.current!.id)
        Message.success('条目已删除')
      } catch {
        Message.error('删除失败，请稍后重试')
      }
    },
  })
}
</script>

<template>
  <div class="item-manager">
    <aside class="item-manager__sidebar">
      <ItemListPanel
        :knowledge-base-id="knowledgeBaseId"
        :selected-id="store.selectedId"
        @select="handleSelect"
        @create="handleCreate"
      />
    </aside>
    <main class="item-manager__main">
      <a-spin :loading="store.detailLoading" style="width: 100%; min-height: 420px">
        <ItemEditorPanel
          :knowledge-base-id="knowledgeBaseId"
          @delete="handleDelete"
          @saved="handleSaved"
        />
      </a-spin>
    </main>
  </div>
</template>

<style scoped>
.item-manager {
  display: grid;
  grid-template-columns: 320px 1fr;
  min-height: 520px;
  border: 1px solid var(--color-border-2);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-bg-1);
}

.item-manager__sidebar {
  min-width: 0;
}

.item-manager__main {
  min-width: 0;
  background: var(--color-bg-2);
}

@media (max-width: 960px) {
  .item-manager {
    grid-template-columns: 1fr;
  }
}
</style>
