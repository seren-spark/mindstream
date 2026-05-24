<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Modal, Message } from '@arco-design/web-vue'
import { IconPlus, IconRefresh, IconSearch } from '@arco-design/web-vue/es/icon'
import PageContainer from '@/components/common/PageContainer.vue'
import KnowledgeBaseCard from '@/components/knowledge/KnowledgeBaseCard.vue'
import KnowledgeBaseFormDrawer from '@/components/knowledge/KnowledgeBaseFormDrawer.vue'
import { useKnowledgeBaseStore } from '@/stores/knowledge-base'
import type { KnowledgeBase } from '@/types/knowledge-base'
import { ROUTE_NAMES } from '@/utils/constants'

const router = useRouter()
const store = useKnowledgeBaseStore()
const searchInput = ref(store.keyword)

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '启用', value: 'active' },
  { label: '禁用', value: 'disabled' },
]

const sortOptions = [
  { label: '最新创建', value: 'created_at_desc' },
  { label: '最早创建', value: 'created_at_asc' },
  { label: '名称 A-Z', value: 'name_asc' },
]

onMounted(() => {
  store.loadList()
})

watch(
  () => store.page,
  () => store.loadList(),
)

watch(
  () => store.statusFilter,
  () => store.loadList(),
)

watch(
  () => store.sort,
  () => store.loadList(),
)

function handleSearch() {
  store.setKeyword(searchInput.value)
  store.loadList()
}

function handleReset() {
  searchInput.value = ''
  store.setKeyword('')
  store.setStatusFilter('')
  store.setSort('created_at_desc')
  store.setPage(1)
  store.loadList(true)
}

function handleEnter(item: KnowledgeBase) {
  router.push({ name: ROUTE_NAMES.KNOWLEDGE_DETAIL, params: { id: item.id } })
}

function handleDelete(item: KnowledgeBase) {
  Modal.warning({
    title: '确认删除知识库？',
    content: `删除「${item.name}」后不可恢复，关联文档与向量数据将在后续模块中一并清理。`,
    okText: '确认删除',
    cancelText: '取消',
    onOk: async () => {
      try {
        await store.remove(item.id)
        Message.success('知识库已删除')
      } catch {
        Message.error('删除失败，请稍后重试')
      }
    },
  })
}
</script>

<template>
  <PageContainer title="知识库管理">
    <template #extra>
      <a-button type="primary" @click="store.openCreateDrawer()">
        <template #icon><icon-plus /></template>
        新建知识库
      </a-button>
    </template>

    <div class="kb-toolbar ui-toolbar">
      <a-input-search
        v-model="searchInput"
        allow-clear
        placeholder="搜索名称或描述"
        style="width: 280px"
        @search="handleSearch"
        @clear="handleSearch"
        @press-enter="handleSearch"
      >
        <template #prefix><icon-search /></template>
      </a-input-search>

      <a-select
        v-model="store.statusFilter"
        :options="statusOptions"
        placeholder="状态"
        style="width: 140px"
        allow-clear
      />

      <a-select v-model="store.sort" :options="sortOptions" style="width: 160px" />

      <a-button @click="handleReset">重置</a-button>
      <a-button :loading="store.listLoading" @click="store.loadList(true)">
        <template #icon><icon-refresh /></template>
        刷新
      </a-button>
    </div>

    <a-alert
      v-if="store.listError"
      type="error"
      :title="store.listError"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #action>
        <a-button size="mini" @click="store.loadList(true)">重试</a-button>
      </template>
    </a-alert>

    <a-spin :loading="store.listLoading" style="width: 100%; min-height: 240px">
      <a-empty
        v-if="!store.listLoading && store.list.length === 0"
        description="还没有知识库，先创建一个吧"
      >
        <a-button type="primary" @click="store.openCreateDrawer()">新建知识库</a-button>
      </a-empty>

      <TransitionGroup v-else name="ui-stagger" tag="div" class="kb-grid">
        <div
          v-for="(item, i) in store.list"
          :key="item.id"
          class="kb-grid__item"
          :style="{ '--stagger': i }"
        >
          <KnowledgeBaseCard
            :item="item"
            @enter="handleEnter"
            @edit="store.openEditDrawer"
            @delete="handleDelete"
          />
        </div>
      </TransitionGroup>
    </a-spin>

    <div v-if="store.total > 0" class="kb-pagination">
      <a-pagination
        :current="store.page"
        :total="store.total"
        :page-size="store.pageSize"
        show-total
        show-jumper
        @change="store.setPage"
      />
    </div>

    <KnowledgeBaseFormDrawer />
  </PageContainer>
</template>

<style scoped>
.ui-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 18px;
  padding: 14px 16px;
  background: var(--color-fill-1);
  border-radius: var(--ui-radius-md);
  border: 1px solid var(--color-border-1);
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.kb-grid__item {
  min-width: 0;
}

.ui-stagger-enter-active {
  transition-delay: calc(min(var(--stagger, 0), 8) * 0.05s);
}

.kb-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 8px;
}
</style>
