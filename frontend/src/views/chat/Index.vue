<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import ChatMessageItem from '@/components/chat/ChatMessageItem.vue'
import ChatEmptyState from '@/components/chat/ChatEmptyState.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import ChatScrollFab from '@/components/chat/ChatScrollFab.vue'
import { useChatStream } from '@/composables/useChatStream'
import { useChatScroll } from '@/composables/useChatScroll'
import { useKnowledgeBaseStore } from '@/stores/knowledge-base'
import type { ChatMessage } from '@/types/chat'

const input = ref('')
const messages = ref<ChatMessage[]>([])
const knowledgeBaseId = ref<number | undefined>(undefined)
const scrollRef = ref<HTMLElement | null>(null)

const kbStore = useKnowledgeBaseStore()
const { streaming, send, cancel } = useChatStream()
const { pinned, onScroll, scrollToBottom } = useChatScroll(scrollRef)

const showScrollFab = computed(() => !pinned.value && messages.value.length > 0)

const canSend = computed(
  () => !!knowledgeBaseId.value && input.value.trim().length > 0 && !streaming.value,
)

const selectedKbName = computed(
  () => kbStore.list.find((kb) => kb.id === knowledgeBaseId.value)?.name,
)

onMounted(async () => {
  await kbStore.loadList()
  if (kbStore.list.length > 0) {
    knowledgeBaseId.value = kbStore.list[0].id
  }
})

watch(
  messages,
  async () => {
    await nextTick()
    scrollToBottom(streaming.value ? 'auto' : 'smooth')
  },
  { deep: true },
)

watch(streaming, async (now, prev) => {
  if (prev && !now) {
    await nextTick()
    scrollToBottom('smooth')
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

function onPickSuggestion(text: string) {
  input.value = text
}

function handleScrollFab() {
  scrollToBottom('smooth')
}
</script>

<template>
  <div class="chat-page">
    <header class="chat-page__header">
      <div class="chat-page__header-inner">
        <div class="chat-page__kb">
          <span class="chat-page__kb-label">知识库</span>
          <a-select
            v-model="knowledgeBaseId"
            placeholder="请选择知识库"
            allow-search
            :bordered="false"
            class="chat-page__kb-select"
            :loading="kbStore.listLoading"
          >
            <a-option v-for="kb in kbStore.list" :key="kb.id" :value="kb.id" :label="kb.name" />
          </a-select>
        </div>
        <Transition name="ui-fade" mode="out-in">
          <a-tag
            v-if="streaming"
            key="streaming"
            color="arcoblue"
            size="small"
            class="chat-page__tag"
          >
            <span class="chat-page__pulse" />生成中
          </a-tag>
          <span v-else-if="selectedKbName" key="hint" class="chat-page__kb-hint">{{
            selectedKbName
          }}</span>
        </Transition>
      </div>
    </header>

    <main ref="scrollRef" class="chat-page__main" @scroll="onScroll">
      <div class="chat-page__thread">
        <Transition name="ui-fade" mode="out-in">
          <ChatEmptyState v-if="!messages.length" key="empty" @pick="onPickSuggestion" />
          <TransitionGroup v-else key="list" name="chat-msg" tag="div" class="chat-page__list">
            <ChatMessageItem
              v-for="msg in messages"
              :key="msg.id"
              :message="msg"
              :knowledge-base-id="knowledgeBaseId"
            />
          </TransitionGroup>
        </Transition>
      </div>
      <ChatScrollFab :visible="showScrollFab" @click="handleScrollFab" />
    </main>

    <footer class="chat-page__footer">
      <ChatInput
        v-model="input"
        :disabled="streaming"
        :streaming="streaming"
        :can-send="canSend"
        @send="handleSend"
        @stop="handleStop"
      />
    </footer>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: linear-gradient(
    175deg,
    var(--color-bg-1) 0%,
    color-mix(in srgb, var(--color-fill-1) 70%, var(--color-bg-1)) 45%,
    var(--color-bg-1) 100%
  );
}

.chat-page__header {
  flex-shrink: 0;
  border-bottom: 1px solid var(--color-border-1);
  background: color-mix(in srgb, var(--color-bg-2) 90%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.chat-page__header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 768px;
  margin: 0 auto;
  padding: 12px 20px;
  gap: 12px;
}

.chat-page__kb {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.chat-page__kb-label {
  flex-shrink: 0;
  font-size: 13px;
  color: var(--color-text-3);
}

.chat-page__kb-select {
  min-width: 160px;
  max-width: 280px;
}

.chat-page__kb-hint {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--color-text-4);
}

.chat-page__tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.chat-page__pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgb(var(--primary-6));
  animation: pulse 1.4s var(--chat-ease) infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.35;
    transform: scale(0.85);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}

.chat-page__main {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 28px 20px 40px;
  scroll-behavior: smooth;
  overscroll-behavior: contain;
}

.chat-page__thread {
  max-width: 768px;
  margin: 0 auto;
}

.chat-page__list {
  display: block;
}

.chat-page__footer {
  flex-shrink: 0;
  padding: 14px 20px 18px;
  border-top: 1px solid var(--color-border-1);
  background: color-mix(in srgb, var(--color-bg-2) 92%, transparent);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}
</style>
