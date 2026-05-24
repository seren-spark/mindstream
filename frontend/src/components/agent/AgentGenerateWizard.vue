<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { fetchAgentGenerateJob, startAgentGenerate } from '@/api/agent'
import type { AgentGenerationJob } from '@/types/agent'
import { ROUTE_NAMES } from '@/utils/constants'

const props = defineProps<{
  knowledgeBaseId: number
}>()

const visible = defineModel<boolean>('visible', { default: false })

const emit = defineEmits<{
  done: []
}>()

const router = useRouter()
const step = ref<'idle' | 'running' | 'preview' | 'error'>('idle')
const job = ref<AgentGenerationJob | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const stageLabel = computed(() => {
  const s = job.value?.stage
  if (s === 'sampling') return '采样知识库'
  if (s === 'composing') return '组装人设'
  if (s === 'done') return '保存完成'
  return job.value?.progress_message || '准备中'
})

function stopPoll() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function pollJob(jobId: string) {
  const { data } = await fetchAgentGenerateJob(props.knowledgeBaseId, jobId)
  job.value = data
  if (data.status === 'succeeded' && data.agent) {
    step.value = 'preview'
    stopPoll()
  } else if (data.status === 'failed') {
    step.value = 'error'
    stopPoll()
  }
}

async function startGenerate() {
  step.value = 'running'
  job.value = null
  try {
    const { data } = await startAgentGenerate(props.knowledgeBaseId)
    job.value = data
    stopPoll()
    pollTimer = setInterval(() => {
      pollJob(data.id).catch(() => {
        step.value = 'error'
        stopPoll()
      })
    }, 1500)
    await pollJob(data.id)
  } catch {
    step.value = 'error'
    Message.error('启动生成失败')
  }
}

function goEdit() {
  if (!job.value?.agent) return
  visible.value = false
  emit('done')
  router.push({
    name: ROUTE_NAMES.AGENT_DETAIL,
    params: { agentId: job.value.agent.id },
    query: { kbId: props.knowledgeBaseId },
  })
}

function handleClose() {
  visible.value = false
  if (step.value === 'preview') emit('done')
}

watch(visible, (v) => {
  if (v) {
    step.value = 'idle'
    job.value = null
  } else {
    stopPoll()
  }
})

onUnmounted(stopPoll)
</script>

<template>
  <a-modal
    v-model:visible="visible"
    title="一键生成专家助手"
    :width="560"
    :footer="false"
    unmount-on-close
    @cancel="handleClose"
  >
    <div v-if="step === 'idle'" class="wizard">
      <p class="wizard__hint">
        系统将采样知识库内容，自动生成专家人设、欢迎语与示例问题。生成结果为草稿，可编辑后发布。
      </p>
      <a-button type="primary" long @click="startGenerate">开始生成</a-button>
    </div>

    <div v-else-if="step === 'running'" class="wizard">
      <a-spin :loading="true" tip="生成中…" />
      <p class="wizard__stage">{{ stageLabel }}</p>
      <a-progress
        :percent="job?.status === 'running' ? 60 : 30"
        :show-text="false"
        animation
        style="margin-top: 16px"
      />
    </div>

    <div v-else-if="step === 'preview' && job?.agent" class="wizard">
      <div class="wizard__preview-head">
        <span class="wizard__emoji">{{ job.agent.avatar_value }}</span>
        <div>
          <h4>{{ job.agent.name }}</h4>
          <p>{{ job.agent.description }}</p>
        </div>
      </div>
      <a-typography-paragraph :ellipsis="{ rows: 3 }">
        {{ job.agent.persona }}
      </a-typography-paragraph>
      <div class="wizard__questions">
        <a-tag v-for="q in job.agent.suggested_questions" :key="q" color="arcoblue">{{ q }}</a-tag>
      </div>
      <a-space style="margin-top: 20px">
        <a-button type="primary" @click="goEdit">编辑并发布</a-button>
        <a-button @click="handleClose">稍后处理</a-button>
      </a-space>
    </div>

    <div v-else class="wizard">
      <a-result status="error" :title="job?.error_message || '生成失败'" />
      <a-button type="primary" @click="startGenerate">重试</a-button>
    </div>
  </a-modal>
</template>

<style scoped>
.wizard {
  padding: 8px 0 4px;
}

.wizard__hint {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--color-text-3);
  line-height: 1.6;
}

.wizard__stage {
  margin-top: 12px;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-3);
}

.wizard__preview-head {
  display: flex;
  gap: 14px;
  margin-bottom: 12px;
}

.wizard__emoji {
  font-size: 36px;
  line-height: 1;
}

.wizard__preview-head h4 {
  margin: 0 0 4px;
  font-size: 16px;
}

.wizard__preview-head p {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-3);
}

.wizard__questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
</style>
