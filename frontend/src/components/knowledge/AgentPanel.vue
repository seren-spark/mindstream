<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { IconRobot } from '@arco-design/web-vue/es/icon'
import AgentGenerateWizard from '@/components/agent/AgentGenerateWizard.vue'
import { archiveAgent, deleteAgent, fetchAgents, publishAgent } from '@/api/agent'
import type { ExpertAgent } from '@/types/agent'
import { ROUTE_NAMES } from '@/utils/constants'

const props = defineProps<{
  knowledgeBaseId: number
}>()

const router = useRouter()
const loading = ref(false)
const agents = ref<ExpertAgent[]>([])
const wizardVisible = ref(false)

const statusMap = {
  draft: { label: '草稿', color: 'orange' },
  published: { label: '已发布', color: 'green' },
  archived: { label: '已归档', color: 'gray' },
} as const

async function loadAgents() {
  loading.value = true
  try {
    const { data } = await fetchAgents(props.knowledgeBaseId, undefined, 1, 50)
    agents.value = data.items
  } catch {
    Message.error('加载专家助手失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadAgents)

function openWizard() {
  wizardVisible.value = true
}

function onWizardDone() {
  wizardVisible.value = false
  loadAgents()
}

function goDetail(agent: ExpertAgent) {
  router.push({
    name: ROUTE_NAMES.AGENT_DETAIL,
    params: { agentId: agent.id },
    query: { kbId: props.knowledgeBaseId },
  })
}

function goChat(agent: ExpertAgent) {
  if (agent.status !== 'published') {
    Message.warning('请先发布 Agent 后再对话')
    return
  }
  router.push({
    name: ROUTE_NAMES.AGENT_CHAT,
    params: { agentId: agent.id },
    query: { kbId: props.knowledgeBaseId },
  })
}

async function handlePublish(agent: ExpertAgent) {
  try {
    await publishAgent(props.knowledgeBaseId, agent.id)
    Message.success('已发布')
    await loadAgents()
  } catch {
    Message.error('发布失败')
  }
}

function handleArchive(agent: ExpertAgent) {
  Modal.warning({
    title: '归档此专家助手？',
    content: '归档后将无法在新对话中使用，历史会话保留。',
    onOk: async () => {
      await archiveAgent(props.knowledgeBaseId, agent.id)
      Message.success('已归档')
      await loadAgents()
    },
  })
}

function handleDelete(agent: ExpertAgent) {
  Modal.warning({
    title: '删除草稿？',
    content: `确定删除「${agent.name}」？此操作不可恢复。`,
    onOk: async () => {
      await deleteAgent(props.knowledgeBaseId, agent.id)
      Message.success('已删除')
      await loadAgents()
    },
  })
}
</script>

<template>
  <div class="agent-panel">
    <div class="agent-panel__toolbar">
      <a-button type="primary" @click="openWizard">
        <template #icon><icon-robot /></template>
        一键生成专家
      </a-button>
    </div>

    <a-spin :loading="loading" style="width: 100%">
      <a-empty v-if="!agents.length && !loading" description="暂无专家助手，点击上方一键生成">
        <a-button type="primary" @click="openWizard">开始生成</a-button>
      </a-empty>

      <div v-else class="agent-panel__grid">
        <div v-for="agent in agents" :key="agent.id" class="agent-card">
          <div class="agent-card__avatar">{{ agent.avatar_value }}</div>
          <div class="agent-card__body">
            <div class="agent-card__head">
              <h4 class="agent-card__name">{{ agent.name }}</h4>
              <a-tag :color="statusMap[agent.status].color" size="small">
                {{ statusMap[agent.status].label }}
              </a-tag>
            </div>
            <p class="agent-card__desc">{{ agent.description || '暂无描述' }}</p>
            <a-space wrap class="agent-card__actions">
              <a-button size="small" @click="goDetail(agent)">详情</a-button>
              <a-button
                v-if="agent.status === 'published'"
                size="small"
                type="primary"
                @click="goChat(agent)"
              >
                对话
              </a-button>
              <a-button v-if="agent.status === 'draft'" size="small" @click="handlePublish(agent)">
                发布
              </a-button>
              <a-button
                v-if="agent.status === 'published'"
                size="small"
                @click="handleArchive(agent)"
              >
                归档
              </a-button>
              <a-button
                v-if="agent.status === 'draft'"
                size="small"
                status="danger"
                @click="handleDelete(agent)"
              >
                删除
              </a-button>
            </a-space>
          </div>
        </div>
      </div>
    </a-spin>

    <AgentGenerateWizard
      v-model:visible="wizardVisible"
      :knowledge-base-id="knowledgeBaseId"
      @done="onWizardDone"
    />
  </div>
</template>

<style scoped>
.agent-panel__toolbar {
  margin-bottom: 20px;
}

.agent-panel__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.agent-card {
  display: flex;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--color-border-2);
  border-radius: var(--ui-radius-md);
  background: var(--color-bg-2);
  transition:
    border-color var(--ui-duration) var(--ui-ease),
    box-shadow var(--ui-duration) var(--ui-ease);
}

.agent-card:hover {
  border-color: rgb(var(--primary-5));
  box-shadow: var(--ui-shadow-sm);
}

.agent-card__avatar {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  border-radius: 12px;
  background: var(--color-fill-2);
}

.agent-card__body {
  flex: 1;
  min-width: 0;
}

.agent-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.agent-card__name {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-1);
}

.agent-card__desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--color-text-3);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-card__actions {
  margin-top: 4px;
}
</style>
