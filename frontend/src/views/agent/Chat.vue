<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconLeft } from '@arco-design/web-vue/es/icon'
import ChatMessageItem from '@/components/chat/ChatMessageItem.vue'
import ChatEmptyState from '@/components/chat/ChatEmptyState.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import ChatScrollFab from '@/components/chat/ChatScrollFab.vue'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import { fetchAgent } from '@/api/agent'
import { useChatStream } from '@/composables/useChatStream'
import { useChatScroll } from '@/composables/useChatScroll'
import { useChatSessionStore } from '@/stores/chat-session'
import type { ExpertAgent } from '@/types/agent'
import { ROUTE_NAMES } from '@/utils/constants'

const route = useRoute()
const router = useRouter()
const input = ref('')
const scrollRef = ref<HTMLElement | null>(null)
const agent = ref<ExpertAgent | null>(null)
const agentLoading = ref(false)

const agentId = computed(() => route.params.agentId as string)
const knowledgeBaseId = computed(() => Number(route.query.kbId))

const sessionStore = useChatSessionStore()
const { streaming, send, cancel } = useChatStream()
const { pinned, onScroll, scrollToBottom } = useChatScroll(scrollRef)

const messages = computed({
  get: () => sessionStore.messages,
  set: (val) => {
    sessionStore.messages = val
  },
})

const showScrollFab = computed(() => !pinned.value && messages.value.length > 0)
const canSend = computed(
  () =>
    !!knowledgeBaseId.value && !!agent.value && input.value.trim().length > 0 && !streaming.value,
)

function syncRouteConversation(id: string | null) {
  const query = { ...route.query }
  if (id) query.conversationId = id
  else delete query.conversationId
  router.replace({ query })
}

async function loadAgent() {
  if (!knowledgeBaseId.value) return
  agentLoading.value = true
  try {
    const { data } = await fetchAgent(knowledgeBaseId.value, agentId.value)
    if (data.status !== 'published') {
      Message.warning('该助手尚未发布')
      router.replace({
        name: ROUTE_NAMES.AGENT_DETAIL,
        params: { agentId: agentId.value },
        query: { kbId: knowledgeBaseId.value },
      })
      return
    }
    agent.value = data
    sessionStore.setAgentId(data.id)
  } catch {
    Message.error('加载专家助手失败')
  } finally {
    agentLoading.value = false
  }
}

async function bootstrap() {
  await loadAgent()
  if (!knowledgeBaseId.value || !agent.value) return
  await sessionStore.loadConversationList(knowledgeBaseId.value, agentId.value)
  const convId = route.query.conversationId as string | undefined
  if (convId) {
    await sessionStore.loadConversation(knowledgeBaseId.value, convId)
  }
}

onMounted(bootstrap)

async function openConversation(id: string) {
  if (!knowledgeBaseId.value || streaming.value) return
  await sessionStore.loadConversation(knowledgeBaseId.value, id)
  syncRouteConversation(id)
  await nextTick()
  scrollToBottom('auto')
}

function handleNewChat() {
  if (streaming.value) return
  sessionStore.startNewConversation()
  syncRouteConversation(null)
}

async function handleDeleteConversation(id: string) {
  if (!knowledgeBaseId.value) return
  try {
    await sessionStore.removeConversation(knowledgeBaseId.value, id)
    Message.success('已删除对话')
    if (!sessionStore.conversationId) syncRouteConversation(null)
  } catch {
    Message.error('删除失败')
  }
}

watch(
  messages,
  async () => {
    await nextTick()
    scrollToBottom(streaming.value ? 'auto' : 'smooth')
  },
  { deep: true },
)

async function handleSend() {
  if (!canSend.value || !knowledgeBaseId.value || !agent.value) return
  const query = input.value
  input.value = ''
  const kbId = knowledgeBaseId.value
  const convId = await sessionStore.ensureConversation(kbId)
  syncRouteConversation(convId)

  await send({
    knowledgeBaseId: kbId,
    query,
    messages: messages.value,
    conversationId: convId,
    agentId: agent.value.id,
    onUpdate: (next) => {
      messages.value = next
    },
    onDone: async () => {
      await sessionStore.reloadMessages(kbId)
      await sessionStore.loadConversationList(kbId, agent.value!.id)
    },
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

function goBack() {
  router.push({
    name: ROUTE_NAMES.AGENT_DETAIL,
    params: { agentId: agentId.value },
    query: { kbId: knowledgeBaseId.value },
  })
}
</script>

<template>
  <div class="chat-layout">
    <ChatSidebar
      :conversations="sessionStore.conversations"
      :active-id="sessionStore.conversationId"
      :loading="sessionStore.listLoading"
      @new-chat="handleNewChat"
      @select="openConversation"
      @delete="handleDeleteConversation"
    />

    <div class="chat-page">
      <header class="chat-page__header">
        <div class="chat-page__header-inner">
          <a-button type="text" size="small" @click="goBack">
            <template #icon><icon-left /></template>
          </a-button>
          <div v-if="agent" class="chat-page__agent">
            <span class="chat-page__agent-emoji">{{ agent.avatar_value }}</span>
            <div>
              <div class="chat-page__agent-name">{{ agent.name }}</div>
              <div class="chat-page__agent-desc">{{ agent.description }}</div>
            </div>
          </div>
          <a-tag v-if="streaming" color="arcoblue" size="small">生成中</a-tag>
        </div>
      </header>

      <main ref="scrollRef" class="chat-page__main" @scroll="onScroll">
        <a-spin :loading="sessionStore.messagesLoading || agentLoading" class="chat-page__spin">
          <div class="chat-page__thread">
            <Transition name="ui-fade" mode="out-in">
              <ChatEmptyState
                v-if="!messages.length && agent"
                key="empty"
                :title="agent.name"
                :description="agent.welcome_message"
                :suggestions="agent.suggested_questions"
                @pick="onPickSuggestion"
              />
              <TransitionGroup
                v-else-if="messages.length"
                key="list"
                name="chat-msg"
                tag="div"
                class="chat-page__list"
              >
                <ChatMessageItem
                  v-for="msg in messages"
                  :key="msg.id"
                  :message="msg"
                  :knowledge-base-id="knowledgeBaseId"
                />
              </TransitionGroup>
            </Transition>
          </div>
        </a-spin>
        <ChatScrollFab :visible="showScrollFab" @click="scrollToBottom('smooth')" />
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
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.chat-page {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
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
}

.chat-page__header-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 768px;
  margin: 0 auto;
  padding: 12px 20px;
}

.chat-page__agent {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.chat-page__agent-emoji {
  font-size: 28px;
  line-height: 1;
}

.chat-page__agent-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-1);
}

.chat-page__agent-desc {
  font-size: 12px;
  color: var(--color-text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 360px;
}

.chat-page__main {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 28px 20px 40px;
}

.chat-page__spin {
  display: block;
  max-width: 768px;
  margin: 0 auto;
}

.chat-page__thread {
  max-width: 768px;
  margin: 0 auto;
}

.chat-page__footer {
  flex-shrink: 0;
  padding: 14px 20px 18px;
  border-top: 1px solid var(--color-border-1);
  background: color-mix(in srgb, var(--color-bg-2) 92%, transparent);
}
</style>
