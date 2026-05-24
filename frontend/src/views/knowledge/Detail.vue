<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { IconEdit, IconLeft } from '@arco-design/web-vue/es/icon'
import PageContainer from '@/components/common/PageContainer.vue'
import KnowledgeBaseFormDrawer from '@/components/knowledge/KnowledgeBaseFormDrawer.vue'
import KnowledgeItemManager from '@/components/knowledge/KnowledgeItemManager.vue'
import { useKnowledgeBaseStore } from '@/stores/knowledge-base'
import { ROUTE_NAMES } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const store = useKnowledgeBaseStore()

const knowledgeBaseId = computed(() => Number(route.params.id))

const statusMap = {
  active: { label: '启用', color: 'green' },
  disabled: { label: '禁用', color: 'gray' },
} as const

async function loadCurrentDetail() {
  if (Number.isNaN(knowledgeBaseId.value)) {
    store.detailError = '无效的知识库 ID'
    return
  }
  await store.loadDetail(knowledgeBaseId.value)
}

onMounted(loadCurrentDetail)

watch(knowledgeBaseId, loadCurrentDetail)

function handleBack() {
  router.push({ name: ROUTE_NAMES.KNOWLEDGE_LIST })
}

function handleDelete() {
  if (!store.current) return
  Modal.warning({
    title: '确认删除知识库？',
    content: `删除「${store.current.name}」后不可恢复。`,
    okText: '确认删除',
    cancelText: '取消',
    onOk: async () => {
      try {
        await store.remove(store.current!.id)
        Message.success('知识库已删除')
        handleBack()
      } catch {
        Message.error('删除失败，请稍后重试')
      }
    },
  })
}
</script>

<template>
  <PageContainer :title="store.current?.name || '知识库详情'">
    <template #extra>
      <a-space>
        <a-button @click="handleBack">
          <template #icon><icon-left /></template>
          返回列表
        </a-button>
        <a-button v-if="store.current" @click="store.openEditDrawer(store.current)">
          <template #icon><icon-edit /></template>
          编辑
        </a-button>
        <a-button v-if="store.current" status="danger" @click="handleDelete"> 删除 </a-button>
      </a-space>
    </template>

    <a-spin :loading="store.detailLoading" style="width: 100%">
      <a-result
        v-if="store.detailError"
        status="error"
        :title="store.detailError"
        subtitle="请返回列表重新选择知识库"
      >
        <template #extra>
          <a-button type="primary" @click="handleBack">返回列表</a-button>
        </template>
      </a-result>

      <template v-else-if="store.current">
        <a-descriptions :column="2" bordered size="large" style="margin-bottom: 20px">
          <a-descriptions-item label="名称">{{ store.current.name }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="statusMap[store.current.status].color">
              {{ statusMap[store.current.status].label }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="描述" :span="2">
            {{ store.current.description || '暂无描述' }}
          </a-descriptions-item>
          <a-descriptions-item label="标签" :span="2">
            <a-space v-if="store.current.tags.length" wrap>
              <a-tag v-for="tag in store.current.tags" :key="tag" color="arcoblue">
                {{ tag }}
              </a-tag>
            </a-space>
            <span v-else class="text-muted">暂无标签</span>
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ formatDateTime(store.current.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="更新时间">
            {{ formatDateTime(store.current.updated_at) }}
          </a-descriptions-item>
        </a-descriptions>

        <a-tabs default-active-key="documents">
          <a-tab-pane key="documents" title="知识条目">
            <KnowledgeItemManager :knowledge-base-id="knowledgeBaseId" />
          </a-tab-pane>
          <a-tab-pane key="vectors" title="向量状态">
            <a-empty description="向量化状态将在 ChromaDB 模块中展示" />
          </a-tab-pane>
          <a-tab-pane key="chat" title="关联问答">
            <a-empty description="可在此知识库范围内发起 RAG 对话（后续模块）">
              <a-button type="primary" @click="router.push({ name: ROUTE_NAMES.CHAT })">
                前往问答
              </a-button>
            </a-empty>
          </a-tab-pane>
        </a-tabs>
      </template>
    </a-spin>

    <KnowledgeBaseFormDrawer />
  </PageContainer>
</template>

<style scoped>
.text-muted {
  color: var(--color-text-3);
}
</style>
