<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import PageContainer from '@/components/common/PageContainer.vue'
import ResolveGapDrawer from '@/components/gaps/ResolveGapDrawer.vue'
import {
  dismissUnansweredQuestion,
  fetchUnansweredQuestions,
  updateUnansweredQuestion,
} from '@/api/unanswered'
import { useKnowledgeBaseStore } from '@/stores/knowledge-base'
import { formatDateTime } from '@/utils/format'
import { ROUTE_NAMES } from '@/utils/constants'
import type { UnansweredQuestion, UnansweredStatus } from '@/types/unanswered'
import { REASON_LABELS, STATUS_LABELS } from '@/types/unanswered'

const route = useRoute()
const router = useRouter()
const kbStore = useKnowledgeBaseStore()

const kbId = ref<number | undefined>(route.query.kbId ? Number(route.query.kbId) : undefined)
const statusFilter = ref<UnansweredStatus | ''>('open')
const loading = ref(false)
const items = ref<UnansweredQuestion[]>([])
const total = ref(0)
const page = ref(1)

const resolveVisible = ref(false)
const activeRecord = ref<UnansweredQuestion | null>(null)

const statusTabs = [
  { key: '', label: '全部' },
  { key: 'open', label: '待处理' },
  { key: 'reviewing', label: '处理中' },
  { key: 'resolved', label: '已沉淀' },
  { key: 'dismissed', label: '已忽略' },
] as const

async function loadList() {
  if (!kbId.value) {
    items.value = []
    total.value = 0
    return
  }
  loading.value = true
  try {
    const { data } = await fetchUnansweredQuestions(kbId.value, {
      status: statusFilter.value || undefined,
      page: page.value,
      page_size: 20,
    })
    items.value = data.items
    total.value = data.total
  } catch {
    Message.error('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await kbStore.loadList()
  if (!kbId.value && kbStore.list.length) {
    kbId.value = kbStore.list[0].id
  }
  await loadList()
})

watch([kbId, statusFilter, page], loadList)

function openResolve(record: UnansweredQuestion) {
  activeRecord.value = record
  resolveVisible.value = true
}

async function markReviewing(record: UnansweredQuestion) {
  await updateUnansweredQuestion(record.knowledge_base_id, record.id, { status: 'reviewing' })
  Message.success('已标记为处理中')
  await loadList()
}

function handleDismiss(record: UnansweredQuestion) {
  Modal.warning({
    title: '忽略此问题？',
    content: '忽略后不再出现在待处理列表，历史次数仍保留。',
    onOk: async () => {
      await dismissUnansweredQuestion(record.knowledge_base_id, record.id)
      Message.success('已忽略')
      await loadList()
    },
  })
}

function goItem(record: UnansweredQuestion) {
  if (!record.resolved_item_id) return
  router.push({
    name: ROUTE_NAMES.KNOWLEDGE_ITEMS,
    params: { id: record.knowledge_base_id, itemId: record.resolved_item_id },
  })
}
</script>

<template>
  <PageContainer title="知识缺口">
    <template #extra>
      <a-button type="text" @click="router.push({ name: ROUTE_NAMES.DASHBOARD })"
        >返回概览</a-button
      >
    </template>

    <div class="gaps-intro">
      <p>
        来自真实问答的<strong>未命中问题</strong>，按频次聚合。确认后可一键沉淀为知识条目，形成「使用
        → 补库 → 命中」闭环。
      </p>
    </div>

    <a-space wrap class="gaps-toolbar">
      <a-select
        v-model="kbId"
        placeholder="选择知识库"
        allow-clear
        style="width: 220px"
        :loading="kbStore.listLoading"
      >
        <a-option v-for="kb in kbStore.list" :key="kb.id" :value="kb.id" :label="kb.name" />
      </a-select>
      <a-radio-group v-model="statusFilter" type="button">
        <a-radio v-for="tab in statusTabs" :key="tab.key" :value="tab.key">{{ tab.label }}</a-radio>
      </a-radio-group>
    </a-space>

    <a-spin :loading="loading" style="width: 100%">
      <a-empty v-if="!kbId" description="请先选择知识库" />
      <a-empty v-else-if="!items.length && !loading" description="暂无未命中记录，知识覆盖良好" />
      <a-table v-else :data="items" :pagination="false" row-key="id" class="gaps-table">
        <template #columns>
          <a-table-column title="问题" data-index="query_text" ellipsis tooltip />
          <a-table-column title="次数" data-index="occurrence_count" :width="72" align="center" />
          <a-table-column title="原因" :width="100">
            <template #cell="{ record }">
              <a-tag size="small">{{ REASON_LABELS[record.reason] || record.reason }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="96">
            <template #cell="{ record }">
              <a-tag
                size="small"
                :color="
                  record.status === 'open'
                    ? 'orange'
                    : record.status === 'resolved'
                      ? 'green'
                      : 'gray'
                "
              >
                {{ STATUS_LABELS[record.status as UnansweredStatus] }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="最近提问" :width="168">
            <template #cell="{ record }">{{ formatDateTime(record.last_asked_at) }}</template>
          </a-table-column>
          <a-table-column title="操作" :width="220" align="center">
            <template #cell="{ record }">
              <a-space v-if="record.status === 'open' || record.status === 'reviewing'">
                <a-button type="text" size="small" @click="openResolve(record)">沉淀</a-button>
                <a-button
                  v-if="record.status === 'open'"
                  type="text"
                  size="small"
                  @click="markReviewing(record)"
                >
                  处理中
                </a-button>
                <a-button type="text" size="small" status="warning" @click="handleDismiss(record)">
                  忽略
                </a-button>
              </a-space>
              <a-button
                v-else-if="record.resolved_item_id"
                type="text"
                size="small"
                @click="goItem(record)"
              >
                查看条目
              </a-button>
            </template>
          </a-table-column>
        </template>
      </a-table>

      <a-pagination
        v-if="total > 20"
        v-model:current="page"
        :total="total"
        :page-size="20"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </a-spin>

    <ResolveGapDrawer
      v-model:visible="resolveVisible"
      :record="activeRecord"
      @resolved="loadList"
    />
  </PageContainer>
</template>

<style scoped>
.gaps-intro {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: var(--ui-radius-md);
  background: color-mix(in srgb, rgb(var(--primary-1)) 60%, var(--color-bg-2));
  border: 1px solid color-mix(in srgb, rgb(var(--primary-6)) 12%, transparent);
}

.gaps-intro p {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-2);
  line-height: 1.65;
}

.gaps-toolbar {
  margin-bottom: 16px;
}

.gaps-table :deep(.arco-table-tr) {
  border-left: 3px solid transparent;
}

.gaps-table :deep(.arco-table-tr:hover) {
  border-left-color: rgb(var(--primary-6));
}
</style>
