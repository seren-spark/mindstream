<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconLeft } from '@arco-design/web-vue/es/icon'
import PageContainer from '@/components/common/PageContainer.vue'
import { fetchAgent, publishAgent, regenerateAgent, updateAgent } from '@/api/agent'
import type { AgentTone, ExpertAgent } from '@/types/agent'
import { ROUTE_NAMES } from '@/utils/constants'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const agent = ref<ExpertAgent | null>(null)

const agentId = computed(() => route.params.agentId as string)
const knowledgeBaseId = computed(() => Number(route.query.kbId))

const form = ref({
  name: '',
  description: '',
  persona: '',
  tone: 'professional' as AgentTone,
  custom_instructions: '',
  welcome_message: '',
  suggested_questions_text: '',
})

async function loadAgent() {
  if (!knowledgeBaseId.value || Number.isNaN(knowledgeBaseId.value)) {
    Message.error('缺少知识库参数')
    return
  }
  loading.value = true
  try {
    const { data } = await fetchAgent(knowledgeBaseId.value, agentId.value)
    agent.value = data
    form.value = {
      name: data.name,
      description: data.description,
      persona: data.persona,
      tone: data.tone as AgentTone,
      custom_instructions: data.custom_instructions ?? '',
      welcome_message: data.welcome_message,
      suggested_questions_text: data.suggested_questions.join('\n'),
    }
  } catch {
    Message.error('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadAgent)
watch([agentId, knowledgeBaseId], loadAgent)

function handleBack() {
  if (knowledgeBaseId.value) {
    router.push({ name: ROUTE_NAMES.KNOWLEDGE_DETAIL, params: { id: knowledgeBaseId.value } })
  } else {
    router.back()
  }
}

async function handleSave() {
  if (!agent.value) return
  saving.value = true
  const questions = form.value.suggested_questions_text
    .split('\n')
    .map((q) => q.trim())
    .filter(Boolean)
  try {
    const { data } = await updateAgent(knowledgeBaseId.value, agent.value.id, {
      name: form.value.name,
      description: form.value.description,
      persona: form.value.persona,
      tone: form.value.tone,
      custom_instructions: form.value.custom_instructions || null,
      welcome_message: form.value.welcome_message,
      suggested_questions: questions,
    })
    agent.value = data
    Message.success('已保存')
  } catch {
    Message.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handlePublish() {
  if (!agent.value) return
  await handleSave()
  try {
    const { data } = await publishAgent(knowledgeBaseId.value, agent.value.id)
    agent.value = data
    Message.success('已发布')
  } catch {
    Message.error('发布失败')
  }
}

async function handleRegenerate() {
  if (!agent.value) return
  try {
    const { data } = await regenerateAgent(knowledgeBaseId.value, agent.value.id)
    agent.value = data
    await loadAgent()
    Message.success('已重新生成人设')
  } catch {
    Message.error('重新生成失败')
  }
}

function goChat() {
  if (!agent.value || agent.value.status !== 'published') {
    Message.warning('请先发布')
    return
  }
  router.push({
    name: ROUTE_NAMES.AGENT_CHAT,
    params: { agentId: agent.value.id },
    query: { kbId: knowledgeBaseId.value },
  })
}
</script>

<template>
  <PageContainer :title="agent?.name || '专家助手'">
    <template #extra>
      <a-space>
        <a-button @click="handleBack">
          <template #icon><icon-left /></template>
          返回
        </a-button>
        <a-button v-if="agent?.status === 'published'" type="primary" @click="goChat">
          开始对话
        </a-button>
      </a-space>
    </template>

    <a-spin :loading="loading" style="width: 100%; max-width: 720px">
      <template v-if="agent">
        <a-form layout="vertical" :model="form">
          <a-form-item label="名称">
            <a-input v-model="form.name" />
          </a-form-item>
          <a-form-item label="简介">
            <a-textarea v-model="form.description" :auto-size="{ minRows: 2 }" />
          </a-form-item>
          <a-form-item label="人设">
            <a-textarea v-model="form.persona" :auto-size="{ minRows: 4 }" />
          </a-form-item>
          <a-form-item label="语气">
            <a-select v-model="form.tone">
              <a-option value="professional">专业</a-option>
              <a-option value="concise">简洁</a-option>
              <a-option value="detailed">详尽</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="补充说明">
            <a-textarea
              v-model="form.custom_instructions"
              placeholder="可选，最多 1000 字"
              :auto-size="{ minRows: 2 }"
            />
          </a-form-item>
          <a-form-item label="欢迎语">
            <a-textarea v-model="form.welcome_message" :auto-size="{ minRows: 2 }" />
          </a-form-item>
          <a-form-item label="示例问题（每行一个）">
            <a-textarea v-model="form.suggested_questions_text" :auto-size="{ minRows: 3 }" />
          </a-form-item>
        </a-form>

        <a-space style="margin-top: 8px">
          <a-button type="primary" :loading="saving" @click="handleSave">保存</a-button>
          <a-button v-if="agent.status === 'draft'" type="outline" @click="handlePublish">
            保存并发布
          </a-button>
          <a-button @click="handleRegenerate">重新生成人设</a-button>
        </a-space>
      </template>
    </a-spin>
  </PageContainer>
</template>
