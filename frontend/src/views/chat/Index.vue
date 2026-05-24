<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import ChatMessageItem from '@/components/chat/ChatMessageItem.vue'
import PageContainer from '@/components/common/PageContainer.vue'
import { useChatStream } from '@/composables/useChatStream'
import { useKnowledgeBaseStore } from '@/stores/knowledge-base'
import type { ChatMessage } from '@/types/chat'

const input = ref('')
const messages = ref<ChatMessage[]>([])
const knowledgeBaseId = ref<number | undefined>(undefined)

const kbStore = useKnowledgeBaseStore()
const { streaming, send, cancel } = useChatStream()

const canSend = computed(
  () => !!knowledgeBaseId.value && input.value.trim().length > 0 && !streaming.value,
)

onMounted(async () => {
  await kbStore.loadList()
  if (kbStore.list.length > 0) {
    knowledgeBaseId.value = kbStore.list[0].id
  }
})

function handleSend() {
  if (!canSend.value || !knowledgeBaseId.value) return
  const query = input.value
  input.value = ''
  send(knowledgeBaseId.value, query, messages.value, (next) => {
    messages.value = next
  })
}

function handleStop() {
  cancel()
  const last = messages.value[messages.value.length - 1]
  if (last?.role === 'assistant' && last.status === 'streaming') {
    messages.value = [
      ...messages.value.slice(0, -1),
      { ...last, status: 'cancelled', errorMessage: '已停止生成' },
    ]
  }
}
</script>

<template>
  <PageContainer title="智能问答">
    <div class="chat-panel">
      <div class="chat-panel__toolbar">
        <span class="chat-panel__label">知识库</span>
        <a-select
          v-model="knowledgeBaseId"
          placeholder="请选择知识库"
          allow-search
          style="width: 280px"
          :loading="kbStore.listLoading"
        >
          <a-option v-for="kb in kbStore.list" :key="kb.id" :value="kb.id" :label="kb.name" />
        </a-select>
        <a-tag v-if="streaming" color="arcoblue">生成中…</a-tag>
      </div>

      <div ref="scrollRef" class="chat-panel__messages">
        <a-empty
          v-if="!messages.length"
          description="选择知识库后提问，支持 SSE 流式输出与引用来源展示"
        />
        <ChatMessageItem v-for="msg in messages" :key="msg.id" :message="msg" />
      </div>

      <div class="chat-panel__input">
        <a-textarea
          v-model="input"
          placeholder="输入问题，基于知识库检索并流式回答"
          :auto-size="{ minRows: 2, maxRows: 4 }"
          :disabled="streaming"
          @keydown.enter.exact.prevent="handleSend"
        />
        <a-space style="margin-top: 8px">
          <a-button type="primary" :disabled="!canSend" @click="handleSend">发送</a-button>
          <a-button v-if="streaming" @click="handleStop">停止</a-button>
        </a-space>
      </div>
    </div>
  </PageContainer>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  min-height: 520px;
}

.chat-panel__toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.chat-panel__label {
  font-size: 14px;
  color: var(--color-text-2);
}

.chat-panel__messages {
  flex: 1;
  min-height: 360px;
  max-height: 56vh;
  overflow-y: auto;
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 6px;
  background: var(--color-fill-1);
}
</style>
