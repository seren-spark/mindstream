<script setup lang="ts">
import { computed, onMounted, toRef, watch } from 'vue'
import { useItemStatusPolling } from '@/composables/useItemStatusPolling'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { IconLeft } from '@arco-design/web-vue/es/icon'
import PageContainer from '@/components/common/PageContainer.vue'
import ItemEditorPanel from '@/components/knowledge-item/ItemEditorPanel.vue'
import ItemListPanel from '@/components/knowledge-item/ItemListPanel.vue'
import { useKnowledgeBaseStore } from '@/stores/knowledge-base'
import { useKnowledgeItemStore } from '@/stores/knowledge-item'
import type { KnowledgeItemListItem } from '@/types/knowledge-item'
import { ROUTE_NAMES } from '@/utils/constants'

const route = useRoute()
const router = useRouter()
const baseStore = useKnowledgeBaseStore()
const itemStore = useKnowledgeItemStore()

const knowledgeBaseId = computed(() => Number(route.params.id))
const itemIdParam = computed(() => route.params.itemId as string | undefined)

useItemStatusPolling({
  list: toRef(itemStore, 'list'),
  current: toRef(itemStore, 'current'),
  onDetailUpdate: (item) => {
    itemStore.current = item
    if (itemStore.selectedId === item.id) {
      itemStore.populateFormFromCurrent()
    }
  },
  onListSync: (item) => itemStore.syncListItem(item),
})

async function initPage() {
  if (Number.isNaN(knowledgeBaseId.value)) return

  itemStore.reset()
  await baseStore.loadDetail(knowledgeBaseId.value)
  await itemStore.loadList(knowledgeBaseId.value, true)

  if (itemIdParam.value === 'new') {
    itemStore.startCreate()
  } else if (itemIdParam.value) {
    const id = Number(itemIdParam.value)
    if (!Number.isNaN(id)) {
      await itemStore.loadDetail(id)
      itemStore.populateFormFromCurrent()
    }
  }
}

onMounted(initPage)

watch(itemIdParam, async (value) => {
  if (value === 'new') {
    itemStore.startCreate()
    return
  }
  if (!value) {
    itemStore.cancelEdit()
    return
  }
  const id = Number(value)
  if (!Number.isNaN(id)) {
    await itemStore.loadDetail(id)
    itemStore.populateFormFromCurrent()
  }
})

function navigateToItem(id: number | 'new' | null) {
  if (id === null) {
    router.push({ name: ROUTE_NAMES.KNOWLEDGE_ITEMS, params: { id: knowledgeBaseId.value } })
    return
  }
  router.push({
    name: ROUTE_NAMES.KNOWLEDGE_ITEMS,
    params: { id: knowledgeBaseId.value, itemId: String(id) },
  })
}

async function handleSelect(item: KnowledgeItemListItem) {
  if (itemStore.isDirty) {
    const confirmed = await confirmLeave()
    if (!confirmed) return
  }
  navigateToItem(item.id)
}

async function handleCreate() {
  if (itemStore.isDirty) {
    const confirmed = await confirmLeave()
    if (!confirmed) return
  }
  itemStore.startCreate()
  navigateToItem('new')
}

function handleSaved(itemId: number) {
  navigateToItem(itemId)
  itemStore.populateFormFromCurrent()
}

async function handleDelete() {
  if (!itemStore.current) return
  Modal.warning({
    title: '确认删除条目？',
    content: `删除「${itemStore.current.title}」后不可恢复。`,
    okText: '删除',
    cancelText: '取消',
    onOk: async () => {
      try {
        await itemStore.remove(itemStore.current!.id)
        Message.success('条目已删除')
        navigateToItem(null)
      } catch {
        Message.error('删除失败')
      }
    },
  })
}

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

function handleBack() {
  router.push({ name: ROUTE_NAMES.KNOWLEDGE_DETAIL, params: { id: knowledgeBaseId.value } })
}

onBeforeRouteLeave(async () => {
  if (!itemStore.isDirty) return true
  return confirmLeave()
})
</script>

<template>
  <PageContainer
    :title="baseStore.current?.name ? `${baseStore.current.name} / 知识条目` : '知识条目'"
  >
    <template #extra>
      <a-button @click="handleBack">
        <template #icon><icon-left /></template>
        返回知识库
      </a-button>
    </template>

    <div class="items-layout">
      <aside class="items-layout__sidebar">
        <ItemListPanel
          :knowledge-base-id="knowledgeBaseId"
          :selected-id="itemStore.selectedId"
          @select="handleSelect"
          @create="handleCreate"
        />
      </aside>
      <main class="items-layout__main">
        <a-spin :loading="itemStore.detailLoading" style="width: 100%; min-height: 400px">
          <ItemEditorPanel
            :knowledge-base-id="knowledgeBaseId"
            @delete="handleDelete"
            @saved="handleSaved"
          />
        </a-spin>
      </main>
    </div>
  </PageContainer>
</template>

<style scoped>
.items-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  min-height: calc(100vh - 180px);
  border: 1px solid var(--color-border-1);
  border-radius: var(--ui-radius-lg);
  overflow: hidden;
  background: var(--color-bg-1);
  box-shadow: var(--ui-shadow-sm);
}

.items-layout__sidebar {
  min-width: 0;
}

.items-layout__main {
  min-width: 0;
  background: var(--color-bg-2);
}

@media (max-width: 960px) {
  .items-layout {
    grid-template-columns: 1fr;
  }
}
</style>
